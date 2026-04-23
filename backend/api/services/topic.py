from transformers import pipeline


MODEL_NAME = "WebOrganizer/TopicClassifier"
_classifier = None


def get_topic_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline("text-classification", model=MODEL_NAME, top_k=1)
    return _classifier


def analyze_topic_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_topic_classifier()
    result = classifier(text)[0]

    return {
        "topic": result["label"].lower(),
        "confidence": float(result["score"]),
    }
