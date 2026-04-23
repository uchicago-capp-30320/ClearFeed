from transformers import pipeline


MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
_classifier = None


def get_sentiment_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline("sentiment-analysis", model=MODEL_NAME)
    return _classifier


def analyze_sentiment_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_sentiment_classifier()
    result = classifier(text)[0]

    return {
        "sentiment": result["label"].lower(),
        "confidence": float(result["score"]),
    }
