from django.urls import path
from . import views

urlpatterns = [
    path("import-dataset/", views.import_dataset, name="import_dataset"),
    path("topics/", views.topic_distribution_testing),
    path("topics-summary/", views.topic_summary, name="topic_summary"),
    path("", views.home, name="home"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("profile/", views.profile, name="profile"),
    path("privacy/", views.privacy, name="privacy"),
    path("analysis/", views.full_analysis, name="full_analysis"),
    path("topic_results/", views.topic_distribution, name="topic_distribution"),
]

# if the URL is import-dataset/ run the import_dataset function from views.py.
