import json
import os
import re

from transformers import pipeline


MODEL_NAME = os.getenv("LLM_ANALYSIS_MODEL", "microsoft/Phi-3.5-mini-instruct")
_generator = None


def get_llm_generator():
    global _generator
    if _generator is None:
        # Keep the pipeline cached for the life of the process; loading the model
        # is expensive and this service is called repeatedly by the runner.
        _generator = pipeline("text-generation", model=MODEL_NAME)
    return _generator


def analyze_sampled_tweets(tweets, feed_summary=None):
    """
    Build a prompt from sampled tweets, call the LLM, and normalize output.

    The contract is prose-first: a reflective response in a single text field.
    """
    prompt = build_analysis_prompt(tweets, feed_summary=feed_summary)

    try:
        generator = get_llm_generator()
        # Some tokenizers need the prompt wrapped in a chat template, but the
        # fallback keeps plain-text prompts working for simpler pipelines.
        model_input = _format_model_input(generator, prompt)
        result = generator(
            model_input,
            max_new_tokens=256,
            do_sample=False,
            return_full_text=False,
        )
        raw_output = ""
        if result and isinstance(result, list):
            raw_output = result[0].get("generated_text", "") or ""
        # The model is instructed to return JSON, but we still normalize the
        # output so callers get a stable schema even when the model drifts.
        structured = parse_analysis_output(raw_output)
        return {
            "model_name": MODEL_NAME,
            "prompt": prompt,
            "raw_output": raw_output,
            "analysis": structured,
            "parse_status": "ok" if structured.get("reflection") else "fallback",
        }
    except Exception as exc:
        fallback = build_fallback_analysis(tweets, str(exc))
        return {
            "model_name": MODEL_NAME,
            "prompt": prompt,
            "raw_output": "",
            "analysis": fallback,
            "parse_status": "fallback",
        }


def build_analysis_prompt(tweets, feed_summary=None):
    top_words = _top_words(tweets)
    top_authors = _top_authors(tweets)
    # Each sampled tweet becomes a numbered line so the model can cite concrete
    # evidence instead of free-associating from aggregate stats alone.
    tweet_lines = [
        f"{index + 1}. @{tweet['screen_name'] or 'unknown'} ({tweet['author_name']}): {tweet['text']}"
        for index, tweet in enumerate(tweets)
    ]
    feed_context = _format_feed_summary_context(feed_summary)

    return (
        "You are a witty digital anthropologist — part therapist, part roast comedian, part fortune teller. \n"
        "You've spent years analyzing what people consume online, and you can read someone's soul from their feed.\n"
        "Your job: write a personality reading for someone based on their Twitter/X feed activity.\n"
        "Address them directly as 'you'. Be playful, a little too accurate, and lightly roast them — but keep it warm, not mean.\n"
        "Think: 'a friend who knows you embarrassingly well' meets 'horoscope that's weirdly specific'.\n"
        "Tone rules:\n"
        "- Witty and observational, not corporate or clinical\n"
        "- Allowed to gently roast, not allowed to be cruel\n"
        "- Specific details make it funny — use the actual words and authors from their feed\n"
        "- Avoid: 'This person seems to...', therapy-speak, generic praise\n\n"
        "Return JSON only, no markdown fences, using this exact schema:\n"
        "{\n"
        "  \"title\": \"a 4-7 word punchy label for this person (e.g. 'Reluctant Optimist Who Hate-Reads Finance Twitter', 'Chaotic Intellectual With a Meme Problem')\",\n"
        '  "reflection": "Start with a punchy one-liner. Then 2-3 paragraphs. End with a single-sentence verdict that sounds like a fortune cookie written by someone who is tired of your nonsense. Less than 120 words."\n'
        "}\n\n"
        f"{feed_context}"
        f"Sample size: {len(tweets)}\n"
        f"Top authors: {', '.join(top_authors) if top_authors else 'none'}\n"
        f"Top words: {', '.join(top_words) if top_words else 'none'}\n\n"
        "Tweets:\n" + "\n".join(tweet_lines)
    )


def _format_model_input(generator, prompt):
    tokenizer = getattr(generator, "tokenizer", None)
    if tokenizer and hasattr(tokenizer, "apply_chat_template"):
        messages = [{"role": "user", "content": prompt}]
        try:
            # Chat-tuned models expect role-tagged messages rather than a raw
            # prompt string, so prefer that format when the tokenizer supports it.
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            return prompt
    return prompt


def parse_analysis_output(raw_output):
    """
    Try hard to parse a structured JSON payload out of model output.
    """
    if not raw_output:
        return _empty_analysis()

    # First try the strict contract: the model returned JSON exactly as asked.
    parsed = _load_json_from_text(raw_output)
    if parsed:
        return _normalize_analysis(parsed)

    # If the model ignored the schema, salvage a readable reflection from text.
    return _fallback_from_text(raw_output)


