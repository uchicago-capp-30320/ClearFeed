from django.db import transaction
from django_q.tasks import async_task

from api.models import AnalysisStatus, BrowseSession, SessionStatus, Tweet, ViewedTweet
from api.services.analysis import analyze_tweet


def analyze_session(session_id):
    """
    Run analysis for all tweets belonging to a browse session.

    This is the session-level worker entry point for Django Q. It keeps the
    ingestion request fast and lets the queue process HuggingFace inference in
    the background.
    """
    session = BrowseSession.objects.get(id=session_id)
    session.status = SessionStatus.ANALYZING
    session.save(update_fields=["status", "updated_at"])

    tweet_ids = list(
        ViewedTweet.objects.filter(session_id=session_id)
        .values_list("tweet_id", flat=True)
        .distinct()
    )
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
            task_failed = True
            tweet.analysis_status = AnalysisStatus.FAILED
            tweet.save(update_fields=["analysis_status", "updated_at"])
            print(f"Analysis crashed for tweet {tweet.tweet_id}: {exc}")

    any_failed = Tweet.objects.filter(
        tweet_id__in=tweet_ids,
        analysis_status=AnalysisStatus.FAILED,
    ).exists()

    session.status = (
        SessionStatus.FAILED if task_failed or any_failed else SessionStatus.COMPLETE
    )
    session.save(update_fields=["status", "updated_at"])


def enqueue_session_analysis(session_id):
    """
    Queue analysis for a session after the ingestion transaction commits.
    """

    def _enqueue():
        async_task("api.tasks.analyze_session", str(session_id))

    transaction.on_commit(
        _enqueue
    )  # ensures this runs only after the current DB transaction successfully commits
