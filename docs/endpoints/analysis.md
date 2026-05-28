# ClearFeed Endpoints (Analysis)

The following endpoints support data ingestion and feed analysis within the ClearFeed application.

---

## `POST /api/import-dataset/`

Receives raw NDJSON from the ClearFeed Capture browser extension and runs it through the ingestion pipeline. CSRF exempt. Requires an authenticated session (the extension sends the session cookie via `credentials: 'include'`).

### Headers
- `X-Zeeschuimer-Platform`: Source platform identifier (defaults to `"unknown"`)
- `User-Agent`: Browser user agent string

### Response
```json
{
  "status": "success",
  "session_id": "<uuid>",
  "posts_received": 42
}
```

### Error Responses
- `401` — User not authenticated
- `400` — Malformed request body
- `500` — Ingestion pipeline failure

---

## `GET /api/sessions/<session_id>/status/`

Returns the NLP analysis progress for a specific browse session. Requires authentication.

### URL Parameters
- `session_id` (UUID): The `BrowseSession` primary key

### Response
```json
{
  "session_id": "<uuid>",
  "status": "analyzing",
  "tweet_count": 50,
  "pending_count": 10,
  "processing_count": 5,
  "complete_count": 30,
  "failed_count": 5,
  "progress": 70
}
```

### Error Responses
- `401` — User not authenticated
- `404` — Session not found or does not belong to the user

---

## `POST /api/llm-analysis/runs/`

Queues a new LLM feed blurb generation run for the authenticated user. CSRF exempt.

### Parameters (form body)
- `sample_size` (integer, optional): Number of tweets to sample. Defaults to `10`.
- `seed` (integer, optional): Random seed for reproducibility. Omit or leave blank for no seed.

### Response (`201`)
```json
{
  "run_id": "<uuid>",
  "status": "queued",
  "sample_size": 10
}
```

### Error Responses
- `401` — User not authenticated
- `400` — Invalid seed value or other validation error
- `405` — Method not allowed (non-POST request)

---

## `GET /api/llm-analysis/runs/<run_id>/`

Returns the full detail of a specific LLM analysis run. CSRF exempt.

### URL Parameters
- `run_id` (UUID): The `LLMAnalysisRun` primary key

### Response
```json
{
  "run_id": "<uuid>",
  "status": "complete",
  "sample_size": 10,
  "sample_seed": null,
  "model_name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
  "sample_metadata": {},
  "result": { "reflection": "..." },
  "raw_output": "...",
  "error_message": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:01Z"
}
```

### Error Responses
- `401` — User not authenticated
- `404` — Run not found or does not belong to the user

---

## `GET /api/feed-summary/`

Returns the combined JSON payload for the scrollable feed analysis view. Includes feed statistics and the most recent LLM reflection. Auth via session cookie or `user_id` query parameter.

### Query Parameters
- `user_id` (UUID, optional): Used when the user is not authenticated via session cookie.

### Response
```json
{
  "overview": {
    "top_users": [],
    "total_tweets": 0,
    "since_date": "",
    "promoted_percentage": 0
  },
  "categories": {
    "labels": ["Cats", "Politics"],
    "series": [{ "name": "Topic as a Percent of Tweets", "data": [67, 33] }]
  },
  "word_frequency": {
    "labels": ["future", "climate", "policy"],
    "series": [{ "name": "Frequency", "data": [4, 2, 2] }]
  },
  "sentiment": {
    "sentiment_average": 0,
    "labels": ["Negative", "Neutral", "Positive"],
    "series": [{ "name": "Percentage of Tweets", "data": [33, 33, 33] }]
  },
  "llm_analysis": {
    "status": "complete",
    "reflection": "...",
    "run_id": "<uuid>",
    "model_name": "...",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

> **Note:** `top_users` is the top 5 authors of promoted tweets by frequency, not top accounts overall. `since_date` is the date of the user's first ever viewed tweet (ISO 8601 format). `promoted_percentage` is the percentage of the user's viewed tweets that were served as paid ads.

### Error Responses
- `401` — User not authenticated and no valid `user_id` provided
- `404` — `user_id` provided but user not found

---

## `GET /feed-summary/`

Renders the scrollable feed analysis page. Data is fetched client-side from `GET /api/feed-summary/`.

### Response
- `user_scroll.html`

---

## `GET /home/` and `GET /api/home-summary/`

Returns basic summary statistics for the authenticated user's account. Requires authentication.

### Response
```json
{
  "summary_stats": {
    "total_sessions": 2,
    "total_tweets": 70,
    "days_since_last": 9
  }
}
```

### Error Responses
- `401` — User not authenticated