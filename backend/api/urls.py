from django.urls import path

from . import views

urlpatterns = [
    path("import-dataset/", views.import_dataset, name="import_dataset"),
    path("llm-analysis/runs/", views.llm_analysis_runs, name="llm_analysis_runs"),
    path(
        "llm-analysis/runs/<uuid:run_id>/",
        views.llm_analysis_run_detail,
        name="llm_analysis_run_detail",
    ),
    path(
        "sessions/<uuid:session_id>/status/",
        views.session_status,
        name="session_status",
    ),
    path("feed-summary/", views.api_feed_summary, name="api_feed_summary"),
    path("", views.home, name="home"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("profile/", views.profile, name="profile"),
    path("privacy/", views.privacy, name="privacy"),
    path("landing/", views.landing, name="landing"),
]

# if the URL is import-dataset/ run the import_dataset function from views.py.
