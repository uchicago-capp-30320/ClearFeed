from django.core.management.base import BaseCommand
from api.models import Tweet, AnalysisStatus
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

        for i, tweet in enumerate(tweets, 1):
            self.stdout.write(f"[{i}/{total}] Analyzing tweet {tweet.tweet_id}...")
            analyze_tweet(tweet)
            status = Tweet.objects.get(tweet_id=tweet.tweet_id).analysis_status
            self.stdout.write(f"  → {status}")

        self.stdout.write(self.style.SUCCESS("Done"))
