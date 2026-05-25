# Model/Resource Documentation

This document describes the main data entities and API resources used by ClearFeed's backend.
The system ingests tweet data exported by the ClearFeed Capture browser extension, stores normalized tweet metadata, and runs NLP analysis models asynchronously after each upload.

## Key Concepts

**Canonical tweet vs. viewed tweet**

The system separates a tweet's core content from the event of a user seeing that tweet.

- `Tweet` stores the canonical tweet record once, globally deduplicated across all users.
- `ViewedTweet` stores that a specific user saw that tweet in a specific browsing session.

This is important because the same tweet may appear:

- in multiple user sessions
- multiple times for the same user
- with different engagement counts over time

**Session-oriented ingestion**

Every upload from the extension creates a new BrowseSession. That session groups one batch of collected tweets and links them back to the user who uploaded them. Sessions track the full lifecycle from ingestion through NLP analysis.

**Analysis results are stored separately**

Model outputs are not stored directly on Tweet. Instead, each analysis type has its own result table (SentimentResult, TopicResult). This keeps the tweet record focused on source data while result tables store derived data. The LLM feed blurb is stored in LLMAnalysisRun, separate from per-tweet results.

**Raw source data is partially preserved**

ViewedTweet.raw_data stores the original JSON record from the extension. This is useful if the team later realizes a field was missed during parsing and needs to reprocess old uploads without requiring the user to re-upload.

**Analysis runs asynchronously**
NLP analysis does not run during the upload request. After ingestion completes, a Django-Q task is queued via transaction.on_commit() and picked up by the qcluster worker. The extension gets an immediate response; analysis happens in the background.


## Entities

### `AppUser`

Represents one ClearFeed application user. Extends Django's `AbstractBaseUser` — authentication is via email and password, sessions managed by Django's built-in session framework.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. |
| `email` | `EmailField, unique, nullable` | User's email address, used as the login identifier. |
| `is_staff` | `Boolean` | Whether the user has Django admin access. |
| `is_active` | `Boolean` | Whether the account is active. |
| `created_at` | `DateTime` | Time the user record was created. |

Relationships and constraints:
- primary key is a UUID
- `email` is unique
- one `AppUser` can have many `BrowseSession`
- one `AppUser` can have many `ViewedTweet`
- one `AppUser` can have many `LLMAnalysisRun`

---

### `BrowseSession`

Represents one upload from the browser extension. Groups a batch of tweets collected during one user activity period and tracks the full ingestion and analysis lifecycle.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. |
| `user` | `ForeignKey(AppUser)` | The user who owns this session. |
| `platform` | `Text` | Source platform identifier from the `X-Zeeschuimer-Platform` header. |
| `user_agent` | `Text, nullable` | Browser user agent string from the upload request. |
| `status` | `Text` | Session lifecycle status: `queued`, `analyzing`, `complete`, `failed`. |
| `created_at` | `DateTime` | Time the session was created. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Relationships and constraints:
- belongs to exactly one `AppUser`
- one `BrowseSession` can have many `ViewedTweet`
- indexed by `user`

Important note: The system is session-based, not only user-based. One user may upload many times over time, and each upload remains a separate session.

---

### `TwitterAuthor`

Stores normalized metadata about the author of a tweet. The same author may be referenced by many tweets across many sessions and users. Authors are upserted on every upload — mutable fields are updated, immutable fields are never overwritten.

| Name | Type | Description |
| --- | --- | --- |
| `author_twitter_id` | `Text` | Primary key. Twitter's internal author ID. |
| `screen_name` | `Char(50), nullable` | Author handle without the `@`. Mutable. |
| `display_name` | `Char(100), nullable` | Public profile display name. Mutable. |
| `bio` | `Text, nullable` | Author biography text. Mutable. |
| `location` | `Text, nullable` | Profile location text. Mutable. |
| `followers_count` | `Integer, nullable` | Follower count at time of last upsert. Mutable. |
| `following_count` | `Integer, nullable` | Following count at time of last upsert. Mutable. |
| `statuses_count` | `Integer, nullable` | Total tweet count at time of last upsert. Mutable. |
| `is_blue_verified` | `Boolean, nullable` | Whether the account has blue verification. Mutable. |
| `account_created_at` | `DateTime, nullable` | When the Twitter account was created. **Immutable** — set on first insert only, never updated. |
| `created_at` | `DateTime` | When this row was first inserted. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Relationships and constraints:
- primary key is Twitter's author ID string
- one `TwitterAuthor` can have many `Tweet`
- `screen_name` is indexed

