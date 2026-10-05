// Refresh: ranked decay candidates plus a static "what to test" guidance box.
import type { Brief, Video } from "../types";
import { fmtCompact } from "../format";

export default function Refresh({ brief, videos }: { brief: Brief; videos: Video[] }) {
  const byId = new Map(videos.map((v) => [v.id, v]));

  return (
    <div>
      <div className="panel-head">
        <h2>Refresh candidates</h2>
        <span className="badge badge-amber">⟳ {brief.refresh.length} queued</span>
      </div>

      {brief.refresh.length === 0 ? (
        <div className="card empty">No refresh candidates right now — nothing is decaying.</div>
      ) : (
        <ol className="refresh-list">
          {brief.refresh.map((r, i) => {
            const v = byId.get(r.videoId);
            return (
              <li className="refresh-item" key={r.videoId}>
                <span className="refresh-rank num" aria-hidden="true">
                  {i + 1}
                </span>
                <div>
                  <p className="refresh-title">{r.title}</p>
                  <div className="refresh-meta">
                    <span>
                      Lifetime <span className="num">{fmtCompact(r.lifetimeViews)}</span> views
                    </span>
                    {v && (
                      <span>
                        Velocity <span className="num">{fmtCompact(v.peakVelocity30)}</span> →{" "}
                        <span className="num">{fmtCompact(v.trailingVelocity30)}</span> views/day
                      </span>
                    )}
                    <span>
                      Decay score{" "}
                      <span className="num">{r.decayScore.toFixed(2)}</span>{" "}
                      <span className="decay-track">
                        <span
                          className="decay-fill"
                          style={{ width: `${Math.min(100, r.decayScore * 100)}%` }}
                        />
                      </span>
                    </span>
                  </div>
                  <p className="refresh-why">{r.why}</p>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      <div className="note-box" role="note">
        <p>
          <strong>What to test.</strong> YouTube's Test &amp; Compare runs the thumbnail A/B
          for you — this studio tells you <em>what</em> to test and <em>why</em>.
        </p>
        <p>
          For each candidate: lead with a thumbnail + title refresh (cheapest lever), ship it
          as a Test &amp; Compare, and only reshoot if the refreshed packaging underperforms
          after two weeks. Never touch a video whose decay is still below 0.5 — momentum is
          still on your side.
        </p>
      </div>
    </div>
  );
}
