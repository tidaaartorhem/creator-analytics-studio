"""Tests for services/decay.py."""

from services import decay


def _video(views, age_days, velocity):
    return {
        "id": "v",
        "title": "t",
        "views": views,
        "ageDays": float(age_days),
        "velocity": velocity,
    }


def test_decayed_evergreen():
    videos = [
        _video(1_000_000, 600, 50.0),
        _video(10_000, 600, 16.0),
        _video(12_000, 600, 20.0),
    ]
    enriched = decay.enrich(videos)
    assert enriched[0]["decayScore"] > 0.9
    assert enriched[0]["refreshCandidate"] is True
    assert enriched[0]["peakVelocity30"] > enriched[0]["trailingVelocity30"]
    assert decay.fit_lambda(1_000_000, 600, 50.0) > 0
    assert decay.fit_lambda(12_000, 600, 20.0) == 0.0  # not decaying


def test_young_video_never_decayed():
    videos = [_video(50_000, 20, 2000.0), _video(8_000, 20, 300.0)]
    enriched = decay.enrich(videos)
    assert enriched[0]["decayScore"] == 0.0
    assert enriched[0]["refreshCandidate"] is False


def test_zero_velocity_is_fully_decayed():
    videos = [_video(500_000, 600, 0.0), _video(10_000, 600, 16.0)]
    enriched = decay.enrich(videos)
    assert enriched[0]["decayScore"] == 1.0


def test_refresh_requires_two_x_median_views():
    small = [_video(5_000, 600, 5.0), _video(6_000, 600, 6.0), _video(7_000, 600, 7.0)]
    # median lifetime views = 6000 -> refresh threshold 12000
    videos = small + [_video(100_000, 600, 8.0), _video(11_000, 600, 11_000 / 600)]
    enriched = {v["views"]: v for v in decay.enrich(videos)}
    assert enriched[100_000]["decayScore"] >= 0.75
    assert enriched[100_000]["refreshCandidate"] is True
    assert enriched[11_000]["refreshCandidate"] is False  # below 2x median
