"""Tests for services/outliers.py."""

from datetime import datetime, timezone

from services import outliers

NOW = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
PUBLISHED = "2026-09-25T00:00:00Z"  # 10 days before NOW


def _video(video_id, views, likes=10, comments=2):
    return {
        "id": video_id,
        "title": f"Video {video_id}",
        "publishedAt": PUBLISHED,
        "durationS": 600,
        "views": views,
        "likes": likes,
        "comments": comments,
    }


def _enriched():
    # age 10 days -> views/day 10, 20, 40; median 20
    videos = [_video("a", 100), _video("b", 200), _video("c", 400)]
    return {v["id"]: v for v in outliers.enrich(videos, NOW)}


def test_ratio_math():
    enriched = _enriched()
    assert enriched["a"]["viewsPerDay"] == 10.0
    assert enriched["b"]["ratio"] == 1.0
    assert enriched["c"]["ratio"] == 2.0
    assert enriched["a"]["engagementRate"] == round(12 / 100, 4)
    assert enriched["a"]["ageDays"] == 10.0


def test_classification_boundaries():
    enriched = _enriched()
    assert enriched["c"]["ratioClass"] == "hit"  # exactly 2.0
    assert enriched["a"]["ratioClass"] == "trough"  # exactly 0.5
    assert enriched["b"]["ratioClass"] == "normal"  # exactly 1.0


def test_zero_views_ratio_zero():
    videos = [_video("a", 0, likes=0, comments=0), _video("b", 200)]
    enriched = {v["id"]: v for v in outliers.enrich(videos, NOW)}
    assert enriched["a"]["ratio"] == 0.0
    assert enriched["a"]["engagementRate"] == 0.0
    assert enriched["a"]["ratioClass"] == "trough"


def test_enrich_does_not_mutate_input():
    videos = [_video("a", 100)]
    outliers.enrich(videos, NOW)
    assert "ratio" not in videos[0]
