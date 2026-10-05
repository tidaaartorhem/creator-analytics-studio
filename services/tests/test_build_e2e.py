"""End-to-end build test. No network: build reads the committed sample fixture."""

import json

from services import main as main_mod

VIDEO_FIELDS = {
    "id",
    "title",
    "publishedAt",
    "durationS",
    "views",
    "likes",
    "comments",
    "ageDays",
    "viewsPerDay",
    "engagementRate",
    "ratio",
    "ratioClass",
    "pillar",
    "pillarLabel",
    "peakVelocity30",
    "trailingVelocity30",
    "decayScore",
    "refreshCandidate",
}


def _build(tmp_path):
    out_dir = tmp_path / "public"
    summary = main_mod.run_build(out_dir=out_dir)
    docs = {
        name: json.loads((out_dir / f"{name}.json").read_text())
        for name in ("channel", "videos", "brief")
    }
    return docs, summary


def test_build_writes_three_files(tmp_path):
    (tmp_path / "public").mkdir()
    docs, summary = _build(tmp_path)
    assert summary["videos"] == 76
    assert set(docs.keys()) == {"channel", "videos", "brief"}


def test_channel_and_videos_contract(tmp_path):
    docs, _ = _build(tmp_path)
    channel = docs["channel"]["channel"]
    assert set(docs["channel"].keys()) == {"channel", "computedAt"}
    assert channel["id"] == "UCsampl3ch4nn3l0000"
    assert channel["source"] == "sample"
    assert channel["subscriberCount"] == 148500
    assert channel["videoCount"] == 76
    assert channel["viewCount"] == 9210000
    assert channel["publishedAt"] == "2019-06-11T00:00:00Z"
    assert channel["fetchedAt"].endswith("Z")
    assert isinstance(docs["videos"], list) and len(docs["videos"]) == 76
    for video in docs["videos"]:
        assert set(video.keys()) == VIDEO_FIELDS, video["id"]
        assert video["ratioClass"] in ("hit", "trough", "normal")
        assert isinstance(video["refreshCandidate"], bool)
        assert 0.0 <= video["decayScore"] <= 1.0


def test_brief_contract(tmp_path):
    docs, summary = _build(tmp_path)
    brief = docs["brief"]
    assert set(brief.keys()) == {
        "computedAt",
        "healthScore",
        "healthRules",
        "pillars",
        "doubleDown",
        "refresh",
        "cadence",
        "checklist",
        "topHit",
        "worstTrough",
        "headlineStats",
    }
    assert isinstance(brief["healthScore"], int)
    assert brief["healthScore"] == summary["score"]
    assert brief["checklist"], "checklist must be non-empty"
    assert {c["kind"] for c in brief["checklist"]} <= {
        "double-down",
        "refresh",
        "cadence",
        "score",
    }
    assert set(brief["cadence"].keys()) == {
        "bestDow",
        "bestHour",
        "medianGapDays",
        "guidance",
        "dowStats",
        "hourStats",
    }
    assert len(brief["cadence"]["bestDow"]) <= 3
    assert len(brief["cadence"]["dowStats"]) == 7
    assert len(brief["cadence"]["hourStats"]) == 24
    videos = docs["videos"]
    headline = brief["headlineStats"]
    assert headline["videoCount"] == len(videos) == 76
    assert headline["totalViews"] == sum(v["views"] for v in videos)
    assert headline["hitCount"] == sum(1 for v in videos if v["ratioClass"] == "hit")
    assert headline["troughCount"] == sum(1 for v in videos if v["ratioClass"] == "trough")
    assert headline["refreshCount"] == len(brief["refresh"])
    assert brief["topHit"]["ratio"] == max(v["ratio"] for v in videos)
    assert brief["worstTrough"]["ratio"] == min(v["ratio"] for v in videos)


def test_sample_narrative_survives_pipeline(tmp_path):
    docs, _ = _build(tmp_path)
    by_title = {v["title"]: v for v in docs["videos"]}
    evergreen = by_title["How the YouTube Algorithm Actually Works (2024)"]
    assert evergreen["refreshCandidate"] is True
    assert evergreen["decayScore"] >= 0.9
    assert "AI Voiceovers Tested" in docs["brief"]["topHit"]["title"]
    assert docs["brief"]["doubleDown"][0]["pillar"] == "AI Tools"
