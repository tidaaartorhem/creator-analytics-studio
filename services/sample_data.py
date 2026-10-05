"""Fixture generator for the sample channel ("Frame & Focus").

Deterministic: random.Random(42); no runtime randomness. Run once:

    python3 services/sample_data.py

to (re)generate data/sample-channel.json. The build pipeline does NOT use
this module — the committed JSON is the fixture, this file is documentation
of how it was made.

Narrative baked into the fixture:
  - AI Tools is the breakout pillar (3 hits: 1.5M / 1.9M / 2.4M views).
  - 2 decayed evergreens (1M+ lifetime views, trailing velocity ~2% of the
    modeled peak) -> refresh candidates.
  - Recent flops (troughs) and steady recent winners (hits).
  - Everything else: steady, mediocre, or vlog-trough filler.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
# Fixed "now" so the fixture's velocity estimates line up with ageDays at
# build time (builds run within days of generation; ratios barely move).
NOW = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

NOTE = (
    "SAMPLE DATA — fictional channel bundled so the studio runs without an API key; "
    "bring your own API key + channel id for real data."
)

CHANNEL = {
    "id": "UCsampl3ch4nn3l0000",
    "title": "Frame & Focus",
    "description": (
        "Frame & Focus is a fictional creator channel about video editing, "
        "AI tools for creators, camera gear, and YouTube analytics. Every "
        "video, view count, and velocity in this fixture is invented."
    ),
    "subscriberCount": 148500,
    "videoCount": 76,
    "viewCount": 9210000,
    "publishedAt": "2019-06-11T00:00:00Z",
}

# Filler title banks (narrative titles are assigned explicitly below).
TITLES = {
    "tutorials": [
        "How to Edit Faster in Premiere Pro: 12 Workflow Tips",
        "The Complete Beginner's Guide to Video Editing",
        "Step-by-Step: My Full Editing Workflow From Raw to Upload",
        "How to Cut Talking-Head Videos Without Jump Cuts",
        "Premiere Pro Keyboard Shortcuts That Save Me Hours",
        "How to Sync Audio and Video Perfectly Every Time",
        "Beginner Tutorial: Your First Edit in DaVinci Resolve",
        "How to Add Subtitles That Actually Get Watched",
        "The 5-Second Rule: How I Pace Every Edit",
        "How to Edit B-Roll That Doesn't Feel Like Filler",
        "Tutorial: Multi-Cam Editing in Under 10 Minutes",
        "How to Master the Timeline: Nesting, Markers, and Bins",
        "Color Grading Tutorial: From Flat LOG to Cinematic",
        "How to Edit a YouTube Video in 90 Minutes",
        "The Ultimate Guide to Sound Design for Creators",
        "How to Fix Bad Audio in Post (3 Methods)",
        "Tutorial: Speed Ramping Without the Jerkiness",
        "How to Structure a Tutorial People Finish",
        "Editing Guide: Hooks, Payoffs, and Retention Edits",
        "How I Batch-Edit a Week of Content in One Day",
        "Premiere Pro vs DaVinci Resolve: Editing Workflow Compared",
        "How to Remove Background Noise: A Practical Guide",
        "Tutorial: Animated Captions in Premiere Pro",
        "How to Edit Vertical Video That Holds Attention",
        "The Beginner's Guide to Keyframes and Motion",
        "How I Learned Editing in 30 Days (Full Plan)",
        "Advanced Tutorial: Masking and Tracking Shots",
        "How to Use Adjustment Layers Like a Pro",
    ],
    "ai_tools": [
        "Midjourney for Thumbnails: A Creator's Guide",
        "I Let AI Edit My Video: The Honest Result",
        "5 AI Tools That Save Me 10 Hours a Week",
        "AI Script to Video: Testing 4 Generators",
        "ChatGPT vs Claude for Content Ideas",
        "The AI Upscaler Test: Can It Save Old Footage?",
        "AI Music for Creators: What Actually Sounds Good",
        "I Asked AI to Plan My Content Calendar",
        "Auto-Captions Compared: 6 AI Tools Tested",
        "AI B-Roll Generators: Worth It Yet?",
        "The Truth About AI Faceless Channels",
        "AI Thumbnails vs Human-Made: CTR Test",
        "My AI Research Workflow for Deep-Dive Videos",
        "Testing AI Dubbing for a Second Channel",
        "AI Clip Tools: Turning Long Videos Into Shorts",
        "I Built Thumbnails With 3 AI Image Tools",
    ],
    "gear": [
        "Sony ZV-E10 Review: 2 Years Later",
        "The Best Budget Mic for Creators in 2025",
        "I Switched to This Camera Setup (Full Tour)",
        "Lighting Review: One Light vs Three Lights",
        "Budget Lens Showdown: 35mm vs 50mm",
        "My Entire Desk Setup Tour 2025",
        "Microphone Review: Dynamic vs Condenser for Voice",
        "Is This $200 Tripod Worth It? Honest Review",
        "Camera Settings I Use for Every Shoot",
        "The Cheapest Pro-Looking Lighting Setup",
        "I Tested 5 Webcams for Streaming",
        "Lens Review: The Only 3 Lenses Creators Need",
        "My Travel Filming Setup: Camera, Mic, and Bag",
        "Audio Interface Review: What Beginners Should Buy",
    ],
    "analytics": [
        "I Analyzed 100 Thumbnails: Here's What Wins CTR",
        "Retention Graphs Explained: Reading Your Analytics",
        "Case Study: How One Video 10x'd My Channel Growth",
        "The Data Behind My Best Month Ever",
        "Why Your CTR Is Low: An Analytics Deep Dive",
        "Audience Retention: The 30-Second Rule (Data)",
        "I Tracked Every Metric for 90 Days: Results",
        "Impressions vs Clicks: What the Algorithm Rewards",
        "Growth Case Study: 0 to 100K With Data",
        "Watch Time Sources: Where Views Actually Come From",
    ],
    "vlogs": [
        "A Day in the Life of a Full-Time Creator",
        "Behind the Scenes: Filming My Biggest Video Yet",
        "My Story: Quitting My Job for YouTube",
        "Vlog: Studio Build Day (It Got Messy)",
        "Day in the Life: Shoot Day vs Edit Day",
        "Behind the Scenes of a Brand Deal Shoot",
        "Vlog: I Attended My First Creator Conference",
        "A Realistic Day in My Life as a Creator",
    ],
}

# Narrative videos: (title, views). Assigned to pillar members by date order.
AI_HITS = [
    ("I Tested 7 AI Thumbnail Tools (One Broke My Brain)", 2_400_000),
    ("ChatGPT for Video Scripts: My Exact Workflow", 1_900_000),
    ("AI Voiceovers Tested: 5 Tools Ranked for Creators", 1_500_000),
]
EVERGREENS = [
    ("tutorials", "How to Color Grade Cinematic Footage in Premiere Pro", 1_050_000),
    ("analytics", "How the YouTube Algorithm Actually Works (2024)", 1_180_000),
]

# Base view ranges for filler videos: (low, high).
BASE_VIEWS = {
    "tutorials": (6_000, 26_000),
    "ai_tools": (4_000, 28_000),
    "gear": (4_000, 14_000),
    "analytics": (12_000, 42_000),
    "vlogs": (2_000, 11_000),
}
# Duration ranges in seconds per pillar.
DURATIONS = {
    "tutorials": (600, 1200),
    "ai_tools": (480, 900),
    "gear": (600, 1100),
    "analytics": (700, 1400),
    "vlogs": (500, 1000),
}
PILLAR_COUNTS = {
    "tutorials": 28,
    "ai_tools": 16,
    "gear": 14,
    "analytics": 10,
    "vlogs": 8,
}
DATE_START = datetime(2024, 3, 10, tzinfo=timezone.utc)
DATE_END = datetime(2026, 9, 20, tzinfo=timezone.utc)


def _engagement(views: int, rng: random.Random) -> tuple[int, int]:
    """likes ~= 3-6% of views, comments ~= 0.5-1.5% of views."""
    likes = int(views * rng.uniform(0.03, 0.06))
    comments = int(views * rng.uniform(0.005, 0.015))
    return likes, comments


def _iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate() -> dict:
    rng = random.Random(SEED)

    # Pillar order, shuffled deterministically.
    pillars: list[str] = []
    for pillar, count in PILLAR_COUNTS.items():
        pillars.extend([pillar] * count)
    rng.shuffle(pillars)
    assert len(pillars) == 76

    # Publish dates: linear spread with +/-5 day jitter, strictly increasing.
    span_days = (DATE_END - DATE_START).days
    dates: list[datetime] = []
    prev = None
    for i in range(len(pillars)):
        day = i * span_days / (len(pillars) - 1) + rng.uniform(-5, 5)
        day = max(0, min(span_days, day))
        dt = DATE_START + timedelta(days=day)
        dt = dt.replace(hour=rng.randint(8, 20), minute=rng.randint(0, 59), second=0)
        if prev is not None and dt <= prev:
            dt = prev + timedelta(hours=1)
        dates.append(dt)
        prev = dt

    title_queues = {p: list(ts) for p, ts in TITLES.items()}
    videos: list[dict] = []
    for pillar, published in zip(pillars, dates):
        title = title_queues[pillar].pop(0)
        low, high = BASE_VIEWS[pillar]
        views = rng.randint(low, high)
        dlow, dhigh = DURATIONS[pillar]
        likes, comments = _engagement(views, rng)
        age_days = max(1, (NOW - published).days)
        videos.append(
            {
                "pillar_hint": pillar,
                "title": title,
                "publishedAt": _iso_z(published),
                "durationS": rng.randint(dlow, dhigh),
                "views": views,
                "likes": likes,
                "comments": comments,
                # Steady-state estimate: lifetime average views/day, jittered.
                "velocity": round(views / age_days * rng.uniform(0.7, 1.3), 1),
                "_published": published,
            }
        )

    def members(pillar: str) -> list[dict]:
        return sorted(
            [v for v in videos if v["pillar_hint"] == pillar],
            key=lambda v: v["_published"],
        )

    def retitle(video: dict, title: str, views: int, velocity: float) -> None:
        video["title"] = title
        video["views"] = views
        video["likes"], video["comments"] = _engagement(views, rng)
        video["velocity"] = round(velocity, 1)

    # --- Narrative overrides -------------------------------------------------
    # 1. AI breakout hits: spread across the timeline, still earning strongly.
    ai = members("ai_tools")
    for video, (title, views) in zip([ai[2], ai[6], ai[10]], AI_HITS):
        age = max(1, (NOW - video["_published"]).days)
        retitle(video, title, views, views / age * 0.65)

    # 2. Decayed evergreens: 1M+ lifetime views, trailing velocity ~2% of the
    #    modeled peak (V/12000 lands decayScore ~0.98 in the decay model).
    for pillar, title, views in EVERGREENS:
        video = members(pillar)[0] if pillar == "tutorials" else members(pillar)[1]
        retitle(video, title, views, views / 12000)

    # 3. Recent flops: newest vlogs + newest gear review, barely any views.
    for video in members("vlogs")[-3:]:
        views = rng.randint(1200, 3000)
        age = max(1, (NOW - video["_published"]).days)
        retitle(video, video["title"], views, views / age)
    gear_flop = members("gear")[-1]
    age = max(1, (NOW - gear_flop["_published"]).days)
    retitle(gear_flop, gear_flop["title"], 2500, 2500 / age)

    # 4. Steady recent winners: newest tutorials outperforming the catalog.
    for video, views in zip(members("tutorials")[-2:], [45_000, 60_000]):
        age = max(1, (NOW - video["_published"]).days)
        retitle(video, video["title"], views, views / age * 1.1)

    # --- Finalize ------------------------------------------------------------
    videos.sort(key=lambda v: v["_published"])
    total_views = sum(v["views"] for v in videos)
    print(f"[sample-data] videos={len(videos)} total_views={total_views:,}", file=sys.stderr)
    if total_views > CHANNEL["viewCount"]:
        print(
            "[sample-data] WARNING: catalog views exceed channel viewCount",
            file=sys.stderr,
        )

    out_videos = []
    for i, video in enumerate(videos, start=1):
        out_videos.append(
            {
                "id": f"vid{i:03d}",
                "title": video["title"],
                "publishedAt": video["publishedAt"],
                "durationS": video["durationS"],
                "views": video["views"],
                "likes": video["likes"],
                "comments": video["comments"],
                "velocity": video["velocity"],
            }
        )
    return {"_note": NOTE, "channel": CHANNEL, "videos": out_videos}


def main() -> int:
    doc = generate()
    out_path = ROOT / "data" / "sample-channel.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"[sample-data] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
