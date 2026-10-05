"""Age-normalized performance: views/day vs the channel median.

Definitions:
  age_days       = max(1, (now - published_at).days)
  views_per_day  = views / age_days
  channel median = median(views_per_day) over the catalog
  ratio          = views_per_day / channel_median (0 when the video has no
                   views, or when the channel median is 0)
  hit            = ratio >= 2.0
  trough         = ratio <= 0.5
  normal         = otherwise

`enrich` returns NEW dicts (input untouched) carrying the contract fields
plus pillar assignment. `now` is injectable for deterministic tests.
"""

from __future__ import annotations

from . import HIT_RATIO, TROUGH_RATIO, median, parse_iso8601
from . import pillars as pillar_mod


def classify_ratio(ratio: float) -> str:
    if ratio >= HIT_RATIO:
        return "hit"
    if ratio <= TROUGH_RATIO:
        return "trough"
    return "normal"


def enrich(videos: list, now) -> list:
    """Attach ageDays, viewsPerDay, engagementRate, ratio, ratioClass, pillar."""
    assignment = pillar_mod.assign_pillars(videos)
    enriched = []
    for video in videos:
        published = parse_iso8601(video["publishedAt"])
        age_days = max(1, (now - published).days)
        views = video["views"]
        likes = video["likes"]
        comments = video["comments"]
        views_per_day = views / age_days
        engagement = (likes + comments) / views if views else 0.0
        pillar_id, pillar_label = assignment[video["id"]]
        enriched.append(
            {
                **video,
                "pillar": pillar_id,
                "pillarLabel": pillar_label,
                "ageDays": round(float(age_days), 1),
                "viewsPerDay": round(views_per_day, 1),
                "engagementRate": round(engagement, 4),
            }
        )
    channel_median = median(v["viewsPerDay"] for v in enriched)
    for video in enriched:
        if video["views"] and channel_median:
            ratio = round(video["viewsPerDay"] / channel_median, 2)
        else:
            ratio = 0.0
        video["ratio"] = ratio
        video["ratioClass"] = classify_ratio(ratio)
    return enriched
