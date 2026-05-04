import json
from datetime import datetime, timezone as dt_timezone
from api.models import (
    AppUser,
    BrowseSession,
    TwitterAuthor,
    Tweet,
    TweetMedia,
    ViewedTweet,
    SessionStatus,
    AnalysisStatus,
)

# temporary test users — replace with real auth token from request headers
# swap HARDCODED_USER_ID to test as different users
TEST_USERS = {
    "grace": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "teddy": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "yuri": "c3d4e5f6-a7b8-9012-cdef-123456789012",
}
HARDCODED_USER_ID = TEST_USERS["grace"]


def ingest_posts(body, platform, user_agent):
    """
    Main entry point for the ingestion pipeline.
    Parses NDJSON body
    Returns the completed session.
    Raises ValueError if no valid posts are found.
    Rolls back upload if failure mid-pipeline
    """
    posts = _parse_ndjson(body)
    if not posts:
        raise ValueError("no valid posts received")

    app_user = _upsert_app_user()
    session = _create_session(app_user, platform, user_agent)

    try:
        _upsert_authors(posts)
        _insert_tweets(posts, app_user, session)
        _complete_session(session)
    except Exception as e:
        # Something failed mid-pipeline; delete the session and partially inserted data
        ViewedTweet.objects.filter(session=session).delete()
        session.delete
        print(f"Ingestion failed for session {session.id}: {e}")
        raise

    return session, len(posts)


# ------------------------------------------------------------------------------


def _parse_ndjson(body):
    """
    Parse raw NDJSON string into a list of Python dicts.
    Skips malformed lines silently rather than crashing the whole request.
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


def _upsert_app_user():
    """
    Look up or create the app user.
    Currently uses a hardcoded UUID — will be replaced with real auth token.
    """
    app_user, _ = AppUser.objects.get_or_create(id=HARDCODED_USER_ID)
    return app_user


def _create_session(app_user, platform, user_agent):
    """
    Create a new browse session for this upload.
    Every upload = one session record.
    """
    return BrowseSession.objects.create(
        user=app_user,
        platform=platform,
        user_agent=user_agent,
        status=SessionStatus.QUEUED,
    )


# ------------------------------------------------------------------------------
# Step 3 — upsert twitter_authors


def _upsert_authors(posts):
    """
    For each post, upsert the tweet author into twitter_author.
    Authors must be created before tweets because tweets FK to twitter_author.
    Two cases:
      - existing author: update mutable fields only, never touch account_created_at
      - new author: create full record including account_created_at
    Null filtering ensures we never overwrite good data with nulls from
    incomplete Twitter API responses (e.g. thread view records).
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

        # parse account_created_at from Twitter's date format
        # Twitter format: "Fri Jul 22 16:50:20 +0000 2011"
        # immutable — only set on first insert, never updated
        account_created_at = None
        raw_account_created_at = user.get("core", {}).get("created_at")
        if raw_account_created_at:
            try:
                account_created_at = datetime.strptime(
                    raw_account_created_at, "%a %b %d %H:%M:%S +0000 %Y"
                ).replace(tzinfo=dt_timezone.utc)
            except ValueError:
                account_created_at = None

        # build mutable fields and filter out nulls
        # null filtering prevents overwriting previously good data
        # when Twitter returns incomplete user objects for some records
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


def _insert_tweets(posts, app_user, session):
    """
    For each post, insert the tweet if new, run analysis if needed,
    insert media, and always insert a viewed_tweet record.
    """
    for post in posts:
        legacy = post.get("data", {}).get("legacy", {})
        user = (
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
        author_twitter_id = user.get("rest_id")
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

        # Step 4 — insert tweet if new, skip if already exists
        # tweets are immutable — we never update existing tweet content
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

        # only run analysis if tweet is new or a previous attempt failed
        # skips tweets already marked complete — models never run twice
        # if tweet.full_text and tweet.analysis_status in [
        # AnalysisStatus.PENDING,
        # AnalysisStatus.FAILED,
        # ]:
        # analyze_tweet(tweet)

        # Step 5 — insert media
        _insert_media(post, tweet)

        # Step 6 — always insert viewed_tweet
        _insert_viewed_tweet(post, legacy, tweet, app_user, session)


def _insert_media(post, tweet):
    """
    Insert media items attached to this tweet.
    Uses extended_entities (not entities) for full video variant info.
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


def _insert_viewed_tweet(post, legacy, tweet, app_user, session):
    """
    Always insert a new viewed_tweet row regardless of whether the tweet
    is new or already existed. Records this user seeing this tweet in this
    session with engagement stats at the moment of viewing.
    The same tweet can have many viewed_tweet rows across users and sessions.
    Stores full raw_data as backup for re-parsing if fields are missed.
    """
    ViewedTweet.objects.create(
        user=app_user,
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
# Step 7 — mark session complete


def _complete_session(session):
    """
    Mark the session as complete.
    updated_at is set automatically by auto_now=True on the model.
    When Celery is added this becomes status='queued' and triggers
    analyze_session.delay(str(session.id)) instead.
    """
    session.status = SessionStatus.INGESTED
    session.save()
