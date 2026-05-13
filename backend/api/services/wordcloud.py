import re


WORDCLOUD_LIMIT = 20
WORDCLOUD_STOP_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "being",
    "but",
    "can",
    "could",
    "did",
    "does",
    "for",
    "from",
    "get",
    "had",
    "has",
    "have",
    "her",
    "here",
    "him",
    "his",
    "how",
    "https",
    "into",
    "just",
    "like",
    "more",
    "not",
    "now",
    "our",
    "out",
    "over",
    "she",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "was",
    "were",
    "what",
    "when",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
}


def tokenize_words(text):
    cleaned = re.sub(r"https?://\S+|www\.\S+|@\w+", " ", text.lower())
    return [
        word
        for word in re.findall(r"[a-z][a-z']+", cleaned)
        if len(word) > 2 and word not in WORDCLOUD_STOP_WORDS
    ]
