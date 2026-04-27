from transformers import pipeline


MODEL_NAME = "cardiffnlp/tweet-topic-21-multi"
_classifier = None


def get_topic_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            top_k=1,
        )
    return _classifier


def analyze_topic_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_topic_classifier()
    result = classifier(text)

    # cardiffnlp model with top_k=1 returns [[{'label': ..., 'score': ...}]]
    # so we need to index into the outer list first
    top = result[0][0] if isinstance(result[0], list) else result[0]

    return {
        "topic": top["label"].lower(),
        "confidence": float(top["score"]),
    }