def build_fallback_analysis(tweets, reason):
    top_words = _top_words(tweets)
    top_authors = _top_authors(tweets)
    reply_count = sum(1 for tweet in tweets if tweet.get("is_reply"))
    promoted_count = sum(1 for tweet in tweets if tweet.get("promoted"))
    total = len(tweets) or 1

    reflection = (
        "These tweets read like a feed shaped by "
        f"{', '.join(top_words[:3]) if top_words else 'general conversation'}."
    )
    if top_authors:
        reflection += (
            f" The most visible voices are {', '.join(top_authors[:3])},"
            " which gives the sample a fairly focused feel."
        )
    reflection += (
        f"\n\nAbout {round((reply_count / total) * 100)}% of the tweets are replies, "
        f"and about {round((promoted_count / total) * 100)}% are promoted."
    )

    return {
        "reflection": reflection,
        "fallback_reason": reason,
    }


def _format_feed_summary_context(feed_summary):
    if not feed_summary:
        return ""

    overview = (
        feed_summary.get("overview", {}) if isinstance(feed_summary, dict) else {}
    )
    categories = (
        feed_summary.get("categories", {}) if isinstance(feed_summary, dict) else {}
    )
    word_frequency = (
        feed_summary.get("word_frequency", {}) if isinstance(feed_summary, dict) else {}
    )
    sentiment = (
        feed_summary.get("sentiment", {}) if isinstance(feed_summary, dict) else {}
    )

    lines = ["Feed-wide stats:\n"]

    top_users = overview.get("top_users") or []
    lines.append(
        "- Overview: "
        f"total tweets {overview.get('total_tweets', 0)}, "
        f"since {overview.get('since_date') or 'unknown'}, "
        f"promoted tweets {overview.get('promoted_percentage', 0)}%, "
        f"top users {', '.join(top_users) if top_users else 'none'}.\n"
    )

    category_labels = categories.get("labels") or []
    category_series = categories.get("series") or [{}]
    # The summary data is chart-shaped, so flatten the first series into a
    # human-readable list for the prompt.
    category_data = category_series[0].get("data") if category_series else []
    category_pairs = _format_labeled_values(category_labels, category_data, unit="%")
    lines.append(f"- Topics: {category_pairs if category_pairs else 'none'}.\n")

    word_labels = word_frequency.get("labels") or []
    word_series = word_frequency.get("series") or [{}]
    word_data = word_series[0].get("data") if word_series else []
    word_pairs = _format_labeled_values(word_labels, word_data)
    lines.append(f"- Word frequency: {word_pairs if word_pairs else 'none'}.\n")

    sentiment_labels = sentiment.get("labels") or []
    sentiment_series = sentiment.get("series") or [{}]
    sentiment_data = sentiment_series[0].get("data") if sentiment_series else []
    sentiment_pairs = _format_labeled_values(sentiment_labels, sentiment_data, unit="%")
    lines.append(
        "- Sentiment: "
        f"average {sentiment.get('sentiment_average', 0)}, "
        f"{sentiment_pairs if sentiment_pairs else 'none'}.\n\n"
    )

    return "".join(lines)


def _format_labeled_values(labels, values, unit=""):
    pairs = []
    for label, value in zip(labels, values):
        suffix = f"{unit}" if unit else ""
        pairs.append(f"{label} ({value}{suffix})")
    return ", ".join(pairs)


def _normalize_analysis(data):
    analysis = _empty_analysis()
    analysis["reflection"] = _coerce_text(data.get("reflection"))

    if not analysis["reflection"]:
        analysis["reflection"] = _coerce_text(data.get("text"))

    return analysis


def _fallback_from_text(raw_output):
    cleaned = raw_output.strip()
    analysis = _empty_analysis()
    if cleaned:
        analysis["reflection"] = cleaned
    else:
        analysis["reflection"] = (
            "This sample does not have enough signal for a useful reflection."
        )
    return analysis


def _load_json_from_text(text):
    text = text.strip()
    candidates = [text]
    # Models sometimes wrap the JSON in extra prose, so try the first JSON object
    # embedded in the text before giving up.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.insert(0, match.group(0))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _empty_analysis():
    return {
        "reflection": "",
    }


def _coerce_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n\n".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _top_words(tweets):
    # Below are some functions that extract some statistics, but
    # only from the sampled tweets. Since the LLM will just be a funny
    # reflection it doesn't need to be extremely accurate which requires to include all tweets.
    counts = {}
    for tweet in tweets:
        for word in _tokenize(tweet.get("text", "")):
            counts[word] = counts.get(word, 0) + 1

    return [
        word
        for word, _count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )[:8]
    ]


def _top_authors(tweets):
    counts = {}
    for tweet in tweets:
        author = tweet.get("screen_name") or tweet.get("author_name") or ""
        if not author:
            continue
        counts[author] = counts.get(author, 0) + 1

    return [
        author
        for author, _count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )[:5]
    ]


def _tokenize(text):
    # Strip URLs and handles before counting words so the top terms emphasize
    # actual topics rather than account names or link noise.
    cleaned = re.sub(r"https?://\S+|www\.\S+|@\w+", " ", text.lower())
    return [
        word
        for word in re.findall(r"[a-z][a-z']+", cleaned)
        if len(word) > 2
        and word
        not in {
            "about",
            "after",
            "also",
            "and",
            "are",
            "for",
            "from",
            "have",
            "that",
            "the",
            "this",
            "was",
            "were",
            "with",
            "you",
        }
    ]
