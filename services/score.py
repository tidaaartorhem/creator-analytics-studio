"""Deterministic channel health score (0-100), auditor-style.

Rule table — start at 100, subtract fixed penalties, clamp to [0, 100]:

  rule                 weight  warn penalty   fail penalty   condition
  pillar-focus         20      -12            -20            share of uploads in the
                                                               top-2 pillars by median
                                                               views/day < 60% (warn),
                                                               < 45% (fail)
  hit-rate             20      -12            -20            share of videos with
                                                               ratio >= 1.5 < 12% (warn),
                                                               < 6% (fail)
  trough-rate          20      -12            -20            trough share > 20% (warn),
                                                               > 30% (fail)
  cadence-consistency  15      -9             -15            median gap > 14 days (warn),
                                                               > 21 days (fail)
  engagement           15      -9             -15            median engagement rate
                                                               < 3% (warn), < 1.5% (fail)
  refresh-debt         10      -6             -10            refresh candidates >= 5%
                                                               of catalog (warn),
                                                               >= 10% (fail)

Each rule entry: {"rule", "check", "status" ("pass"|"warn"|"fail"), "detail"}.
"""

from __future__ import annotations

from . import ENGAGEMENT_FAIL, ENGAGEMENT_WARN, median
from . import pillars as pillar_mod

RULE_PILLAR_FOCUS = "pillar-focus"
RULE_HIT_RATE = "hit-rate"
RULE_TROUGH_RATE = "trough-rate"
RULE_CADENCE = "cadence-consistency"
RULE_ENGAGEMENT = "engagement"
RULE_REFRESH_DEBT = "refresh-debt"

PENALTIES = {
    RULE_PILLAR_FOCUS: (12, 20),
    RULE_HIT_RATE: (12, 20),
    RULE_TROUGH_RATE: (12, 20),
    RULE_CADENCE: (9, 15),
    RULE_ENGAGEMENT: (9, 15),
    RULE_REFRESH_DEBT: (6, 10),
}


def _entry(rule: str, check: str, status: str, detail: str) -> dict:
    return {"rule": rule, "check": check, "status": status, "detail": detail}


def score_channel(videos: list, cadence_stats: dict) -> tuple[int, list]:
    """Score the channel. videos must be enriched (outliers + decay stages).

    Returns (score 0-100, rules list in brief.json healthRules shape).
    """
    total = len(videos)
    rules: list[dict] = []
    score = 100

    def apply(rule: str, status: str) -> None:
        nonlocal score
        if status != "pass":
            warn_penalty, fail_penalty = PENALTIES[rule]
            score -= fail_penalty if status == "fail" else warn_penalty

    # --- pillar-focus -------------------------------------------------------
    stats = pillar_mod.pillar_stats(videos)
    top2 = stats[:2]
    top2_share = sum(s["count"] for s in top2) / total if total else 0.0
    top2_names = ", ".join(s["label"] for s in top2) if top2 else "none"
    if top2_share < 0.45:
        status = "fail"
    elif top2_share < 0.60:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_PILLAR_FOCUS, status)
    rules.append(
        _entry(
            RULE_PILLAR_FOCUS,
            "Top-2 pillars by median views/day hold >= 60% of uploads",
            status,
            f"top-2 pillars ({top2_names}) hold {top2_share * 100:.1f}% of uploads",
        )
    )

    # --- hit-rate -----------------------------------------------------------
    hit_share = sum(1 for v in videos if v["ratio"] >= 1.5) / total if total else 0.0
    if hit_share < 0.06:
        status = "fail"
    elif hit_share < 0.12:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_HIT_RATE, status)
    rules.append(
        _entry(
            RULE_HIT_RATE,
            "At least 12% of videos earn >= 1.5x the channel median views/day",
            status,
            f"{hit_share * 100:.1f}% of videos earn >= 1.5x the median",
        )
    )

    # --- trough-rate --------------------------------------------------------
    trough_share = (
        sum(1 for v in videos if v["ratioClass"] == "trough") / total if total else 0.0
    )
    if trough_share > 0.30:
        status = "fail"
    elif trough_share > 0.20:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_TROUGH_RATE, status)
    rules.append(
        _entry(
            RULE_TROUGH_RATE,
            "Troughs (<= 0.5x median views/day) stay under 20% of the catalog",
            status,
            f"{trough_share * 100:.1f}% of videos are troughs",
        )
    )

    # --- cadence-consistency ------------------------------------------------
    median_gap = cadence_stats.get("medianGapDays", 0.0)
    if median_gap > 21:
        status = "fail"
    elif median_gap > 14:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_CADENCE, status)
    rules.append(
        _entry(
            RULE_CADENCE,
            "Median gap between uploads is 14 days or less",
            status,
            f"median gap between uploads is {median_gap} days",
        )
    )

    # --- engagement ---------------------------------------------------------
    med_engagement = median(v["engagementRate"] for v in videos)
    if med_engagement < ENGAGEMENT_FAIL:
        status = "fail"
    elif med_engagement < ENGAGEMENT_WARN:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_ENGAGEMENT, status)
    rules.append(
        _entry(
            RULE_ENGAGEMENT,
            "Median engagement rate (likes+comments)/views is at least 3%",
            status,
            f"median engagement rate is {med_engagement * 100:.2f}%",
        )
    )

    # --- refresh-debt -------------------------------------------------------
    refresh_share = (
        sum(1 for v in videos if v["refreshCandidate"]) / total if total else 0.0
    )
    if refresh_share >= 0.10:
        status = "fail"
    elif refresh_share >= 0.05:
        status = "warn"
    else:
        status = "pass"
    apply(RULE_REFRESH_DEBT, status)
    rules.append(
        _entry(
            RULE_REFRESH_DEBT,
            "Refresh candidates (decayed evergreens) stay under 5% of the catalog",
            status,
            f"{refresh_share * 100:.1f}% of videos are refresh candidates",
        )
    )

    return max(0, min(100, score)), rules
