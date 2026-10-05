"""Publish cadence analysis: day-of-week / hour-of-day performance and gaps.

  - dowStats: per weekday (Mon=0..Sun=6) count + median views/day.
  - hourStats: per hour-of-day (UTC) count + median views/day.
  - bestDow: labels of the top 2 weekdays by median views/day, each with
    >= 3 videos (fewer when the catalog is thin).
  - bestHour: the hour with the highest median views/day among hours with
    >= 3 videos, else None.
  - medianGapDays: median days between consecutive uploads.
  - gapBuckets: median views/day for uploads whose preceding gap fell in
    "0-3 days" / "4-7 days" / "8+ days" (returned for analysis; the brief
    contract does not include it).
  - guidance: 2-3 sentence deterministic summary referencing the stats.
"""

from __future__ import annotations

from . import median, parse_iso8601

DOW_LABELS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

GAP_BUCKETS = [("0-3 days", 0.0, 3.0), ("4-7 days", 3.0, 7.0), ("8+ days", 7.0, float("inf"))]


def compute(videos: list) -> dict:
    """Compute cadence stats over enriched videos (needs publishedAt, viewsPerDay)."""
    by_dow: dict[int, list] = {i: [] for i in range(7)}
    by_hour: dict[int, list] = {h: [] for h in range(24)}
    for video in videos:
        dt = parse_iso8601(video["publishedAt"])
        by_dow[dt.weekday()].append(video["viewsPerDay"])
        by_hour[dt.hour].append(video["viewsPerDay"])

    dow_stats = [
        {
            "dow": i,
            "label": DOW_LABELS[i],
            "count": len(by_dow[i]),
            "medianViewsPerDay": round(median(by_dow[i]), 1),
        }
        for i in range(7)
    ]
    hour_stats = [
        {
            "hour": h,
            "count": len(by_hour[h]),
            "medianViewsPerDay": round(median(by_hour[h]), 1),
        }
        for h in range(24)
    ]

    eligible_dow = sorted(
        (d for d in dow_stats if d["count"] >= 3),
        key=lambda d: d["medianViewsPerDay"],
        reverse=True,
    )
    best_dow = [d["label"] for d in eligible_dow[:2]]

    eligible_hours = sorted(
        (h for h in hour_stats if h["count"] >= 3),
        key=lambda h: h["medianViewsPerDay"],
        reverse=True,
    )
    best_hour = eligible_hours[0]["hour"] if eligible_hours else None

    dates = sorted(parse_iso8601(v["publishedAt"]) for v in videos)
    gaps = [(dates[i] - dates[i - 1]).total_seconds() / 86400.0 for i in range(1, len(dates))]
    median_gap = round(median(gaps), 1)

    # Gap buckets: median views/day of the video that FOLLOWED each gap.
    ordered = sorted(videos, key=lambda v: parse_iso8601(v["publishedAt"]))
    gap_buckets = {}
    for label, low, high in GAP_BUCKETS:
        bucket = []
        for i in range(1, len(ordered)):
            gap = gaps[i - 1]
            in_bucket = gap <= high if low == 0.0 else low < gap <= high
            if in_bucket:
                bucket.append(ordered[i]["viewsPerDay"])
        gap_buckets[label] = round(median(bucket), 1)

    guidance = _guidance(best_dow, eligible_dow, best_hour, median_gap)
    return {
        "bestDow": best_dow,
        "bestHour": best_hour,
        "medianGapDays": median_gap,
        "guidance": guidance,
        "dowStats": dow_stats,
        "hourStats": hour_stats,
        "gapBuckets": gap_buckets,
    }


def _guidance(best_dow: list, eligible_dow: list, best_hour, median_gap: float) -> str:
    if not best_dow:
        day_part = (
            "No weekday has enough uploads (3+) to rank day-of-week performance, "
            "so publish-day effects cannot be measured yet."
        )
    else:
        ranked = ", ".join(
            f"{d['label']} ({d['medianViewsPerDay']}/day)" for d in eligible_dow[:2]
        )
        day_part = (
            f"Uploads on {ranked} earn the highest median views/day of any "
            "weekday with meaningful volume."
        )
    gap_part = (
        f"The median gap between uploads is {median_gap} days, "
        + (
            "a steady rhythm — keep it."
            if median_gap <= 14
            else "which is on the sparse side; tighter gaps tend to compound reach."
        )
    )
    if best_hour is None:
        hour_part = "No hour-of-day has 3+ uploads, so no publish hour stands out yet."
    else:
        hour_part = (
            f"Posting around {best_hour}:00 UTC lines up with the strongest "
            "hour-of-day performance."
        )
    return f"{day_part} {gap_part} {hour_part}"
