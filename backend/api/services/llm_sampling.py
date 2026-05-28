import random

from api.models import Tweet

DEFAULT_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 100
MAX_TWEET_CHARS = 280


def sample_user_tweets(user, sample_size=DEFAULT_SAMPLE_SIZE, seed=None):
    """
    Return a random sample of the user's tweets as normalized dicts.

    The service is intentionally user-scoped. Session-scoped sampling can be
    added later without changing the output contract.
    """
    requested_size = _normalize_sample_size(sample_size)
    tweets = list(
        Tweet.objects.filter(
            viewedtweet__user=user,
            full_text__isnull=False,
        )
        .select_related("author")
        .distinct()
        .order_by("created_at", "tweet_id")
    )

    if not tweets:
        return []

    rng = random.Random(seed)
    if requested_size >= len(tweets):
        selected = list(tweets)
        rng.shuffle(selected)
    else:
        selected = rng.sample(tweets, requested_size)

    return [_serialize_tweet(tweet) for tweet in selected]


def _normalize_sample_size(sample_size):
    try:
        sample_size = int(sample_size)
    except (TypeError, ValueError):
        sample_size = DEFAULT_SAMPLE_SIZE

    return max(1, min(sample_size, MAX_SAMPLE_SIZE))


def _serialize_tweet(tweet):
    author_name = "Unknown"
    screen_name = ""
    if tweet.author:
        if tweet.author.display_name:
            author_name = tweet.author.display_name
        elif tweet.author.screen_name:
            author_name = tweet.author.screen_name

        if tweet.author.screen_name:
            screen_name = tweet.author.screen_name

    return {
        "tweet_id": tweet.tweet_id,
        "author_name": author_name,
        "screen_name": screen_name,
        "text": (tweet.full_text or "")[:MAX_TWEET_CHARS],
        "promoted": tweet.promoted,
        "is_reply": tweet.is_reply,
    }
