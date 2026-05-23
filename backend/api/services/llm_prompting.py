import json
import os
import re

from transformers import pipeline


MODEL_NAME = os.getenv("LLM_ANALYSIS_MODEL", "microsoft/Phi-3.5-mini-instruct")
_generator = None


def get_llm_generator():
    global _generator
    if _generator is None:
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
    tweet_lines = [
        f"{index + 1}. @{tweet['screen_name'] or 'unknown'} ({tweet['author_name']}): {tweet['text']}"
        for index, tweet in enumerate(tweets)
    ]
    feed_context = _format_feed_summary_context(feed_summary)

    return (
        "You are a sharp social media analyst.\n"
        "Write a thoughtful reflection on what these tweets suggest about the person.\n"
        "Keep it natural, interesting, and human.\n"
        "Return JSON only with this schema:\n"
        "{"
        '"reflection": "2-4 short paragraphs separated by blank lines"'
        "}\n"
        "The reflection should sound like a real observation, not a report.\n"
        "Do not include markdown fences or extra commentary.\n\n"
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

    parsed = _load_json_from_text(raw_output)
    if parsed:
        return _normalize_analysis(parsed)

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
