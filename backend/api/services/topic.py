from transformers import pipeline


MODEL_NAME = "cardiffnlp/tweet-topic-21-multi"
_classifier = None


def get_topic_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline("text-classification", model=MODEL_NAME, top_k=None)
    return _classifier


def analyze_topic_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_topic_classifier()
    results = classifier(text)[0]
    top_result = max(results, key=lambda item: item["score"])

    # Output: the highest-scoring topic label and its score.
    return {
        "topic": top_result["label"].lower(),
        "confidence": float(top_result["score"]),
    }
