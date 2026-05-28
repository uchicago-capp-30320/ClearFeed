import os
from collections import Counter
import re

from django.core.cache import cache
from django.db.models import Count, Min

from api.models import SentimentResult, TopicResult, Tweet, ViewedTweet
from api.services.wordcloud import WORDCLOUD_LIMIT, tokenize_words


TOPIC_SERIES_NAME = "Topic as a Percent of Tweets"
WORD_FREQUENCY_SERIES_NAME = "Frequency"
SENTIMENT_SERIES_NAME = "Percentage of Tweets"
SENTIMENT_LABELS = ["Negative", "Neutral", "Positive"]
FEED_SUMMARY_CACHE_TTL = int(os.getenv("FEED_SUMMARY_CACHE_TTL", "300"))


def build_feed_summary(user):
    cache_key = _cache_key(user)
    cached_summary = cache.get(cache_key)
    if cached_summary is not None:
        return cached_summary

    summary = _build_feed_summary_uncached(user)
    cache.set(cache_key, summary, FEED_SUMMARY_CACHE_TTL)
    return summary


def invalidate_feed_summary_cache(user):
    cache.delete(_cache_key(user))


def _build_feed_summary_uncached(user):
    return {
        "overview": _get_overview_summary(user),
        "categories": _get_topic_summary(user),
        "word_frequency": _get_word_frequency_summary(user),
        "sentiment": _get_sentiment_summary(user),
    }


def _cache_key(user):
    return f"feed-summary:{user.pk}"


def _get_viewed_tweet_ids(user):
    return (
        ViewedTweet.objects.filter(user=user)
        .values_list("tweet_id", flat=True)
        .distinct()
    )


def _format_topic_label(topic):
    if not topic:
        return ""

    cleaned = re.sub(r"[_-]+", " ", topic).strip()
    small_words = {"and", "or", "of", "the", "a", "an", "to", "in", "for", "on", "with"}
    words = cleaned.split()
    formatted = []
    for index, word in enumerate(words):
        lower = word.lower()
        if index != 0 and lower in small_words:
            formatted.append(lower)
        else:
            formatted.append(lower[:1].upper() + lower[1:])
    return " ".join(formatted)


def _get_topic_summary(user):
    tweet_ids = _get_viewed_tweet_ids(user)

    topic_counts = (
        TopicResult.objects.filter(tweet_id__in=tweet_ids)
        .values("topic")
        .annotate(count=Count("topic"))
        .order_by("-count", "topic")[:5]
    )
    total = TopicResult.objects.filter(tweet_id__in=tweet_ids).count()

    labels = [_format_topic_label(item["topic"]) for item in topic_counts]
    data = (
        [round((item["count"] / total) * 100) for item in topic_counts] if total else []
    )

    return {
        "labels": labels,
        "series": [
            {
                "name": TOPIC_SERIES_NAME,
                "data": data,
            }
        ],
    }


def _get_overview_summary(user):
    tweet_ids = _get_viewed_tweet_ids(user)
    viewed_tweets = Tweet.objects.filter(tweet_id__in=tweet_ids)
    total_tweets = viewed_tweets.count()
    promoted_count = viewed_tweets.filter(promoted=True).count()
    promoted_percentage = (
        round((promoted_count / total_tweets) * 100) if total_tweets else 0
    )

    since_date = (
        ViewedTweet.objects.filter(user=user)
        .aggregate(first_viewed=Min("created_at"))
        .get("first_viewed")
    )

    top_users = [
        item["author__screen_name"] or item["author__display_name"] or "Unknown"
        for item in viewed_tweets.filter(promoted=True)
        .values("author__screen_name", "author__display_name")
        .annotate(count=Count("tweet_id"))
        .order_by("-count", "author__screen_name", "author__display_name")[:5]
    ]

    return {
        "top_users": top_users,
        "total_tweets": total_tweets,
        "since_date": since_date.date().isoformat() if since_date else "",
        "promoted_percentage": promoted_percentage,
    }


def _get_word_frequency_summary(user):
    texts = (
        Tweet.objects.filter(tweet_id__in=_get_viewed_tweet_ids(user))
        .exclude(full_text__isnull=True)
        .values_list("full_text", flat=True)
    )

    counts = Counter()
    for text in texts:
        counts.update(tokenize_words(text))

    common_words = counts.most_common(WORDCLOUD_LIMIT)

    return {
        "labels": [word for word, _count in common_words],
        "series": [
            {
                "name": WORD_FREQUENCY_SERIES_NAME,
                "data": [count for _word, count in common_words],
            }
        ],
    }


def _get_sentiment_summary(user):
    counts = {
        item["sentiment"].lower(): item["count"]
        for item in SentimentResult.objects.filter(
            tweet_id__in=_get_viewed_tweet_ids(user)
        )
        .values("sentiment")
        .annotate(count=Count("sentiment"))
    }
    negative_count = counts.get("negative", 0)
    neutral_count = counts.get("neutral", 0)
    positive_count = counts.get("positive", 0)
    total = negative_count + neutral_count + positive_count

    data = (
        [
            round((negative_count / total) * 100),
            round((neutral_count / total) * 100),
            round((positive_count / total) * 100),
        ]
        if total
        else [0, 0, 0]
    )
    sentiment_average = (
        round((positive_count - negative_count) / total, 2) if total else 0
    )

    return {
        "sentiment_average": sentiment_average,
        "labels": SENTIMENT_LABELS,
        "series": [
            {
                "name": SENTIMENT_SERIES_NAME,
                "data": data,
            }
        ],
    }
