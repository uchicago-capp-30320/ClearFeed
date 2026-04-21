# ClearFeed

Social media platforms send users an endless stream of content determined by algorithms with unknown weights and functions. People scroll through hundreds of posts daily without understand the big picture of what is being recommended to them and whether this actually aligns with their interests.

ClearFeed is a tool designed to give users a simple summary of who and what is showing up in their scrolling. The project begins as a modification of [Zeeschuimer](https://github.com/digitalmethodsinitiative/zeeschuimer), a browser extension that collects data from various online social media web interfaces. Using this tool, ClearFeed takes the metadata from posts and uses a local LLM to summarize content genres, common users, and flag uncomfortable topics.

## Team Members

- Grace Kluender: Project Manager, Backend Developer (secondary role)
- Yuri Chang: Data Engineering, Machine Learning (secondary role)
- Ganon Evans: Front-end/UI UX Engineer, Database Research (secondary role)
- Khushi Desai: Front-end/UI UX Engineer, ML/Data Engineering (secondary role)
- Teddy Kolios: QA Engineer, Backend Developer/Machine Learning (secondary role)

## Development
ClearFeed is in early development. The steps to begin developing this project is:

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), if you haven't already.
2. Install [Django](https://www.djangoproject.com/download/), the web framework that links our backend databases and model to the frontend website.
3. Run `uv sync` to set up the relevant Python environment

```bash
$ uv sync
```

### Tech Stack
This is a [Django](https://www.djangoproject.com/) application that will use a Javascript-based frontend such as [Vue](https://vuejs.org/). Our backend is coded in [Python >3.10](https://www.python.org/downloads/) and uses a local [HuggingFace](https://huggingface.co/) model for text analysis. Our data is stored on a [postgreSQL](https://www.postgresql.org/) server through [Railway](https://railway.com/). We use [pytest](https://docs.pytest.org/en/stable/) for our testing.

The following is our proposed folder structure
```
ClearFeed/
├── .github/
│   └── workflows/          // GitHub CI/CD files
│       ├── ci-tests.yml
│       └── ci-lint.yml
│
├── backend/                // Django backend application
│   ├── api/                // API app with models, views, and routes
│   │   ├── migrations/     // Database migration files
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py        // Django admin configuration
│   │   ├── apps.py         // App configuration
│   │   ├── models.py       // Database models
│   │   ├── urls.py         // API route definitions
│   │   └── views.py        // API view handlers
│   ├── clearfeed_django/   // Django project config
│   │   ├── __init__.py
│   │   ├── asgi.py         // ASGI entry point
│   │   ├── settings.py     // Django settings
│   │   ├── urls.py         // Root URL configuration
│   │   └── wsgi.py         // WSGI entry point
│   └── manage.py           // Django management CLI
│
├── frontend/               // React frontend files
│
├── tests/                  // Contains all tests for the project
│   ├── __init__.py
│   └── test.py
│
├── docs/                   // Documentation, wireframes, and models
│   ├── index.md            // Documentation landing page
│   ├── architecture.md     // System architecture overview
│   ├── models.md           // Data model documentation
│   ├── changelog.md        // Project changelog
│   ├── endpoints/          // API endpoint documentation
│   │   └── import.md
│   └── decisions/          // Architecture decision records
│
├── pyproject.toml          // Python project configuration
├── uv.lock                 // uv dependency lockfile
│
├── .gitignore
├── .env                    // Environment variables (not committed)
├── .env.example            // Example environment file (committed)
├── .pre-commit-config.yaml // Pre-commit hook configuration
├── README.md
└── LICENSE
```

## User Installation

ClearFeed has two major steps: the first is to install [our modified version](https://github.com/teddykolios11/capp-zeeschuimer) of the Zeeschuimer web extension that sends API request to our internal URL. With the extension on, users can scroll on a social media platform for how many posts they'd like - we'd recommend at least 100 for the original analysis. Our platform is currently developing with X/Twitter but may expand support to other services in the future.

Once the user has scrolled, they can use the extension to produce a JSON file sent to ClearFeed's servers. ClearFeed will then analyze the data and update the user's profile when done.
