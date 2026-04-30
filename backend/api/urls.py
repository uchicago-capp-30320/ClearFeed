from django.urls import path
from . import views

urlpatterns = [
    path("import-dataset/", views.import_dataset, name="import_dataset"),
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("privacy/", views.privacy, name="privacy"),
    path("tutorial/", views.tutorial, name="tutorial"),
    path("analysis/", views.full_analysis, name="full_analysis"),
    path("sentiment_results/", views.sentiment_results, name="sentiment_results"),
    path("topic_results/", views.topic_results, name="topic_results"),
    path("toxicity_results/", views.toxicity_results, name="toxicity_results"),
]

# if the URL is import-dataset/ run the import_dataset function from views.py.
