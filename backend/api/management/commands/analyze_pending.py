from django.core.management.base import BaseCommand
from api.models import Tweet, BrowseSession, ViewedTweet, AnalysisStatus, SessionStatus
from api.services.analysis import analyze_tweet


class Command(BaseCommand):
    help = "Run analysis on all tweets with status pending or failed"

    def handle(self, *args, **options):
        tweets = Tweet.objects.filter(
            analysis_status__in=[
                AnalysisStatus.PENDING,
                AnalysisStatus.FAILED,
            ],
            full_text__isnull=False,
        )

        total = tweets.count()
        self.stdout.write(f"Found {total} tweets to analyze")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to do"))
            return

        # find all sessions that have pending tweets and mark them analyzing
        session_ids = (
            ViewedTweet.objects.filter(tweet__in=tweets)
            .values_list("session_id", flat=True)
            .distinct()
        )

        BrowseSession.objects.filter(id__in=session_ids).update(
            status=SessionStatus.ANALYZING
        )

        # analyze each tweet
        for i, tweet in enumerate(tweets, 1):
            self.stdout.write(f"[{i}/{total}] Analyzing tweet {tweet.tweet_id}...")
            analyze_tweet(tweet)
            status = Tweet.objects.get(tweet_id=tweet.tweet_id).analysis_status
            self.stdout.write(f"  → {status}")

        # after all tweet processed, check each session
        for session_id in session_ids:
            session = BrowseSession.objects.get(id=session_id)
            tweet_ids = (
                ViewedTweet.objects.filter(session=session)
                .values_list("tweet_id", flat=True)
                .distinct()
            )

            unfinished = Tweet.objects.filter(
                tweet_id__in=tweet_ids,
                analysis_status__in=[
                    AnalysisStatus.PENDING,
                    AnalysisStatus.PROCESSING,
                ],
            ).count()

            if unfinished == 0:
                session.status = SessionStatus.COMPLETE
                session.save()
                self.stdout.write(f"Session {session_id} → complete")
            else:
                self.stdout.write(
                    f"Session {session_id} → {unfinished} tweets still unfinished"
                )

        self.stdout.write(self.style.SUCCESS("Done"))
