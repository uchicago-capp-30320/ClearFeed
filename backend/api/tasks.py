from django.db import transaction
from django_q.tasks import async_task

from api.models import AnalysisStatus, BrowseSession, SessionStatus, Tweet, ViewedTweet
from api.services.analysis import analyze_tweet
from api.services.llm_analysis_runner import run_user_llm_analysis


def analyze_session(session_id):
    """
    Run analysis for all tweets belonging to a browse session.

    This is the session-level worker entry point for Django Q. It keeps the
    ingestion request fast and lets the queue process HuggingFace inference in
    the background.
    """
    session = BrowseSession.objects.get(id=session_id)
    # Mark the session as actively processing before any tweet work begins.
    session.status = SessionStatus.ANALYZING
    session.save(update_fields=["status", "updated_at"])

    # Only analyze tweets that were actually present in this session.
    tweet_ids = list(
        ViewedTweet.objects.filter(session_id=session_id)
        .values_list("tweet_id", flat=True)
        .distinct()
    )
    # Skip tweets without text and retry ones that previously failed.
    tweets = list(
        Tweet.objects.filter(
            tweet_id__in=tweet_ids,
            full_text__isnull=False,
            analysis_status__in=[
                AnalysisStatus.PENDING,
                AnalysisStatus.FAILED,
            ],
        ).order_by("created_at")
    )

    task_failed = False

    for tweet in tweets:
        try:
            analyze_tweet(tweet)
        except Exception as exc:
            # Keep the session moving even if a single tweet analysis crashes.
            task_failed = True
            tweet.analysis_status = AnalysisStatus.FAILED
            tweet.save(update_fields=["analysis_status", "updated_at"])
            print(f"Analysis crashed for tweet {tweet.tweet_id}: {exc}")

    # Re-check persisted tweet state in case some failures were recorded elsewhere.
    any_failed = Tweet.objects.filter(
        tweet_id__in=tweet_ids,
        analysis_status=AnalysisStatus.FAILED,
    ).exists()

    # Session status reflects the aggregate result of all tweet analyses.
    session.status = (
        SessionStatus.FAILED if task_failed or any_failed else SessionStatus.COMPLETE
    )
    session.save(update_fields=["status", "updated_at"])

    if session.status == SessionStatus.COMPLETE:
        try:
            # Only generate the user-level LLM summary after tweet analysis succeeds.
            run_user_llm_analysis(session.user, sample_size=10, seed=None)
        except Exception as exc:
            print(f"LLM analysis failed for session {session_id}: {exc}")


def enqueue_session_analysis(session_id):
    """
    Queue analysis for a session after the ingestion transaction commits.
    """

    def _enqueue():
        # Django-Q runs the analysis worker asynchronously after commit.
        async_task("api.tasks.analyze_session", str(session_id))

    # Delay queueing until the ingestion transaction is safely persisted.
    transaction.on_commit(_enqueue)
