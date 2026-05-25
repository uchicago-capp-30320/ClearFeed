import json
from datetime import datetime, timezone as dt_timezone

from django.db import transaction

from api.models import (
    BrowseSession,
    TwitterAuthor,
    Tweet,
    TweetMedia,
    ViewedTweet,
    SessionStatus,
    AnalysisStatus,
)
from api.tasks import enqueue_session_analysis


def ingest_posts(body, platform, user_agent, user):
    """
    Main entry point for the ingestion pipeline.

    Parses a raw NDJSON request body and writes all records to the database
    inside a single atomic transaction. If anything fails mid-pipeline, the
    entire transaction rolls back. No partial data is saved.

    After a successful commit, enqueues an async analysis task via Django-Q.

    Args:
        body:       Raw NDJSON string from the extension POST request
        platform:   Platform identifier (e.g. "X/Twitter")
        user_agent: Browser user agent string
        user:       Authenticated AppUser making the request

    Returns:
        (session, post_count) tuple
    Raises:
        ValueError: if no valid posts are found in the body
    """
    posts = _parse_ndjson(body)
    if not posts:
        raise ValueError("no valid posts received")

    try:
        with transaction.atomic():
            session = _create_session(user, platform, user_agent)
            _upsert_authors(posts)
            _insert_tweets(posts, user, session)
            _queue_session(session)
    except Exception as e:
        print(f"Ingestion failed: {e}")
        raise

    return session, len(posts)


# ------------------------------------------------------------------------------
# Step 1 — parse NDJSON
# ------------------------------------------------------------------------------


def _parse_ndjson(body):
    """
    Parse a raw NDJSON string into a list of Python dicts.

    Processes line by line and skips malformed lines silently rather than
    crashing the entire request on a single bad record.
    """
    posts = []
    for line in body.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            posts.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return posts


# ------------------------------------------------------------------------------
# Step 2 — create browse session
# ------------------------------------------------------------------------------


def _create_session(user, platform, user_agent):
    """
    Create a new BrowseSession for this upload.

    Every upload creates exactly one session record, regardless of how many
    tweets are in it. Status starts as QUEUED and is updated by the analysis
    worker once processing begins.
    """
    return BrowseSession.objects.create(
        user=user,
        platform=platform,
        user_agent=user_agent,
        status=SessionStatus.QUEUED,
    )


# ------------------------------------------------------------------------------
# Step 3 — upsert Twitter authors
# ------------------------------------------------------------------------------


def _upsert_authors(posts):
    """
    Upsert TwitterAuthor records for every post in the batch.

    Authors must be created before tweets because tweets FK to twitter_author.
    Handles two cases:
      - Existing author: update mutable fields only, never touch account_created_at
        (that field is immutable — set once on first insert and never changed)
      - New author: create full record including account_created_at

    Null filtering on mutable fields ensures we never overwrite previously good
    data with nulls from incomplete API responses (e.g. thread view records
    where Twitter returns a minimal user object).
    """
    for post in posts:
        user = (
            post.get("data", {})
            .get("core", {})
            .get("user_results", {})
            .get("result", {})
        )
        if not user:
            continue

        author_twitter_id = user.get("rest_id")
        if not author_twitter_id:
            continue

        # account_created_at is immutable — only set on first insert
        account_created_at = None
        raw_account_created_at = user.get("core", {}).get("created_at")
        if raw_account_created_at:
            try:
                account_created_at = datetime.strptime(
                    raw_account_created_at, "%a %b %d %H:%M:%S +0000 %Y"
                ).replace(tzinfo=dt_timezone.utc)
            except ValueError:
                account_created_at = None

        # filter out nulls before updating — never overwrite good data
        mutable_fields = {
            "screen_name": user.get("core", {}).get("screen_name"),
            "display_name": user.get("core", {}).get("name"),
            "bio": user.get("legacy", {}).get("description"),
            "location": user.get("location", {}).get("location"),
            "is_blue_verified": user.get("is_blue_verified", False),
            "followers_count": user.get("legacy", {}).get("followers_count"),
            "following_count": user.get("legacy", {}).get("friends_count"),
            "statuses_count": user.get("legacy", {}).get("statuses_count"),
        }
        mutable_fields = {k: v for k, v in mutable_fields.items() if v is not None}

        try:
            # existing author — update mutable fields only
            author = TwitterAuthor.objects.get(author_twitter_id=author_twitter_id)
            for field, value in mutable_fields.items():
                setattr(author, field, value)
            author.save()
        except TwitterAuthor.DoesNotExist:
            # new author — create with all fields including account_created_at
            TwitterAuthor.objects.create(
                author_twitter_id=author_twitter_id,
                account_created_at=account_created_at,
                **mutable_fields,
            )


# ------------------------------------------------------------------------------
# Steps 4, 5, 6 — tweets, media, viewed_tweets
# ------------------------------------------------------------------------------