Important note: `account_created_at` is the only truly immutable field — it represents when the Twitter account was created, which never changes. All other fields are updated on each upsert to reflect the latest profile state. Null filtering prevents overwriting good data with incomplete API responses.

---

### `Tweet`

Stores the canonical metadata and text for one tweet. A tweet is stored once globally — if the same tweet is seen by multiple users or in multiple sessions, it is only inserted once. Tweets are immutable after first insert.

| Name | Type | Description |
| --- | --- | --- |
| `tweet_id` | `Text` | Primary key. Twitter's tweet ID string. |
| `author` | `ForeignKey(TwitterAuthor), nullable` | The tweet's author. |
| `conversation_id` | `Text, nullable` | Thread identifier. |
| `is_reply` | `Boolean` | Whether the tweet is a reply. |
| `in_reply_to_tweet_id` | `Text, nullable` | ID of the tweet being replied to. |
| `in_reply_to_screen_name` | `Text, nullable` | Screen name of the account being replied to. |
| `timestamp_collected` | `BigInteger, nullable` | Collection timestamp from the extension payload. |
| `full_text` | `Text, nullable` | Tweet text, used for NLP analysis. |
| `hashtags` | `JSON, nullable` | List of hashtag strings extracted from the tweet. |
| `lang` | `Char(10), nullable` | Language code. |
| `source_app` | `Text, nullable` | Client application used to post (e.g. "Twitter for iPhone"). |
| `source_platform_url` | `Text, nullable` | URL where the extension captured the tweet. |
| `is_quote_status` | `Boolean` | Whether the tweet quotes another tweet. |
| `is_retweet` | `Boolean` | Whether the tweet is a retweet. |
| `possibly_sensitive` | `Boolean` | Whether Twitter flagged the content as sensitive. |
| `promoted` | `Boolean` | Whether the tweet was served as a paid ad. Detected from `promotedMetadata` in the Twitter API response. |
| `tweet_created_at` | `DateTime, nullable` | When the tweet was originally posted. |
| `analysis_status` | `Text` | NLP pipeline status: `pending`, `processing`, `complete`, `failed`. |
| `created_at` | `DateTime` | When this row was first inserted. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Relationships and constraints:
- primary key is Twitter's tweet ID string
- belongs to zero or one `TwitterAuthor`
- one `Tweet` can have many `TweetMedia`
- one `Tweet` can have many `ViewedTweet`
- has one `SentimentResult` and one `TopicResult`
- indexed by `author`, `conversation_id`, `tweet_created_at`, `analysis_status`

Important note: `promoted` is one of ClearFeed's most important fields — it identifies tweets served as paid ads, powering the promoted content analysis in the dashboard.

---

### `TweetMedia`

Stores media attachments (photos, videos, GIFs) for a tweet.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. |
| `tweet` | `ForeignKey(Tweet)` | The tweet this media belongs to. |
| `media_key` | `Text, unique` | Twitter's unique media identifier. |
| `type` | `Text, nullable` | Media type: `photo`, `video`, or `animated_gif`. |
| `media_url` | `Text, nullable` | CDN URL to the media asset. |
| `width` | `Integer, nullable` | Width in pixels. |
| `height` | `Integer, nullable` | Height in pixels. |
| `duration_ms` | `Integer, nullable` | Duration for video media; null for photos. |
| `video_variants` | `JSON, nullable` | Available quality variants for video. |
| `created_at` | `DateTime` | When this row was created. |

Relationships and constraints:
- belongs to exactly one `Tweet`
- `media_key` is unique — the same media shared across tweets is stored once
- indexed by `tweet`

Important note: Uses `extended_entities` rather than `entities` from the Twitter API — `extended_entities` contains full video variant information; `entities` only has the thumbnail.

---

### `ViewedTweet`

