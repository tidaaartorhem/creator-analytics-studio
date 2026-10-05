"""creator-analytics-studio services package.

Shared constants and small helpers. Pure functions only — importing this
module never exits, never touches the network, and never reads secrets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Classification thresholds -------------------------------------------------
HIT_RATIO = 2.0  # views/day >= 2x channel median -> "hit"
TROUGH_RATIO = 0.5  # views/day <= 0.5x channel median -> "trough"

# --- Engagement benchmarks (fraction of views) ----------------------------------
ENGAGEMENT_WARN = 0.03  # median engagement below this -> warn
ENGAGEMENT_FAIL = 0.015  # median engagement below this -> fail

# --- Decay / refresh ------------------------------------------------------------
DECAY_YOUNG_DAYS = 45  # videos younger than this never count as decayed
REFRESH_DECAY_MIN = 0.75  # decayScore at/above this qualifies for refresh
REFRESH_VIEWS_MULT = 2.0  # ... and lifetime views >= this x channel median views

# --- YouTube client ---------------------------------------------------------------
API_TIMEOUT_S = 20  # seconds per HTTP call


def median(values) -> float:
    """Median of a numeric iterable. Returns 0.0 for empty input."""
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return float(vals[mid])
    return (vals[mid - 1] + vals[mid]) / 2.0


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware datetime.

    Accepts the trailing "Z" form the YouTube API emits as well as numeric
    offsets. Raises ValueError on anything unparseable.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def utcnow() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    """Format an aware datetime as ISO-8601 with a trailing Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compact(number) -> str:
    """Compact a large number for human copy: 1_240_000 -> "1.2M"."""
    n = float(number)
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(n) >= threshold:
            text = f"{n / threshold:.1f}".rstrip("0").rstrip(".")
            return f"{text}{suffix}"
    return str(int(n))
