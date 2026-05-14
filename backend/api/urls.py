from django.urls import path

from . import views

urlpatterns = [
    path("import-dataset/", views.import_dataset, name="import_dataset"),
    path(
        "sessions/<uuid:session_id>/status/",
        views.session_status,
        name="session_status",
    ),
    path("feed-summary/", views.feed_summary, name="feed_summary"),
    path("", views.home, name="home"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("profile/", views.profile, name="profile"),
    path("privacy/", views.privacy, name="privacy"),
    path("analysis/", views.full_analysis, name="full_analysis"),
    path("wordcloud/", views.wordcloud_page, name="wordcloud_page"),
    path("topic_results/", views.topic_results, name="topic_results"),
]

# if the URL is import-dataset/ run the import_dataset function from views.py.
