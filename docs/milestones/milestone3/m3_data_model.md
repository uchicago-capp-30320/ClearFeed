# ClearFeed Data Model & Processing Workflow

## Schema Overview (Tables, Columns, and Purpose)

### Table: app_user
**Purpose:** Represents a unique user of the browser extension. 

- id (uuid, PK) — generated client-side on install
- created_at (timestamptz) — account creation timestamp

NOTE: This table (and others) will necessarily change once we understand and implement authorization/log-ins for users.

---

### Table: browse_session
**Purpose:** Tracks a single browsing session in the extension.

- id (uuid, PK) — session identifier  
- user_id (uuid, FK → app_user)  
- platform (text) — twitter / x.com etc  
- user_agent (text) — browser metadata  
- status (text) — tracks overall session lifecycle  
  - `ingesting` — data is being saved to database  
  - `queued` — ingestion done, analysis job on queue  
  - `analyzing` — worker is processing tweets  
  - `complete` — all analysis done, results ready  
  - `failed` — something went wrong  
- started_at (timestamptz)  
- ended_at (timestamptz)

---

### Table: twitter_author
**Purpose:** Twitter/X user profiles (global entity, deduplicated).

- twitter_id (bigint, PK)  
- screen_name (varchar)  
- display_name (varchar)  
- bio (text)  
- location (text)  
- followers_count (int)  
- following_count (int)  
- statuses_count (int)  
- is_blue_verified (boolean)  
- account_created_at (timestamptz)  
- last_updated_at (timestamptz)  

---
### Table: tweet
**Purpose:** Stores each unique tweet once globally.

- twitter_id (bigint, PK)  
- author_twitter_id (bigint, FK → twitter_author)  
- conversation_id (bigint)  
- in_reply_to_tweet_id (bigint)  
- in_reply_to_screen_name (text)  
- timestamp_collected (bigint)  
- full_text (text)  
- hashtags (jsonb)  
- lang (varchar)  
- source_app (text)  
- source_platform_url (text)  
- is_quote_status (boolean)  
- is_retweet (boolean)  
- possibly_sensitive (boolean)  
- promoted (boolean)  
- tweet_created_at (timestamptz)  
- analysis_status (text) — tracks analysis pipeline progress  
  - `pending` — not yet analyzed  
  - `processing` — currently being analyzed  
  - `complete` — all analysis done  
  - `failed` — analysis attempted but errored

---

### Table: tweet_media
**Purpose:** Stores media attached to tweets (images/videos/GIFs).

- id (uuid, PK)  
- tweet_twitter_id (bigint, FK → tweet)  
- media_key (text, unique)  
- type (text)  
- media_url (text)  
- width (int)  
- height (int)  
- duration_ms (int)  
- video_variants (jsonb)  
- created_at (timestamptz)  


---

### Table: viewed_tweet
**Purpose:** Stores user-specific tweet view data.

- id (uuid, PK)  
- user_id (uuid, FK → app_user)  
- session_id (uuid, FK → browse_session)  
- tweet_twitter_id (bigint, FK → tweet)  
- nav_index (text)  
- source_platform (text)  
- source_platform_url (text)  
- viewed_at (timestamptz)  
- favorite_count (int)  
- retweet_count (int)  
- reply_count (int)  
- quote_count (int)  
- bookmark_count (int)  
- view_count (bigint)  
- raw_data (jsonb)  

---

### Table: sentiment_result
**Purpose:** Stores sentiment analysis outputs per tweet.

- id (uuid, PK)  
- tweet_twitter_id (bigint, FK → tweet)  
- sentiment (varchar) — positive / negative / neutral  
- confidence (real)  
- detail (jsonb)  
- analyzed_at (timestamptz)  


---

### Table: topic_result
**Purpose:** Stores topic classification outputs per tweet.

- id (uuid, PK)  
- tweet_twitter_id (bigint, FK → tweet)  
- topic (text)  
- confidence (real)  
- analyzed_at (timestamptz)  

---

### Table: political_leaning
**Purpose:** Stores political classification (subset of tweets).

- id (uuid, PK)  
- tweet_twitter_id (bigint, FK → tweet)  
- leaning (text) — left / right / centrist / unclear  
- confidence (real)  
- analyzed_at (timestamptz)  

---

### Table: toxicity_result
**Purpose:** Stores toxicity / hate speech classification outputs.

- id (uuid, PK)  
- tweet_twitter_id (bigint, FK → tweet)  
- toxicity_label (text)  
- confidence (real)  
- analyzed_at (timestamptz)  

---

## High-Level Workflow

### Step 1: Data Collection (Frontend Extension)

A user scrolls Twitter/X using the browser extension.

For each session:
- A `session_id` (UUID) is generated client-side
- Each tweet encountered becomes an NDJSON row
- Each row contains:
  - tweet data
  - author data
  - metadata (nav_index, source_platform_url, timestamp_collected)

---

### Step 2: Upload to Backend

When user clicks “To ClearFeed”:
The extension sends:

- session_id
- platform
- NDJSON file

to Django API.

---

### Step 3: Backend Ingestion Pipeline

Django parses NDJSON line-by-line and updates tables accordingly:

#### twitter_author (Upsert)

If author exists:
    Update mutable fields:
    - followers_count
    - following_count
    - statuses_count
    - display_name
    - bio
    - location
    - is_blue_verified
    - last_updated_at

If new:
- Insert full record.

Why?
- Avoids duplicating author data per tweet
- Author stats are not tied to tweet events
- We only care about latest known profile state (We think? - we took a different strategy with tweets, though)

---

#### tweet

Each tweet is stored once.

Behavior:
- Insert if not exists
- Never update existing tweet
- If exists, skip to viewed_tweet insertion


#### tweet_media

Media is stored once per media_key.

Why:
- Media is large
- Reused across users
- Avoid duplication across sessions

---

#### viewed_tweet

This table is what captures:

> “A specific user saw a specific tweet in a specific session at a specific time.”

Supports:
- multiple users seeing same tweet
- same user seeing same tweet multiple times
- session-level analysis of feed

---

#### sentiment_result (ML Layer)

Stores sentiment output per tweet in tweet table (avoid duplicate processing)

---

#### topic_result

Stores topic classification outputs per tweet in tweet table (avoids duplicate processing)

---

#### political_leaning

Stores political classification for each tweet in tweet table (avoids duplicate processing)

---

#### toxicity_result

Stores hate speech / toxicity detection outputs for each tweet in tweet table (avoids duplicate processing)

---

## Explanation of Design Choices

### 1. Scales across users (storage efficient)
Same tweet stored once, referenced many times.
Avoids repeated author/tweet/media duplication.

### 2. Preserves user experience
viewed_tweets preserves user-specific data on time-relevant stats for that tweet.

---

## Questions
1. Is our design choice of a tweet table and a viewed_tweet table achieving what we hope it is? (i.e., reducing duplicate stored info, while preserving time-sensitive stats about the tweets a user viewed during that browsing session)
2. We separated out the ML/analysis results for each tweet into separate tables because we thought this would increase flexibility in model testing. We also thought it was good for a separation of concerns. Is this reasonable?
3. We currently have the raw_data column in the viewed_tweet table to store the entire ndjson record as a backup. Is that overkill? Could it be something we test with for right now, and then get rid of down the line?
