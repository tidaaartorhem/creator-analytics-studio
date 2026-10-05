"""Tests for services/score.py."""

from services import score


def _video(
    ratio=1.0,
    ratio_class="normal",
    engagement=0.05,
    pillar="tutorials",
    refresh=False,
    views_per_day=100.0,
):
    return {
        "id": "v",
        "title": "t",
        "ratio": ratio,
        "ratioClass": ratio_class,
        "engagementRate": engagement,
        "pillar": pillar,
        "pillarLabel": pillar.title(),
        "refreshCandidate": refresh,
        "viewsPerDay": views_per_day,
        "views": 10_000,
    }


def _numbered(videos):
    for i, v in enumerate(videos):
        v["id"] = f"v{i}"
    return videos


def test_all_pass_scores_100():
    videos = _numbered([_video(ratio=2.0) for _ in range(4)] + [_video() for _ in range(16)])
    final, rules = score.score_channel(videos, {"medianGapDays": 7.0})
    assert final == 100
    assert all(r["status"] == "pass" for r in rules)
    assert [r["rule"] for r in rules] == [
        "pillar-focus",
        "hit-rate",
        "trough-rate",
        "cadence-consistency",
        "engagement",
        "refresh-debt",
    ]
    for rule in rules:
        assert set(rule.keys()) == {"rule", "check", "status", "detail"}


def test_trough_fail_and_hit_warn_penalties():
    videos = _numbered(
        [_video(ratio=2.0) for _ in range(2)]  # 10% at >= 1.5x -> warn (-12)
        + [_video(ratio=0.2, ratio_class="trough") for _ in range(8)]  # 40% -> fail (-20)
        + [_video() for _ in range(10)]
    )
    final, rules = score.score_channel(videos, {"medianGapDays": 7.0})
    by_rule = {r["rule"]: r for r in rules}
    assert by_rule["trough-rate"]["status"] == "fail"
    assert by_rule["hit-rate"]["status"] == "warn"
    assert final == 68  # 100 - 20 - 12
    assert "40.0% of videos are troughs" in by_rule["trough-rate"]["detail"]


def test_everything_failing_floors_at_zero():
    pillars = ["tutorials", "ai_tools", "gear", "analytics", "vlogs"]
    videos = _numbered(
        [
            _video(
                ratio=0.2 if i < 8 else 1.0,  # 40% troughs, 0% hits
                ratio_class="trough" if i < 8 else "normal",
                engagement=0.01,
                pillar=pillars[i % 5],  # top-2 hold 40% of uploads
                refresh=i < 3,  # 15% refresh candidates
            )
            for i in range(20)
        ]
    )
    final, rules = score.score_channel(videos, {"medianGapDays": 30.0})
    assert final == 0
    assert all(r["status"] == "fail" for r in rules)
