import json
import os
import re

from transformers import pipeline


MODEL_NAME = os.getenv("LLM_ANALYSIS_MODEL", "google/flan-t5-small")
PROMPT_VERSION = "v1"
_generator = None

EXPECTED_KEYS = [
    "title",
    "themes",
    "patterns",
    "surprises",
    "follow_up_question",
]


def get_llm_generator():
    global _generator
    if _generator is None:
        _generator = pipeline("text2text-generation", model=MODEL_NAME)
    return _generator


def analyze_sampled_tweets(tweets):
    """
    Build a prompt from sampled tweets, call the LLM, and normalize output.

    Returns a dict containing the raw model output plus a structured analysis
    payload that the orchestration layer can persist.
    """
    prompt = build_analysis_prompt(tweets)

    try:
        generator = get_llm_generator()
        result = generator(prompt, max_new_tokens=256, do_sample=False)
        raw_output = ""
        if result and isinstance(result, list):
            raw_output = result[0].get("generated_text", "") or ""
        structured = parse_analysis_output(raw_output)
        return {
            "model_name": MODEL_NAME,
            "prompt_version": PROMPT_VERSION,
            "prompt": prompt,
            "raw_output": raw_output,
            "analysis": structured,
            "parse_status": "ok" if structured.get("title") else "fallback",
        }
    except Exception as exc:
        fallback = build_fallback_analysis(tweets, str(exc))
        return {
            "model_name": MODEL_NAME,
            "prompt_version": PROMPT_VERSION,
            "prompt": prompt,
            "raw_output": "",
            "analysis": fallback,
            "parse_status": "fallback",
        }


def build_analysis_prompt(tweets):
    top_words = _top_words(tweets)
    top_authors = _top_authors(tweets)
    tweet_lines = [
        f"{index + 1}. @{tweet['screen_name'] or 'unknown'} ({tweet['author_name']}): {tweet['text']}"
        for index, tweet in enumerate(tweets)
    ]

    return (
        "You are a sharp social media analyst.\n"
        "Analyze this random sample of tweets from one person and return JSON only.\n"
        "Use this schema exactly:\n"
        "{"
        '"title": "short headline", '
        '"themes": ["one sentence fragments"], '
        '"patterns": ["bullet-like observations"], '
        '"surprises": ["unexpected observations"], '
        '"follow_up_question": "one question"'
        "}\n"
        "Do not include markdown fences or extra commentary.\n\n"
        f"Sample size: {len(tweets)}\n"
        f"Top authors: {', '.join(top_authors) if top_authors else 'none'}\n"
        f"Top words: {', '.join(top_words) if top_words else 'none'}\n\n"
        "Tweets:\n" + "\n".join(tweet_lines)
    )


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

    return {
        "title": "Feed snapshot",
        "themes": [
            f"Repeated words: {', '.join(top_words) if top_words else 'none'}",
            f"Visible authors: {', '.join(top_authors) if top_authors else 'none'}",
        ],
        "patterns": [
            f"{round((reply_count / total) * 100)}% of the sample are replies",
            f"{round((promoted_count / total) * 100)}% of the sample are promoted tweets",
        ],
        "surprises": [
            "A random sample is often enough to tell whether the feed is conversational, news-heavy, or creator-driven."
        ],
        "follow_up_question": "Which authors or topics dominate when the sample size increases?",
        "fallback_reason": reason,
    }


def _normalize_analysis(data):
    analysis = _empty_analysis()
    for key in EXPECTED_KEYS:
        value = data.get(key)
        if key == "follow_up_question":
            analysis[key] = _coerce_text(value)
        else:
            analysis[key] = _coerce_list(value)

    if isinstance(analysis["title"], list):
        analysis["title"] = analysis["title"][0] if analysis["title"] else ""

    if not analysis["title"]:
        analysis["title"] = _coerce_text(data.get("title"))

    return analysis


def _fallback_from_text(raw_output):
    cleaned = raw_output.strip()
    lines = [line.strip("-• \t") for line in cleaned.splitlines() if line.strip()]
    analysis = _empty_analysis()
    if lines:
        analysis["title"] = lines[0][:120]
        if len(lines) > 1:
            analysis["themes"] = lines[1:2]
        if len(lines) > 2:
            analysis["patterns"] = lines[2:4]
        if len(lines) > 4:
            analysis["surprises"] = lines[4:5]
        analysis["follow_up_question"] = lines[-1][:180]
    else:
        analysis["title"] = "Feed snapshot"
        analysis["follow_up_question"] = "What stands out most in this sample?"
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
        "title": "",
        "themes": [],
        "patterns": [],
        "surprises": [],
        "follow_up_question": "",
    }


def _coerce_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _coerce_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    return [str(value).strip()]


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
