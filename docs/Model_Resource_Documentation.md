# Model/Resource Documentation

This document describes the main data entities and API resource used by ClearFeed's current backend.
The system ingests tweet data exported by a browser extension, stores normalized tweet metadata, and runs text analysis models during upload.

## Key Concepts

**Canonical tweet vs. viewed tweet**

The system separates a tweet's core content from the event of a user seeing that tweet.

- `Tweet` stores the canonical tweet record once.
- `ViewedTweet` stores that a specific user saw that tweet in a specific browsing session.

This is important because the same tweet may appear:

- in multiple user sessions
- multiple times for the same user
- with different engagement counts over time

**Session-oriented ingestion**

Every upload from the extension creates a new `BrowseSession`.
That session groups one batch of collected tweets and links them back to the user who uploaded them.

**Analysis results are stored separately**

Model outputs are not stored directly on `Tweet`.
Instead, each analysis type has its own result table, such as `SentimentResult`, `TopicResult`, and `ToxicityResult`.
This keeps the tweet record focused on source data, while result tables store derived data.

**Raw source data is partially preserved**

`ViewedTweet.raw_data` stores the original JSON record from the extension.
This is useful if the team later realizes a field was missed during parsing and needs to reprocess old uploads.

## Resource

### `POST /api/import-dataset/`

This resource accepts NDJSON from the browser extension and performs the current ingestion pipeline.

It:

- reads the uploaded NDJSON lines
- creates or finds the current `AppUser`
- creates a new `BrowseSession`
- upserts `TwitterAuthor`
- creates or reuses `Tweet`
- runs text analysis models on `Tweet.full_text`
- stores result rows
- creates `ViewedTweet`
- creates `TweetMedia`

Important note:
This endpoint currently performs both ingestion and model inference in one request, so uploads may take longer as more models are added.

## Entities

### `AppUser`

This represents one application user.
Right now the code uses a hardcoded test user, but the table is designed to support real authentication later.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. Unique identifier for one app user. |
| `created_at` | `DateTime` | Time the user record was created. |

Relationships and constraints:

- primary key is a UUID
- one `AppUser` can have many `BrowseSession`
- one `AppUser` can have many `ViewedTweet`

### `BrowseSession`

This represents one upload or browsing session from the browser extension.
It groups a batch of tweets collected during one user activity period.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key. Unique identifier for one browsing session. |
| `user` | `ForeignKey(AppUser)` | The user who owns this session. |
| `platform` | `Text` | Source platform, such as `twitter.com` or `x.com`. |
| `user_agent` | `Text, nullable` | Browser user agent string from the upload request. |
| `status` | `Text` | Session lifecycle status: `queued`, `analyzing`, `complete`, `failed`. |
| `started_at` | `DateTime` | Time the session record was created. |
| `ended_at` | `DateTime, nullable` | Time ingestion or processing finished. |

Relationships and constraints:

- belongs to exactly one `AppUser`
- one `BrowseSession` can have many `ViewedTweet`
- indexed by `user`

Important note:
The system is session-based, not only user-based.
This matters because one user may upload multiple datasets over time, and each upload should remain separate.

### `TwitterAuthor`

This stores normalized metadata about the author of a tweet.
The same author may be referenced by many tweets.

| Name | Type | Description |
| --- | --- | --- |
| `author_twitter_id` | `Text` | Primary key. Twitter/X author identifier from the source data. |
| `screen_name` | `Char(50), nullable` | Author handle, such as `@example` without the `@`. |
| `display_name` | `Char(100), nullable` | Public profile display name. |
| `bio` | `Text, nullable` | Author biography text. |
| `location` | `Text, nullable` | Profile location text. |
| `followers_count` | `Integer, nullable` | Number of followers at the time this metadata was seen. |
| `following_count` | `Integer, nullable` | Number of followed accounts. |
| `statuses_count` | `Integer, nullable` | Number of tweets/posts made by the account. |
| `is_blue_verified` | `Boolean, nullable` | Whether the account is marked as blue verified. |
| `account_created_at` | `DateTime, nullable` | Account creation time parsed from source data. |
| `last_updated_at` | `DateTime` | Timestamp automatically updated when the row is updated. |

Relationships and constraints:

- primary key is the source platform's author id
- one `TwitterAuthor` can have many `Tweet`
- `screen_name` is indexed

Important note:
This table is updated over time because author metadata can change.
For example, follower count and bio are mutable, while the author id remains stable.

### `Tweet`

This stores the canonical metadata and text for one tweet.
A tweet is stored once globally, even if it appears in many sessions.

| Name | Type | Description |
| --- | --- | --- |
| `tweet_id` | `Text` | Primary key. Source tweet identifier. |
| `author` | `ForeignKey(TwitterAuthor), nullable` | The tweet's author. |
| `conversation_id` | `Text, nullable` | Conversation/thread identifier from the source platform. |
| `is_reply` | `Boolean` | Whether the tweet is a reply. |
| `in_reply_to_tweet_id` | `Text, nullable` | Source tweet id being replied to. |
| `in_reply_to_screen_name` | `Text, nullable` | Screen name of the account being replied to. |
| `timestamp_collected` | `BigInteger, nullable` | Collection timestamp from the outer extension payload. |
| `full_text` | `Text, nullable` | Main tweet text used for NLP analysis. |
| `hashtags` | `JSON, nullable` | List of hashtag strings extracted from the tweet. |
| `lang` | `Char(10), nullable` | Language code from source metadata. |
| `source_app` | `Text, nullable` | Client application source string. |
| `source_platform_url` | `Text, nullable` | Source platform URL captured by the extension. |
| `is_quote_status` | `Boolean` | Whether the tweet quotes another tweet. |
| `is_retweet` | `Boolean` | Whether the tweet is a retweet. |
| `possibly_sensitive` | `Boolean` | Whether the platform flagged the tweet as sensitive. |
| `promoted` | `Boolean` | Whether the tweet appears to be promoted content. |
| `tweet_created_at` | `DateTime, nullable` | Original tweet creation time. |
| `analysis_status` | `Text` | NLP progress status: `pending`, `processing`, `complete`, `failed`. |

