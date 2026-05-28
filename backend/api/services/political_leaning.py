from transformers import pipeline


MODEL_NAME = "matous-volf/political-leaning-politics"
TOKENIZER_NAME = "launch/POLITICS"
_classifier = None
LABEL_MAP = {
    "LABEL_0": "left",
    "LABEL_1": "center",
    "LABEL_2": "right",
}


def get_political_leaning_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            tokenizer=TOKENIZER_NAME,
            top_k=1,
        )
    return _classifier


def analyze_political_leaning_text(text):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_political_leaning_classifier()
    result = classifier(text)[0][0]

    # Output: one political leaning label like left/center/right and a score.
    return {
        "leaning": LABEL_MAP.get(result["label"], result["label"].lower()),
        "confidence": float(result["score"]),
    }
