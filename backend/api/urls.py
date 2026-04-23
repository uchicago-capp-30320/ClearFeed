from django.urls import path
from . import views

urlpatterns = [
    path('import-dataset/', views.import_dataset, name='import_dataset'),
    path('analyze-sentiment/', views.analyze_sentiment, name='analyze_sentiment'),
]

# if the URL is import-dataset/ run the import_dataset function from views.py.
