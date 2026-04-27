from api.models import (
    SentimentResult,
    ToxicityResult,
    TopicResult,
    AnalysisStatus,
)
from api.services.sentiment import analyze_sentiment_text
from api.services.toxicity import analyze_toxicity_text
from api.services.topic import analyze_topic_text


def analyze_tweet(tweet):
    """
    Runs all three ML models on a tweet.
    Each model only runs if it doesn't already have a successful result row.
    Sets analysis_status to 'complete' if all succeed, 'failed' if any fail.
    Only call this if tweet.analysis_status is 'pending' or 'failed'.
    """
    tweet.analysis_status = AnalysisStatus.PROCESSING
    tweet.save(update_fields=["analysis_status"])

    all_succeeded = True

    if not SentimentResult.objects.filter(tweet=tweet).exists():
        try:
            _run_sentiment(tweet)
        except Exception as e:
            all_succeeded = False
            print(f"Sentiment failed for tweet {tweet.tweet_id}: {e}")

    if not ToxicityResult.objects.filter(tweet=tweet).exists():
        try:
            _run_toxicity(tweet)
        except Exception as e:
            all_succeeded = False
            print(f"Toxicity failed for tweet {tweet.tweet_id}: {e}")

    if not TopicResult.objects.filter(tweet=tweet).exists():
        try:
            _run_topic(tweet)
        except Exception as e:
            all_succeeded = False
            print(f"Topic failed for tweet {tweet.tweet_id}: {e}")

    tweet.analysis_status = (
        AnalysisStatus.COMPLETE if all_succeeded else AnalysisStatus.FAILED
    )
    tweet.save(update_fields=["analysis_status"])


def _run_sentiment(tweet):
    result = analyze_sentiment_text(tweet.full_text[:512])
    SentimentResult.objects.update_or_create(
        tweet=tweet,
        defaults={
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
        },
    )


def _run_toxicity(tweet):
    result = analyze_toxicity_text(tweet.full_text[:512])
    ToxicityResult.objects.update_or_create(
        tweet=tweet,
        defaults={
            "toxicity_label": result["toxicity_label"],
            "confidence": result["confidence"],
        },
    )


def _run_topic(tweet):
    result = analyze_topic_text(tweet.full_text[:512])
    TopicResult.objects.update_or_create(
        tweet=tweet,
        defaults={
            "topic": result["topic"],
            "confidence": result["confidence"],
        },
    )
