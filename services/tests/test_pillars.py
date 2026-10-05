"""Tests for services/pillars.py."""

from services import pillars


def test_contract_title_examples():
    assert pillars.classify_title("How to Edit Faster in Premiere Pro") == (
        "tutorials",
        "Tutorials",
    )
    assert pillars.classify_title("I Tested 7 AI Thumbnail Tools") == (
        "ai_tools",
        "AI Tools",
    )
    assert pillars.classify_title("Quantum Banana Economics") == ("general", "General")


def test_vlog_phrase_with_stopwords():
    # "day in the life" contains stopwords; phrase matching must survive that.
    assert pillars.classify_title("A Day in the Life of a Full-Time Creator") == (
        "vlogs",
        "Vlogs",
    )
    assert pillars.classify_title("Sony ZV-E10 Review: 2 Years Later") == (
        "gear",
        "Gear Reviews",
    )


def test_assign_pillars_maps_ids():
    videos = [
        {"id": "a", "title": "How to Edit Faster in Premiere Pro"},
        {"id": "b", "title": "Quantum Banana Economics"},
    ]
    assert pillars.assign_pillars(videos) == {
        "a": ("tutorials", "Tutorials"),
        "b": ("general", "General"),
    }


def test_pillar_stats_medians():
    videos = [
        {"pillar": "tutorials", "viewsPerDay": 100.0, "engagementRate": 0.05},
        {"pillar": "tutorials", "viewsPerDay": 300.0, "engagementRate": 0.03},
        {"pillar": "vlogs", "viewsPerDay": 10.0, "engagementRate": 0.02},
    ]
    stats = pillars.pillar_stats(videos)
    by_id = {s["id"]: s for s in stats}
    assert by_id["tutorials"]["count"] == 2
    assert by_id["tutorials"]["medianViewsPerDay"] == 200.0
    assert by_id["tutorials"]["medianEngagementRate"] == 0.04
    assert by_id["tutorials"]["shareOfCatalogPct"] == round(2 / 3 * 100, 1)
    assert stats[0]["id"] == "tutorials"  # sorted by median views/day desc
