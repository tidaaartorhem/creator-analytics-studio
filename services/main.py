"""creator-analytics-studio build/fetch CLI.

  python3 services/main.py build
      Loads data/sample-channel.json -> pillars -> outliers -> decay ->
      cadence -> score -> writes web/public/{channel,videos,brief}.json
      with source "sample".

  python3 services/main.py fetch --api-key KEY --channel-id UC... [--max-videos N]
      Pulls real data through the quota-cheap YouTube client (fetchedAt=now,
      source "youtube") and runs the same pipeline. The API has no
      trailing-30d velocity endpoint, so decay falls back to the lifetime
      average views/day as a velocity proxy — decayScores skew low for older
      videos. Documented limitation, not a silent one.

Exits non-zero on ANY failure. The API key is never printed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Allow `python3 services/main.py build` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import ROOT, compact, iso_z, median, utcnow
from services import cadence as cadence_mod
from services import decay as decay_mod
from services import outliers as outliers_mod
from services import pillars as pillars_mod
from services import score as score_mod
from services import youtube_client

CHANNEL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,}$")

# Exact videos.json field list — the frontend depends on it.
VIDEO_FIELDS = [
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
]


def _build_brief(videos: list, cadence_stats: dict, health: tuple) -> dict:
    health_score, health_rules = health
    pillar_stats = pillars_mod.pillar_stats(videos)

    double_down = []
    for stat in [s for s in pillar_stats if s["count"] >= 3][:2]:
        double_down.append(
            {
                "pillar": stat["label"],
                "medianViewsPerDay": stat["medianViewsPerDay"],
                "engagement": stat["medianEngagementRate"],
                "count": stat["count"],
                "why": (
                    f"{stat['label']} leads the channel at "
                    f"{stat['medianViewsPerDay']}/day median views with "
                    f"{stat['medianEngagementRate'] * 100:.1f}% median engagement "
                    f"across {stat['count']} videos — publish more of what "
                    "works here."
                ),
            }
        )

    refresh = []
    for video in sorted(videos, key=lambda v: v["decayScore"], reverse=True):
        if not video["refreshCandidate"]:
            continue
        peak = video["peakVelocity30"]
        pct = round(video["trailingVelocity30"] / peak * 100) if peak else 0
        refresh.append(
            {
                "videoId": video["id"],
                "title": video["title"],
                "decayScore": video["decayScore"],
                "lifetimeViews": video["views"],
                "why": (
                    f"{compact(video['views'])} lifetime views but trailing "
                    f"velocity is {pct}% of its modeled peak — refresh the "
                    "title and thumbnail, then run YouTube's Test & Compare "
                    "on the thumbnail"
                ),
            }
        )

    cadence_out = {
        "bestDow": cadence_stats["bestDow"],
        "bestHour": cadence_stats["bestHour"],
        "medianGapDays": cadence_stats["medianGapDays"],
        "guidance": cadence_stats["guidance"],
        "dowStats": cadence_stats["dowStats"],
        "hourStats": cadence_stats["hourStats"],
    }

    checklist = []
    for entry in double_down:
        checklist.append(
            {
                "title": f"Double down on {entry['pillar']}",
                "detail": entry["why"],
                "kind": "double-down",
            }
        )
    for entry in refresh:
        checklist.append(
            {
                "title": f"Refresh '{entry['title']}'",
                "detail": entry["why"],
                "kind": "refresh",
            }
        )
    best_dow = cadence_stats["bestDow"]
    checklist.append(
        {
            "title": (
                f"Publish on {', '.join(best_dow)}"
                if best_dow
                else "Establish a steadier publish rhythm"
            ),
            "detail": cadence_stats["guidance"],
            "kind": "cadence",
        }
    )
    for rule in health_rules:
        if rule["status"] != "pass":
            checklist.append(
                {
                    "title": f"Address: {rule['rule']} ({rule['status']})",
                    "detail": f"{rule['check']}. {rule['detail']}.",
                    "kind": "score",
                }
            )

    top_hit = max(videos, key=lambda v: v["ratio"])
    worst_trough = min(videos, key=lambda v: v["ratio"])
    headline = {
        "videoCount": len(videos),
        "totalViews": sum(v["views"] for v in videos),
        "medianViewsPerDay": round(median(v["viewsPerDay"] for v in videos), 1),
        "hitCount": sum(1 for v in videos if v["ratioClass"] == "hit"),
        "troughCount": sum(1 for v in videos if v["ratioClass"] == "trough"),
        "refreshCount": sum(1 for v in videos if v["refreshCandidate"]),
    }
    return {
        "computedAt": iso_z(utcnow()),
        "healthScore": health_score,
        "healthRules": health_rules,
        "pillars": pillar_stats,
        "doubleDown": double_down,
        "refresh": refresh,
        "cadence": cadence_out,
        "checklist": checklist,
        "topHit": {
            "videoId": top_hit["id"],
            "title": top_hit["title"],
            "ratio": top_hit["ratio"],
        },
        "worstTrough": {
            "videoId": worst_trough["id"],
            "title": worst_trough["title"],
            "ratio": worst_trough["ratio"],
        },
        "headlineStats": headline,
    }


def run_pipeline(
    channel_in: dict, videos_in: list, source: str, out_dir: Path,
    velocity_proxy: bool = False,
) -> dict:
    """Run the full pipeline and write the three JSON files. Returns summary.

    velocity_proxy=True fills each video's trailing-30d velocity with its
    lifetime average views/day (used for real API pulls, which have no
    velocity signal) before the decay stage.
    """
    if not videos_in:
        raise ValueError("no videos to analyze")
    now = utcnow()
    out_dir.mkdir(parents=True, exist_ok=True)

    videos = outliers_mod.enrich(videos_in, now)
    if velocity_proxy:
        for video in videos:
            video["velocity"] = video["viewsPerDay"]
    videos = decay_mod.enrich(videos)
    cadence_stats = cadence_mod.compute(videos)
    health = score_mod.score_channel(videos, cadence_stats)

    channel_doc = {
        "channel": {
            "id": channel_in["id"],
            "title": channel_in["title"],
            "description": channel_in.get("description", ""),
            "subscriberCount": int(channel_in.get("subscriberCount", 0)),
            "videoCount": int(channel_in.get("videoCount", 0)),
            "viewCount": int(channel_in.get("viewCount", 0)),
            "publishedAt": channel_in.get("publishedAt", ""),
            "fetchedAt": iso_z(now),
            "source": source,
        },
        "computedAt": iso_z(now),
    }
    (out_dir / "channel.json").write_text(
        json.dumps(channel_doc, indent=2), encoding="utf-8"
    )

    videos_doc = [{f: v[f] for f in VIDEO_FIELDS} for v in videos]
    (out_dir / "videos.json").write_text(
        json.dumps(videos_doc, indent=2), encoding="utf-8"
    )

    brief_doc = _build_brief(videos, cadence_stats, health)
    (out_dir / "brief.json").write_text(
        json.dumps(brief_doc, indent=2), encoding="utf-8"
    )

    headline = brief_doc["headlineStats"]
    return {
        "videos": len(videos),
        "hits": headline["hitCount"],
        "troughs": headline["troughCount"],
        "refresh": headline["refreshCount"],
        "score": brief_doc["healthScore"],
        "out_dir": str(out_dir),
    }


def run_build(data_path: Path | None = None, out_dir: Path | None = None) -> dict:
    """Build from the sample fixture."""
    data_path = data_path or ROOT / "data" / "sample-channel.json"
    out_dir = out_dir or ROOT / "web" / "public"
    doc = json.loads(data_path.read_text(encoding="utf-8"))
    channel_in = doc["channel"]
    videos_in = [
        {
            "id": v["id"],
            "title": v["title"],
            "publishedAt": v["publishedAt"],
            "durationS": v["durationS"],
            "views": v["views"],
            "likes": v["likes"],
            "comments": v["comments"],
            "velocity": v.get("velocity", 0),
        }
        for v in doc["videos"]
    ]
    return run_pipeline(channel_in, videos_in, "sample", out_dir)


def run_fetch(api_key: str, channel_id: str, max_videos: int, out_dir: Path) -> dict:
    """Fetch real data from YouTube and run the pipeline."""
    if not CHANNEL_ID_RE.match(channel_id):
        raise ValueError(
            "channel id must look like a YouTube channel id (e.g. UC...); "
            f"got {channel_id!r}"
        )
    meta = youtube_client.fetch_channel_meta(api_key, channel_id)
    raw = youtube_client.fetch_channel_videos(api_key, channel_id, max_videos)
    videos_in = [
        {
            "id": v["id"],
            "title": v["title"],
            "publishedAt": v["published_at"],
            "durationS": v["duration_s"],
            "views": v["views"],
            "likes": v["likes"],
            "comments": v["comments"],
            "velocity": None,  # filled by the velocity_proxy step
        }
        for v in raw
    ]
    channel_in = {
        "id": meta["id"],
        "title": meta["title"],
        "description": meta["description"],
        "subscriberCount": meta["subscriberCount"],
        "videoCount": meta["videoCount"],
        "viewCount": meta["viewCount"],
        "publishedAt": meta["publishedAt"],
    }
    # The API exposes no trailing-30d velocity; the lifetime average stands
    # in as a proxy (decay skews low on old videos).
    return run_pipeline(channel_in, videos_in, "youtube", out_dir, velocity_proxy=True)


def _parse_fetch_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="main.py fetch")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--max-videos", type=int, default=200)
    return parser.parse_args(argv)


def main(argv) -> int:
    if len(argv) < 2 or argv[1] not in ("build", "fetch"):
        print(
            "usage: python3 services/main.py build | "
            "python3 services/main.py fetch --api-key KEY --channel-id UC... "
            "[--max-videos N]",
            file=sys.stderr,
        )
        return 2
    summary = None
    source = argv[1]
    try:
        if source == "build":
            summary = run_build()
        else:
            args = _parse_fetch_args(argv[2:])
            import os

            api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY")
            if not api_key:
                print(
                    "[fetch] FATAL: no API key (pass --api-key or set YOUTUBE_API_KEY)",
                    file=sys.stderr,
                )
                return 1
            summary = run_fetch(
                api_key, args.channel_id, args.max_videos, ROOT / "web" / "public"
            )
        print(
            f"[build] source={source} videos={summary['videos']} "
            f"hits={summary['hits']} troughs={summary['troughs']} "
            f"refresh={summary['refresh']} score={summary['score']} "
            f"out={summary['out_dir']}"
        )
        return 0
    except (youtube_client.YouTubeAPIError, ValueError, FileNotFoundError) as exc:
        print(f"[build] FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # fail loudly on anything unexpected
        print(f"[build] FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
