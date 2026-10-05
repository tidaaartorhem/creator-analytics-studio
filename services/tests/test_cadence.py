"""Tests for services/cadence.py."""

from services import cadence


def _video(video_id, published_at, views_per_day):
    return {
        "id": video_id,
        "title": video_id,
        "publishedAt": published_at,
        "viewsPerDay": views_per_day,
    }


def _fixture():
    # 2026-09-14/21/28 and 2026-10-05 are Mondays; 09-15/22/29 Tuesdays.
    return [
        _video("m1", "2026-09-14T10:00:00Z", 100.0),
        _video("m2", "2026-09-21T10:00:00Z", 100.0),
        _video("m3", "2026-09-28T10:00:00Z", 100.0),
        _video("t1", "2026-09-15T10:00:00Z", 200.0),
        _video("t2", "2026-09-22T10:00:00Z", 200.0),
        _video("t3", "2026-09-29T10:00:00Z", 200.0),
        _video("m4", "2026-10-05T10:00:00Z", 100.0),
    ]


def test_dow_stats_and_best_dow():
    stats = cadence.compute(_fixture())
    by_dow = {d["dow"]: d for d in stats["dowStats"]}
    assert by_dow[0]["label"] == "Monday"
    assert by_dow[0]["count"] == 4
    assert by_dow[0]["medianViewsPerDay"] == 100.0
    assert by_dow[1]["medianViewsPerDay"] == 200.0
    assert stats["bestDow"] == ["Tuesday", "Monday"]
    assert len(stats["dowStats"]) == 7
    assert len(stats["hourStats"]) == 24
    # gaps: 1, 6, 1, 6, 1, 6 -> median 3.5
    assert stats["medianGapDays"] == 3.5
    assert "Tuesday" in stats["guidance"]
    assert stats["guidance"] == cadence.compute(_fixture())["guidance"]


def test_thin_catalog_has_no_best_dow_or_hour():
    videos = [_video("a", "2026-09-14T10:00:00Z", 100.0)]
    stats = cadence.compute(videos)
    assert stats["bestDow"] == []
    assert stats["bestHour"] is None


def test_best_hour_picks_highest_median_with_volume():
    videos = [
        _video(f"h10-{i}", "2026-09-14T10:00:00Z", 300.0) for i in range(3)
    ] + [_video(f"h09-{i}", "2026-09-15T09:00:00Z", 100.0) for i in range(3)]
    stats = cadence.compute(videos)
    assert stats["bestHour"] == 10