Records a specific user seeing a specific tweet during a specific browsing session. This is the event table — a new row is always inserted, even if the tweet already exists from a previous session. The same tweet can have many `ViewedTweet` rows across different users and sessions.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. |
| `user` | `ForeignKey(AppUser)` | User who saw the tweet. |
| `session` | `ForeignKey(BrowseSession)` | Session in which the tweet was seen. |
| `tweet` | `ForeignKey(Tweet)` | The canonical tweet that was viewed. |
| `timestamp_collected` | `BigInteger, nullable` | Collection time from the extension payload. |
| `favorite_count` | `Integer, nullable` | Like count at the moment of viewing. |
| `retweet_count` | `Integer, nullable` | Retweet count at the moment of viewing. |
| `reply_count` | `Integer, nullable` | Reply count at the moment of viewing. |
| `quote_count` | `Integer, nullable` | Quote count at the moment of viewing. |
| `bookmark_count` | `Integer, nullable` | Bookmark count at the moment of viewing. |
| `view_count` | `BigInteger, nullable` | View count at the moment of viewing. |
| `raw_data` | `JSON, nullable` | Full original JSON record from the extension, stored as a backup for re-parsing. |
| `created_at` | `DateTime` | When this row was created. |

Relationships and constraints:
- belongs to exactly one `AppUser`
- belongs to exactly one `BrowseSession`
- belongs to exactly one `Tweet`
- indexed by `user`, `session`, `tweet`

Important note: Engagement counts are captured as a snapshot at the moment of viewing — not at the time the tweet was posted. These values change over time and must not overwrite the canonical `Tweet` row.

---

### `SentimentResult`

Stores sentiment analysis output for one tweet. One result per tweet (`OneToOneField`).

| Name | Type | Description |
| --- | --- | --- |
| `tweet` | `OneToOneField(Tweet)` | The analyzed tweet. Primary key relationship. |
| `sentiment` | `Text` | Predicted label: `positive`, `neutral`, or `negative`. |
| `confidence` | `Float, nullable` | Confidence score for the predicted label. |
| `created_at` | `DateTime` | When this result was created. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Model: [cardiffnlp/twitter-roberta-base-sentiment-latest](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest)

---

### `TopicResult`

Stores topic classification output for one tweet. One result per tweet (`OneToOneField`).

| Name | Type | Description |
| --- | --- | --- |
| `tweet` | `OneToOneField(Tweet)` | The analyzed tweet. Primary key relationship. |
| `topic` | `Text` | Predicted topic label from a fixed set of 21 categories. |
| `confidence` | `Float, nullable` | Confidence score for the predicted topic. |
| `created_at` | `DateTime` | When this result was created. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Model: [cardiffnlp/tweet-topic-21-multi](https://huggingface.co/cardiffnlp/tweet-topic-21-multi)

Important note: The topic model returns one top label from a fixed category set — not freeform keywords.

---

### `LLMAnalysisRun`

Stores the result of one LLM feed blurb generation run for a user. One run is created per analysis invocation and tracks the full lifecycle from queuing through completion. The most recent completed run's reflection is surfaced in the `/api/feed-summary/` response.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. |
| `user` | `ForeignKey(AppUser)` | The user this run belongs to. |
| `status` | `Text` | Run lifecycle status: `queued`, `processing`, `complete`, `failed`. |
| `sample_size` | `Integer` | Number of tweets sampled for the prompt. |
| `sample_seed` | `BigInteger, nullable` | Random seed used for sampling, for reproducibility. |
| `model_name` | `Text` | Name of the model used (configured via `LLM_ANALYSIS_MODEL` env var). |
| `sample_metadata` | `JSON, nullable` | Metadata about the sample: tweet IDs and feed summary context used in the prompt. |
| `result` | `JSON, nullable` | Structured output from the model. Currently contains a `reflection` field with prose text. |
| `raw_output` | `Text, nullable` | Raw model output, stored for debugging. |
| `error_message` | `Text, nullable` | Error message if the run failed. |
| `created_at` | `DateTime` | When this run was created. |
| `updated_at` | `DateTime` | Automatically updated on every save. |

Relationships and constraints:
- belongs to exactly one `AppUser`
- indexed by `user`, `status`, `created_at`

Important note: The LLM prompt is built from a sample of the user's tweets combined with feed-wide stats (topics, sentiment, word frequency, promoted percentage) from `build_feed_summary()`. This gives the model context about both individual tweets and overall feed patterns when generating the reflection.