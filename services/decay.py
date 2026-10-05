"""View-velocity decay via an exponential-fit model.

Model: v(t) = v0 * e^(-lambda * t), where v(t) is views/day t days after
publish. We observe lifetime views V, age T days, and the trailing-30d
velocity v(T). Total views equal the integral of v(t) over [0, T]:

    V = v(T) * (e^(lambda*T) - 1) / lambda

so lambda solves (e^(lambda*T) - 1) / lambda = V / v(T), found by bisection
(the left side is monotone increasing in lambda, and tends to T as
lambda -> 0, so a root exists exactly when lifetime-average velocity
exceeds current velocity — i.e. the video is actually decaying).

Derived quantities:
  peakVelocity30   = v0 * (1 - e^(-30*lambda)) / (30*lambda), the modeled
                     average views/day over the best 30-day window.
  decayScore       = clamp(1 - v(T) / v0, 0, 1); 1 = fully collapsed.
  refreshCandidate = decayScore >= 0.75 AND lifetime views >= 2x the channel
                     median lifetime views.

Special cases:
  - Videos younger than DECAY_YOUNG_DAYS: decayScore 0 (too young to decay);
    peak falls back to max(trailing, views / min(age, 30)).
  - Trailing velocity <= 0 with views > 0: fully decayed -> decayScore 1.0;
    peak falls back to views / min(age, 30) as a crude proxy.
  - Videos not actually decaying (lifetime average <= trailing): lambda = 0,
    decayScore 0, peak = trailing velocity.
"""

from __future__ import annotations

import math

from . import (
    DECAY_YOUNG_DAYS,
    REFRESH_DECAY_MIN,
    REFRESH_VIEWS_MULT,
    median,
)


def fit_lambda(lifetime_views: float, age_days: float, velocity: float) -> float:
    """Solve (e^(l*T) - 1)/l = V/v for l by bisection. Returns 0 when the
    video is not decaying (lifetime average velocity <= current velocity)."""
    target = lifetime_views / velocity
    if age_days >= target:
        return 0.0

    def f(lam: float) -> float:
        x = lam * age_days
        if x > 700:  # e^x would overflow; f is already hugely positive
            return float("inf")
        return (math.exp(x) - 1.0) / lam - target

    lo, hi = 1e-12, 1.0
    while f(hi) < 0:
        hi *= 2.0
        if hi > 1e12:  # degenerate input; treat as not decaying
            return 0.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def peak_velocity_30(v0: float, lam: float) -> float:
    """Modeled average views/day over the best 30-day window."""
    if lam <= 0:
        return v0
    return v0 * (1.0 - math.exp(-30.0 * lam)) / (30.0 * lam)


def enrich(videos: list) -> list:
    """Attach peakVelocity30, trailingVelocity30, decayScore, refreshCandidate.

    Expects views, ageDays, and velocity (estimated trailing-30d views/day)
    on each video. Returns NEW dicts.
    """
    median_lifetime = median(v["views"] for v in videos)
    threshold = REFRESH_VIEWS_MULT * median_lifetime
    enriched = []
    for video in videos:
        views = float(video["views"])
        age = float(video["ageDays"])
        velocity = float(video.get("velocity", 0) or 0)
        trailing = round(velocity, 1)

        if age < DECAY_YOUNG_DAYS:
            peak = max(velocity, views / min(age, 30.0)) if age else velocity
            decay_score = 0.0
        elif velocity <= 0 and views > 0:
            peak = views / min(age, 30.0)
            decay_score = 1.0
        else:
            lam = fit_lambda(views, age, velocity)
            if lam <= 0:
                peak = velocity
                decay_score = 0.0
            else:
                v0 = velocity * math.exp(lam * age)
                peak = peak_velocity_30(v0, lam)
                decay_score = min(1.0, max(0.0, 1.0 - velocity / v0))

        refresh = decay_score >= REFRESH_DECAY_MIN and views >= threshold
        enriched.append(
            {
                **video,
                "peakVelocity30": round(peak, 1),
                "trailingVelocity30": trailing,
                "decayScore": round(decay_score, 3),
                "refreshCandidate": bool(refresh),
            }
        )
    return enriched
