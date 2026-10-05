"""Keyword-based content-pillar assignment (stdlib only).

Tokenization: lowercase, strip punctuation, drop ~60 common English stopwords,
drop pure digits, drop tokens shorter than 3 chars. Unigrams are scored
against single-word seeds on the filtered stream. Multi-word seeds
("how to", "behind the scenes", "day in the life") are matched against
bigram/trigram phrases built from the stream BEFORE stopword removal —
otherwise seeds containing stopwords could never match. The pillar with the
most hits wins. Ties resolve to the earliest pillar in the PILLARS table;
titles with no hits fall back to "general".

One deliberate exception: the seed keyword "ai" is shorter than 3 chars, so
it can never survive length filtering. Short seed keywords are matched
against the pre-filter token stream instead (documented here so the rule
stays auditable).
"""

from __future__ import annotations

import re

from . import median

PILLARS = [
    # Vlogs sorts before tutorials: table order breaks ties deterministically,
    # and a vlog title containing an editing word ("Day in the Life: Shoot
    # Day vs Edit Day") should stay a vlog.
    {
        "id": "vlogs",
        "label": "Vlogs",
        "keywords": [
            "vlog",
            "behind the scenes",
            "day in the life",
            "day in my life",
            "my story",
            "studio",
        ],
    },
    {
        "id": "tutorials",
        "label": "Tutorials",
        "keywords": [
            "how to",
            "tutorial",
            "edit",
            "editing",
            "premiere",
            "davinci",
            "guide",
            "step by step",
            "workflow",
            "timeline",
            "color grade",
            "keyframes",
            "captions",
        ],
    },
    {
        "id": "ai_tools",
        "label": "AI Tools",
        "keywords": [
            "ai",
            "artificial intelligence",
            "chatgpt",
            "claude",
            "midjourney",
            "ai tool",
            "ai tools",
            "generative",
            "ai voice",
            "ai video",
            "ai edit",
            "ai research",
            "video scripts",
            "thumbnails",
        ],
    },
    {
        "id": "gear",
        "label": "Gear Reviews",
        "keywords": [
            "camera",
            "mic",
            "microphone",
            "lens",
            "lighting",
            "review",
            "setup",
            "tripod",
            "webcam",
            "webcams",
            "audio interface",
        ],
    },
    {
        "id": "analytics",
        "label": "Analytics Deep Dives",
        "keywords": [
            "analytics",
            "algorithm",
            "analyzed",
            "ctr",
            "retention",
            "growth",
            "data",
            "metric",
            "metrics",
            "case study",
            "impressions",
            "watch time",
        ],
    },
]

FALLBACK = ("general", "General")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further",
    "once", "here", "there", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "can",
    "will", "just", "don", "should", "now", "i", "me", "my",
    "myself", "we", "our", "ours", "you", "your", "yours", "he",
    "him", "his", "she", "her", "it", "its", "they", "them",
    "their", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "would", "could", "ought", "i'm", "you're",
}

_PUNCT_RE = re.compile(r"[^a-z0-9\s]")


def tokenize(title: str) -> tuple[list, list, list, set]:
    """Return (unigrams >=3 chars, short tokens <3 chars, phrase n-grams).

    Unigrams/short tokens come from the filtered stream (stopwords, digits,
    and short tokens handled per the rules above). Phrase n-grams (bigrams
    and trigrams) are built from the stream BEFORE stopword removal so that
    multi-word seeds containing stopwords ("how to", "behind the scenes")
    can still match. Digits are dropped from both streams.
    """
    text = _PUNCT_RE.sub(" ", title.lower())
    raw = [t for t in text.split() if t and not t.isdigit()]
    phrases = {" ".join(ng) for n in (2, 3, 4) for ng in zip(*[raw[i:] for i in range(n)])}
    filtered = [t for t in raw if t not in STOPWORDS]
    unigrams = [t for t in filtered if len(t) >= 3]
    short = [t for t in filtered if len(t) < 3]
    return unigrams, short, phrases


def score_title(title: str) -> dict:
    """Score a title against every pillar: {pillar_id: hit count}."""
    unigrams, short, phrases = tokenize(title)
    unigram_set = set(unigrams)
    short_set = set(short)
    scores = {}
    for pillar in PILLARS:
        hits = 0
        for keyword in pillar["keywords"]:
            if " " in keyword:
                if keyword in phrases:
                    hits += 1
            elif len(keyword) < 3:
                if keyword in short_set:
                    hits += 1
            elif keyword in unigram_set:
                hits += 1
        scores[pillar["id"]] = hits
    return scores


def classify_title(title: str) -> tuple[str, str]:
    """Return (pillar_id, pillar_label) for a title."""
    scores = score_title(title)
    best = max(scores.values())
    if best == 0:
        return FALLBACK
    for pillar in PILLARS:  # table order breaks ties deterministically
        if scores[pillar["id"]] == best:
            return pillar["id"], pillar["label"]
    return FALLBACK  # unreachable, kept for clarity


def assign_pillars(videos: list) -> dict:
    """Map video id -> (pillar_id, pillar_label) for a list of video dicts."""
    return {v["id"]: classify_title(v["title"]) for v in videos}


def pillar_label(pillar_id: str) -> str:
    for pillar in PILLARS:
        if pillar["id"] == pillar_id:
            return pillar["label"]
    return FALLBACK[1]


def pillar_stats(videos: list) -> list:
    """Per-pillar aggregates over enriched videos.

    Expects viewsPerDay and engagementRate on each video. Returns one dict
    per pillar present in the input, sorted by median views/day desc.
    """
    buckets: dict[str, list] = {}
    for video in videos:
        buckets.setdefault(video["pillar"], []).append(video)
    total = len(videos)
    stats = []
    for pillar_id, members in buckets.items():
        stats.append(
            {
                "id": pillar_id,
                "label": pillar_label(pillar_id),
                "count": len(members),
                "medianViewsPerDay": round(median(m["viewsPerDay"] for m in members), 1),
                "medianEngagementRate": round(
                    median(m["engagementRate"] for m in members), 4
                ),
                "shareOfCatalogPct": round(len(members) / total * 100, 1) if total else 0.0,
            }
        )
    stats.sort(key=lambda s: s["medianViewsPerDay"], reverse=True)
    return stats
