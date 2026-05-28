# ClearFeed

Social media platforms send users an endless stream of content determined by algorithms with unknown weights and functions. People scroll through hundreds of posts daily without understanding the big picture of what is being recommended to them and whether this actually aligns with their interests.

ClearFeed is a tool designed to give users a clear summary of who and what is showing up in their feed. Users install the ClearFeed Capture browser extension, scroll their Twitter/X feed, and ClearFeed automatically ingests and analyzes the collected posts — surfacing sentiment, topic breakdowns, word frequency, promoted content percentage, and an AI-generated reflection of their feed.

## Team Members

- Grace Kluender: Project Manager, Backend Developer (secondary role)
- Yuri Chang: Data Engineering, Machine Learning (secondary role)
- Ganon Evans: Front-end/UI UX Engineer, Database Research (secondary role)
- Khushi Desai: Front-end/UI UX Engineer, ML/Data Engineering (secondary role)
- Teddy Kolios: QA Engineer, Backend Developer/Machine Learning (secondary role)

## Tech Stack

ClearFeed is a [Django](https://www.djangoproject.com/) web application with a server-rendered HTML frontend.

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Django |
| Database | PostgreSQL (hosted on [Railway](https://railway.com/)) |
| NLP — Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` (HuggingFace) |
| NLP — Topic | `cardiffnlp/tweet-topic-21-multi` (HuggingFace) |
| LLM Feed Reflection | `meta-llama/Meta-Llama-3.1-8B-Instruct` (HuggingFace) |
| Task Queue | [Django-Q](https://django-q.readthedocs.io/) |
| Testing | [pytest](https://docs.pytest.org/en/stable/) |
| Package Management | [uv](https://docs.astral.sh/uv/) |

NLP analysis runs asynchronously via Django-Q after each upload — users get an immediate response from the extension while analysis happens in the background.

## Project Structure
```
ClearFeed/
├── backend/                        # Django application root
│   ├── api/                        # Main Django app
│   │   ├── management/             # Custom management commands
│   │   ├── services/               # Business logic (ingestion, analysis, feed summary)
│   │   ├── tests/                  # Unit and integration tests
│   │   ├── models.py               # Data models
│   │   ├── views.py                # API and page views
│   │   ├── urls.py                 # App-level URL routing
│   │   └── tasks.py                # Django-Q async task definitions
│   ├── clearfeed_django/           # Django project configuration
│   │   ├── settings.py
│   │   └── urls.py                 # Top-level URL routing
│   └── manage.py
├── docs/                           # Project documentation
│   ├── decisions/                  # Architecture decision records
│   ├── endpoints/                  # API and page endpoint documentation
│   ├── milestones/                 # Milestone deliverables
│   └── testing/                   # Testing documentation
├── static/                         # Source static files (CSS, JS, images)
├── staticfiles/                    # Collected static files (generated, do not edit)
├── templates/                      # Django HTML templates
├── pyproject.toml                  # Project dependencies
└── uv.lock
```

## Development Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.
2. Run `uv sync` to set up the Python environment and install dependencies.

```bash
uv sync
```

3. Run database migrations:

```bash
cd backend
python manage.py migrate
```

## User Installation

ClearFeed requires Firefox and works alongside the **ClearFeed Capture** browser extension, a forked and modified version of [Zeeschuimer](https://github.com/digitalmethodsinitiative/zeeschuimer) distributed as a signed unlisted Firefox extension.

To get started:

1. Install the ClearFeed Capture extension in Firefox.
2. Create a ClearFeed account at `/signup/`.
3. Make sure you are logged into ClearFeed, Twitter/X, and have the extension active — all in the same Firefox browser.
4. Navigate to Twitter/X and scroll your feed. The extension collects post data as you scroll — we recommend at least 100 posts for a meaningful analysis.
5. Use the extension to send your collected data to ClearFeed. Analysis runs automatically in the background.
6. Once complete, your feed summary will be available in the ClearFeed dashboard.

ClearFeed currently only supports Twitter/X.
