from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"

    def ready(self):
        """
        Pre-load all ML models when Django starts.
        This avoids timeouts on the first upload request.
        """

        from api.services.sentiment import get_sentiment_classifier
        from api.services.toxicity import get_toxicity_classifier
        from api.services.topic import get_topic_classifier

        get_sentiment_classifier()
        get_toxicity_classifier()
        get_topic_classifier()
