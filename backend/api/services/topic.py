from transformers import pipeline


MODEL_NAME = "WebOrganizer/TopicClassifier"
_classifier = None


def get_topic_classifier():
    # Load the model once, then reuse it for later requests.
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            top_k=1,
            trust_remote_code=True,
            use_memory_efficient_attention=False,
        )
    return _classifier


def analyze_topic_text(text, url=""):
    # Run the Hugging Face model on one piece of tweet text.
    classifier = get_topic_classifier()
    model_input = f"{url}\n\n{text}" if url else text
    result = classifier(model_input)[0]

    # Output: one topic label such as Adult, Art & Design, Software Dev.,
    # Crime & Law, Education & Jobs, Hardware, Entertainment, Social Life,
    # Fashion & Beauty, Finance & Business, Food & Dining, Games, Health,
    # History, Home & Hobbies, Industrial, Literature, Politics, Religion,
    # Science & Tech., Software, Sports & Fitness, Transportation, or Travel,
    # plus a score.
    return {
        "topic": result["label"].lower(),
        "confidence": float(result["score"]),
    }