Relationships and constraints:

- primary key is the source tweet id
- belongs to zero or one `TwitterAuthor`
- one `Tweet` can have many `TweetMedia`
- one `Tweet` can have many `ViewedTweet`
- one `Tweet` can have many result rows across analysis tables
- indexed by `author`, `conversation_id`, `tweet_created_at`, and `analysis_status`

Important note:
This table stores tweet content once, while `ViewedTweet` stores each viewing event separately.
That split avoids duplicating tweet text for every session.

### `TweetMedia`

This stores media objects attached to a tweet, such as photos or videos.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this media record. |
| `tweet` | `ForeignKey(Tweet)` | The tweet this media belongs to. |
| `media_key` | `Text` | Unique media identifier from the source data. |
| `type` | `Text, nullable` | Media type such as `photo`, `video`, or `animated_gif`. |
| `media_url` | `Text, nullable` | URL to the media asset or thumbnail. |
| `width` | `Integer, nullable` | Media width in pixels. |
| `height` | `Integer, nullable` | Media height in pixels. |
| `duration_ms` | `Integer, nullable` | Duration for video media; usually null for photos. |
| `video_variants` | `JSON, nullable` | Variant list for video media. |
| `created_at` | `DateTime` | Time this media row was created. |

Relationships and constraints:

- belongs to exactly one `Tweet`
- `media_key` is unique
- indexed by `tweet`

Important note:
Media is stored separately because one tweet may have multiple media attachments.

### `ViewedTweet`

This represents a specific user seeing a specific tweet during a specific browsing session.
It is the event table that connects users, sessions, and canonical tweets.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this viewing event. |
| `user` | `ForeignKey(AppUser)` | User who saw the tweet. |
| `session` | `ForeignKey(BrowseSession)` | Session in which the tweet was seen. |
| `tweet` | `ForeignKey(Tweet)` | Canonical tweet that was viewed. |
| `timestamp_collected` | `BigInteger, nullable` | Collection time from the extension payload. |
| `favorite_count` | `Integer, nullable` | Like count at the moment the tweet was seen. |
| `retweet_count` | `Integer, nullable` | Retweet count at the moment the tweet was seen. |
| `reply_count` | `Integer, nullable` | Reply count at the moment the tweet was seen. |
| `quote_count` | `Integer, nullable` | Quote count at the moment the tweet was seen. |
| `bookmark_count` | `Integer, nullable` | Bookmark count at the moment the tweet was seen. |
| `view_count` | `BigInteger, nullable` | View count at the moment the tweet was seen. |
| `raw_data` | `JSON, nullable` | Original full source record for this viewed tweet. |

Relationships and constraints:

- belongs to exactly one `AppUser`
- belongs to exactly one `BrowseSession`
- belongs to exactly one `Tweet`
- indexed by `user`, `session`, and `tweet`

Important note:
This table stores time-sensitive engagement counts as a snapshot.
Those values can change over time, so they should not overwrite the canonical `Tweet` row.

### `SentimentResult`

This stores sentiment analysis output for one tweet.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this sentiment result. |
| `tweet` | `ForeignKey(Tweet)` | Tweet that was analyzed. |
| `sentiment` | `Text` | Predicted sentiment label, currently expected to be `positive`, `neutral`, or `negative`. |
| `confidence` | `Float, nullable` | Confidence score for the predicted label. |
| `analyzed_at` | `DateTime` | Time this result row was created. |

Relationships and constraints:

- belongs to exactly one `Tweet`
- indexed by `tweet`

### `TopicResult`

This stores topic-classification output for one tweet.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this topic result. |
| `tweet` | `ForeignKey(Tweet)` | Tweet that was analyzed. |
| `topic` | `Text` | Predicted topic label from the topic classifier. |
| `confidence` | `Float, nullable` | Confidence score for the predicted topic. |
| `analyzed_at` | `DateTime` | Time this result row was created. |

Relationships and constraints:

- belongs to exactly one `Tweet`
- indexed by `tweet`

Important note:
The topic model returns one top label from a fixed category set, not freeform keywords.

### `PoliticalLeaningResult`

This stores political-leaning analysis output for one tweet.
The model integration is planned in the schema even if the current pipeline may not yet populate it.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this result. |
| `tweet` | `ForeignKey(Tweet)` | Tweet that was analyzed. |
| `leaning` | `Text` | Predicted political leaning label, such as `left`, `right`, `centrist`, or `unclear`. |
| `confidence` | `Float, nullable` | Confidence score for the predicted leaning. |
| `analyzed_at` | `DateTime` | Time this result row was created. |

Relationships and constraints:

- belongs to exactly one `Tweet`
- indexed by `tweet`

### `ToxicityResult`

This stores toxicity-classification output for one tweet.

| Name | Type | Description |
| --- | --- | --- |
| `id` | `UUID` | Primary key for this toxicity result. |
| `tweet` | `ForeignKey(Tweet)` | Tweet that was analyzed. |
| `toxicity_label` | `Text` | Predicted toxicity label, currently expected to be something like `neutral` or `toxic`. |
| `confidence` | `Float, nullable` | Confidence score for the predicted label. |
| `analyzed_at` | `DateTime` | Time this result row was created. |

Relationships and constraints:

- belongs to exactly one `Tweet`
- indexed by `tweet`
