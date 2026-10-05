// Pillars: per-pillar cards plus a catalog-wide comparison bar chart.
import type { Brief } from "../types";
import { fmtCompact, fmtPct } from "../format";

const ENGAGEMENT_BENCHMARK = 0.06;

export default function Pillars({ brief }: { brief: Brief }) {
  const pillars = [...brief.pillars].sort((a, b) => b.medianViewsPerDay - a.medianViewsPerDay);
  const maxVpd = Math.max(...pillars.map((p) => p.medianViewsPerDay), 1);

  return (
    <div>
      <div className="panel-head">
        <h2>Content pillars</h2>
        <span className="muted" style={{ fontSize: "12px" }}>
          Keyword-based groups — not semantic topic modeling
        </span>
      </div>

      <div className="pillar-cards" style={{ marginBottom: "16px" }}>
        {pillars.map((p) => (
          <div className="card" key={p.id}>
            <div className="panel-head" style={{ marginBottom: "6px" }}>
              <strong style={{ fontSize: "13.5px" }}>{p.label}</strong>
              <span className="badge badge-neutral">
                {p.count} video{p.count === 1 ? "" : "s"} · {p.shareOfCatalogPct.toFixed(1)}%
              </span>
            </div>
            <div className="micro-label">Median views/day</div>
            <div className="stat-val num">{p.medianViewsPerDay.toFixed(1)}</div>
            <div className="micro-label" style={{ marginTop: "8px" }}>
              Median engagement vs 6% benchmark
            </div>
            <div className="bar-list" style={{ marginTop: "6px" }}>
              <div className="bar-row" style={{ gridTemplateColumns: "1fr 120px" }}>
                <span className="bar-track" style={{ gridColumn: "1" }}>
                  <span
                    className="bar-fill"
                    style={{
                      width: `${Math.min(100, (p.medianEngagementRate / ENGAGEMENT_BENCHMARK) * 100)}%`,
                    }}
                  />
                </span>
                <span className="bar-val num">{fmtPct(p.medianEngagementRate)}</span>
              </div>
            </div>
            <p className="footnote">
              {p.medianEngagementRate >= ENGAGEMENT_BENCHMARK
                ? `▲ above the ${fmtPct(ENGAGEMENT_BENCHMARK)} benchmark`
                : `▼ below the ${fmtPct(ENGAGEMENT_BENCHMARK)} benchmark`}
            </p>
          </div>
        ))}
      </div>

      <h3>Median views/day by pillar</h3>
      <div className="card">
        <div className="bar-list">
          {pillars.map((p) => (
            <div className="bar-row" key={p.id}>
              <span className="bar-label">{p.label}</span>
              <span className="bar-track">
                <span
                  className="bar-fill"
                  style={{ width: `${(p.medianViewsPerDay / maxVpd) * 100}%` }}
                />
              </span>
              <span className="bar-val num">
                {p.medianViewsPerDay.toFixed(1)} · {fmtCompact(p.count)} videos
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