def _insert_tweets(posts, user, session):
    """
    Insert tweet records, media, and viewed_tweet records for each post.

    Tweets are immutable after first insert — get_or_create skips existing
    tweets without modifying them. This means a tweet seen by multiple users
    is only stored once in the tweet table, but each user gets their own
    viewed_tweet row recording their engagement stats at the moment of viewing.

    Note: `user` is the logged-in AppUser. `twitter_user` is the tweet author
    from the API response.
    """
    for post in posts:
        legacy = post.get("data", {}).get("legacy", {})
        twitter_user = (
            post.get("data", {})
            .get("core", {})
            .get("user_results", {})
            .get("result", {})
        )

        tweet_id = legacy.get("id_str")
        if not tweet_id:
            continue

        entities = legacy.get("entities", {})
        hashtags = [h.get("text") for h in entities.get("hashtags", [])]

        # look up author we just upserted in Step 3
        author = None
        author_twitter_id = twitter_user.get("rest_id")
        if author_twitter_id:
            try:
                author = TwitterAuthor.objects.get(author_twitter_id=author_twitter_id)
            except TwitterAuthor.DoesNotExist:
                pass

        # parse tweet_created_at from Twitter's date format
        tweet_created_at = None
        raw_created_at = legacy.get("created_at")
        if raw_created_at:
            try:
                tweet_created_at = datetime.strptime(
                    raw_created_at, "%a %b %d %H:%M:%S +0000 %Y"
                ).replace(tzinfo=dt_timezone.utc)
            except ValueError:
                tweet_created_at = None

        # Step 4 — insert tweet if new, skip if already exists (immutable)
        tweet, created = Tweet.objects.get_or_create(
            tweet_id=tweet_id,
            defaults={
                "author": author,
                "conversation_id": legacy.get("conversation_id_str"),
                "is_reply": bool(legacy.get("in_reply_to_status_id_str")),
                "in_reply_to_tweet_id": legacy.get("in_reply_to_status_id_str"),
                "in_reply_to_screen_name": legacy.get("in_reply_to_screen_name"),
                "timestamp_collected": post.get("timestamp_collected"),
                "full_text": legacy.get("full_text"),
                "hashtags": hashtags,
                "lang": legacy.get("lang"),
                "source_app": legacy.get("source"),
                "source_platform_url": post.get("source_platform_url"),
                "is_quote_status": legacy.get("is_quote_status", False),
                "is_retweet": bool(legacy.get("retweeted_status_result")),
                "possibly_sensitive": legacy.get("possibly_sensitive", False),
                "promoted": post.get("data", {}).get("promoted", False),
                "tweet_created_at": tweet_created_at,
                "analysis_status": AnalysisStatus.PENDING,
            },
        )

        # Step 5 — insert media attachments
        _insert_media(post, tweet)

        # Step 6 — always insert a viewed_tweet row for this user + session
        _insert_viewed_tweet(post, legacy, tweet, user, session)


def _insert_media(post, tweet):
    """
    Insert media items attached to this tweet.

    Keyed by media_key — same media shared across tweets is only stored once.
    """
    media_items = (
        post.get("data", {})
        .get("legacy", {})
        .get("extended_entities", {})
        .get("media", [])
    )
    for media in media_items:
        media_key = media.get("media_key")
        if not media_key:
            continue
        TweetMedia.objects.get_or_create(
            media_key=media_key,
            defaults={
                "tweet": tweet,
                "type": media.get("type"),
                "media_url": media.get("media_url_https"),
                "width": media.get("original_info", {}).get("width"),
                "height": media.get("original_info", {}).get("height"),
                "duration_ms": media.get("video_info", {}).get("duration_millis"),
                "video_variants": media.get("video_info", {}).get("variants"),
            },
        )


def _insert_viewed_tweet(post, legacy, tweet, user, session):
    """
    Inserts a new viewed_tweet row for this user + session.

    Records the user seeing this tweet in this session, along with engagement
    stats at the exact moment of viewing. The same tweet can have many
    viewed_tweet rows across different users and sessions.

    Stores raw_data as a backup for re-parsing if fields are missed or
    the data model changes later.
    """
    ViewedTweet.objects.create(
        user=user,
        session=session,
        tweet=tweet,
        timestamp_collected=post.get("timestamp_collected"),
        favorite_count=legacy.get("favorite_count"),
        retweet_count=legacy.get("retweet_count"),
        reply_count=legacy.get("reply_count"),
        quote_count=legacy.get("quote_count"),
        bookmark_count=legacy.get("bookmark_count"),
        view_count=int(post.get("data", {}).get("views", {}).get("count", 0) or 0),
        raw_data=post,
    )


# ------------------------------------------------------------------------------
# Step 7 — queue session for analysis
# ------------------------------------------------------------------------------


def _queue_session(session):
    """
    Mark the session as queued and enqueue an async analysis task.

    enqueue_session_analysis() uses transaction.on_commit() internally, which
    ensures the Django-Q task is only queued after the database transaction
    successfully commits. This prevents the worker from picking up a task
    before the tweets are actually written to the database.
    """
    session.status = SessionStatus.QUEUED
    session.save()
    enqueue_session_analysis(session.id)
