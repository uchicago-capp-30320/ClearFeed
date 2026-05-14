# ClearFeed Endpoints (Analysis)

The following endpoints support data ingestion and analysis-related pages within the ClearFeed application.

---

## `/import_dataset`

### Parameters
- `request`: Incoming API POST request JSON from Zeeschuimer browser extension

### Function
- Parses incoming Zeeschuimer NDJSON for relevant feed data
- Ingests processed data into backend system
- This is an API endpoint and does not render an HTML template

### Response
- JSON response indicating ingestion status

### Template Context Variables
- None

---

## `/analysis`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `full_analysis.html`: HTML page displaying comprehensive analysis of user's feed data

### Template Context Variables
- `user`: corresponding `AppUser` object  
- `sentiment_results`: list of `SentimentResult` objects  
- `topic_results`: list of `TopicResult` objects  
- `political_leaning_results`: list of `PoliticalLeaningResult` objects  
- `toxicity_results`: list of `ToxicityResult` objects  

---

## `/sentiment`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `sentiment.html`: HTML page displaying sentiment-specific analysis of user's feed data

### Template Context Variables
- `user`: corresponding `AppUser` object  
- `sentiment_results`: list of `SentimentResult` objects  

---

## `/topics`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `topics.html`: HTML page displaying topic-specific analysis of user's feed data

### Template Context Variables
- `user`: corresponding `AppUser` object  
- `topic_results`: list of `TopicResult` objects  

---

## `/feed-summary`

### Parameters
- Authenticated `AppUser` from the current request session

### Response
- Combined JSON payload for the scrollable feed analysis view:

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
    "series": [
      {
        "name": "Topic as a Percent of Tweets",
        "data": [67, 33]
      }
    ]
  },
  "word_frequency": {
    "labels": ["future", "climate", "policy", "science"],
    "series": [
      {
        "name": "Frequency",
        "data": [4, 2, 2, 2]
      }
    ]
  },
  "sentiment": {
    "sentiment_average": 0,
    "labels": ["Negative", "Neutral", "Positive"],
    "series": [
      {
        "name": "Percentage of Tweets",
        "data": [33, 33, 33]
      }
    ]
  }
}
```

### Template Context Variables
- None

---

## `/political_leaning`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `political_leaning.html`: HTML page displaying political identity analysis of user's feed data

### Template Context Variables
- `user`: corresponding `AppUser` object  
- `political_leaning_results`: list of `PoliticalLeaningResult` objects  

---

## `/toxicity`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `toxicity.html`: HTML page displaying toxicity-specific analysis of user's feed data

### Template Context Variables
- `user`: corresponding `AppUser` object  
- `toxicity_results`: list of `ToxicityResult` objects  
