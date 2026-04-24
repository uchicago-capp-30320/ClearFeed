⸻

ClearFeed Endpoints (Analysis)

The following endpoints support data ingestion and analysis-related pages within the ClearFeed application.

⸻

/import_dataset

Parameters:

* request: Incoming API POST request JSON from Zeeschuimer browser extension

Function:

* This view parses through incoming Zeeschuimer NDJSON for relevant feed data and ingests accordingly into backend system. This is an API endpoint and does not on its own redirect to any HTML template.

Response:

* JSON response indicating ingestion status

Template Context Variables:

* None

⸻

/analysis

Parameters:

* user_id: PK to AppUser

Response:

* full_analysis.html: HTML page displaying comprehensive analysis of user's feed data

Template Context Variables:

* user: corresponding AppUser object

* sentiment_results: list of SentimentResult model objects traced to user

* topic_results: list of TopicResult model objects traced to user

* political_leaning_results: list of PoliticalLeaningResult model objects traced to user

* toxicity_results: list of ToxicityResult model objects traced to user

⸻

/sentiment

Parameters:

* user_id: PK to AppUser

Response:

* sentiment.html: HTML page displaying sentiment-specific analysis of user's feed data

Template Context Variables:

* user: corresponding AppUser object

* sentiment_results: list of SentimentResult model objects traced to user

⸻

/topics

Parameters:

* user_id: PK to AppUser

Response:

* topics.html: HTML page displaying topic-specific analysis of user's feed data

Template Context Variables:

* user: corresponding AppUser object

* topic_results: list of TopicResult model objects traced to user

⸻

/political_leaning

Parameters:

* user_id: PK to AppUser

Response:

* political_leaning.html: HTML page displaying political identity analysis of user's feed data

Template Context Variables:

* user: corresponding AppUser object

* political_leaning_results: list of PoliticalLeaningResult model objects traced to user

⸻

/toxicity

Parameters:

* user_id: PK to AppUser

Response:

* toxicity.html: HTML page displaying toxicity-specific analysis of user's feed data

Template Context Variables:

* user: corresponding AppUser object

* toxicity_results: list of ToxicityResult model objects traced to user

⸻