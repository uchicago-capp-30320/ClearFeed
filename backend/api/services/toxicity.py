from transformers import pipeline


MODEL_NAME = "s-nlp/roberta_toxicity_classifier"
_classifier = None


def get_toxicity_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline("text-classification", model=MODEL_NAME, top_k=None)
    return _classifier


def analyze_toxicity_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_toxicity_classifier()
    results = classifier(text)[0]
    top_result = max(results, key=lambda item: item["score"])

    # Output: top toxicity label like neutral/toxic and its score.
    return {
        "toxicity_label": top_result["label"].lower(),
        "confidence": float(top_result["score"]),
    }
