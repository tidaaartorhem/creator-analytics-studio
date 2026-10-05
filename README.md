# Creator Analytics Studio — the content-portfolio audit for the solo YouTube creator

## The problem

A solo creator is a one-person media business, and YouTube Studio drowns them
in per-video numbers without ever answering the portfolio questions: which
topics actually earn the most per upload, which back-catalog videos are
decaying and worth a title/thumbnail refresh, whether the upload cadence helps
or hurts, and what to do this week. So creators guess — remaking formats that
quietly flopped, and ignoring evergreen videos that a new thumbnail could
revive. The analytics tell you *what* each video did. Nothing tells you what
the catalog is telling you.

## What this does

Point the studio at any public channel (bring your own free YouTube Data API
v3 key) or run the bundled sample channel. The Python service layer pulls the
full uploads playlist, then computes:

- **Performance ratio per video** — views/day normalized by video age, scored
  against the channel median. Hits (≥ 2.0x) and troughs (≤ 0.5x) surface
  automatically.
- **Content pillars** — keyword extraction over titles groups videos into
  topics, each with median views/day and engagement, so you can see which
  pillar earns its uploads.
- **Decay detection** — videos with strong lifetime views but collapsed recent
  velocity are flagged as **refresh candidates**: the highest-ROI work a
  creator can do is a new title/thumbnail on a proven video. (YouTube's own
  Test & Compare runs the A/B test — this tells you *what* to test.)
- **Cadence analysis** — publish day-of-week and hour vs median performance,
  plus median gap between uploads.
- **Channel health score 0–100** — deterministic, six documented rules, fixed
  penalties (`services/score.py`):

| Rule | Check | Warn | Fail |
|---|---|---|---|
| pillar-focus | top-2 pillars by median views/day hold ≥ 60% of uploads | −12 | −20 |
| hit-rate | ≥ 12% of videos earn ≥ 1.5x the channel median | −12 | −20 |
| trough-rate | troughs (≤ 0.5x median) stay under 20% of catalog | −12 | −20 |
| cadence-consistency | median gap between uploads ≤ 14 days | −9 | −15 |
| engagement | median (likes+comments)/views ≥ 3% | −9 | −15 |
| refresh-debt | refresh candidates under 5% of catalog | −6 | −10 |

- **Weekly studio brief** — a deterministic checklist: which topics to double
  down on, which videos to refresh, and what the cadence data says about the
  next publish.

The React frontend (`web/`, Vite + React 18, light mode) renders six views —
Overview, Videos, Pillars, Refresh, Cadence, Brief — from the generated JSONs.

## How it works

`python3 services/main.py build` reads `data/sample-channel.json` (76 videos,
clearly labeled as fictional sample data), runs the full analysis, and writes
`web/public/{channel,videos,brief}.json`. `python3 services/main.py fetch
--api-key KEY --channel-id UC...` pulls a real public channel through the
YouTube Data API v3 using the quota-cheap pattern (uploads playlist →
paginated playlist items → batched `videos.list`, 50 ids per call; `search`
is never called in a loop) and writes the same JSONs. The frontend build
re-runs the pipeline first, so every build ships freshly computed data.

## Run it

```bash
# 1. Run the pipeline (sample channel; no API key needed)
python3 services/main.py build

# ...or fetch a real public channel (free API key, your own quota)
python3 services/main.py fetch --api-key "$YOUTUBE_API_KEY" --channel-id UCxxxxxxxxxxxxxxxxxxxxxx

# 2. Dev the frontend
cd web && npm install && npm run dev

# 3. Production build (re-runs the pipeline, then vite build)
cd web && npm run build

# 4. Tests
python3 -m pytest services/tests/ -q   # 29 tests
cd web && npm test                     # 44 vitest tests
```

## Data sources

Public channel and video statistics come from the YouTube Data API v3, which
is free (10,000 units/day) and needs only an API key for public data — no
OAuth, no key shipped in this repo. The bundled sample channel is fictional
but realistic, so the studio runs end-to-end with zero setup.

## Honest limitations

- The public API exposes **no** click-through rate, audience retention,
  impressions, or revenue — those live behind the OAuth Analytics API and are
  out of scope by design. Every conclusion here is drawn from public counts.
- Pillars are keyword-based title clustering, not semantic topic modeling; a
  rebrand or title-style change can shift pillar assignments.
- The bundled channel is a fictional sample. Bring your own API key and
  channel id for real data.
- Velocity and decay are estimated from lifetime public counts, not true
  time-series — treat refresh rankings as a prioritized shortlist, not a
  guarantee.
