// Overview: health score ring, headline stats, hit/trough callouts, health rules.
import type { Brief, RuleStatus } from "../types";
import { fmtCompact, fmtRatio, scoreBand } from "../format";
import { ScoreRing, StatCard } from "../components";

const RULE_ICONS: Record<RuleStatus, { icon: string; cls: string }> = {
  pass: { icon: "✓", cls: "pos" },
  warn: { icon: "!", cls: "" },
  fail: { icon: "✕", cls: "neg" },
};

const BAND_GUIDANCE: Record<string, string> = {
  healthy: "The catalog is compounding — keep the current mix and shipping rhythm.",
  mixed: "Solid base, a few drags. Work the checklist below the fold.",
  "at-risk": "The catalog is stalling — refresh and double-down items are urgent.",
};

export default function Overview({ brief }: { brief: Brief }) {
  const h = brief.headlineStats;
  const band = scoreBand(brief.healthScore);
  return (
    <div>
      <div className="panel-head">
        <h2>Studio overview</h2>
        <span className="muted" style={{ fontSize: "12px" }}>
          Computed <span className="num">{new Date(brief.computedAt).toISOString().slice(0, 10)}</span>
        </span>
      </div>

      <div className="card" style={{ marginBottom: "12px" }}>
        <div className="score-wrap">
          <ScoreRing score={brief.healthScore} />
          <div className="score-meta">
            <div className="micro-label">Portfolio health</div>
            <p>
              <strong className="num">{Math.round(brief.healthScore)}/100</strong> —{" "}
              <span className={band === "healthy" ? "pos" : band === "at-risk" ? "neg" : ""}>
                {band}
              </span>
            </p>
            <p className="muted">{BAND_GUIDANCE[band]}</p>
          </div>
        </div>
      </div>

      <div className="stat-grid">
        <StatCard label="Videos" value={String(h.videoCount)} />
        <StatCard label="Total views" value={fmtCompact(h.totalViews)} />
        <StatCard label="Median views/day" value={h.medianViewsPerDay.toFixed(1)} />
        <StatCard
          label="Hits"
          value={String(h.hitCount)}
          sub={`${h.hitCount} of ${h.videoCount} above 2×`}
        />
        <StatCard label="Troughs" value={String(h.troughCount)} sub="at or below 0.5×" />
        <StatCard
          label="Refresh candidates"
          value={String(h.refreshCount)}
          sub="decaying, evergreen topics"
        />
      </div>

      <div className="callout-grid">
        <div className="callout callout-hit">
          <span className="badge badge-green">
            <span aria-hidden="true">▲</span> top hit
          </span>
          <p className="callout-title">{brief.topHit.title}</p>
          <p className="muted" style={{ margin: 0, fontSize: "12.5px" }}>
            <span className="num">{fmtRatio(brief.topHit.ratio)}</span> vs catalog median
          </p>
        </div>
        <div className="callout callout-trough">
          <span className="badge badge-red">
            <span aria-hidden="true">▼</span> worst trough
          </span>
          <p className="callout-title">{brief.worstTrough.title}</p>
          <p className="muted" style={{ margin: 0, fontSize: "12.5px" }}>
            <span className="num">{fmtRatio(brief.worstTrough.ratio)}</span> vs catalog median
          </p>
        </div>
      </div>

      <h3>Health rules</h3>
      <div className="card">
        <ul className="rules">
          {brief.healthRules.map((r, i) => {
            const ic = RULE_ICONS[r.status];
            return (
              <li key={i}>
                <span className={`rule-icon ${ic.cls}`} aria-hidden="true">
                  {ic.icon}
                </span>
                <div>
                  <div className="rule-head">
                    <span className="rule-name">{r.rule}</span>
                    <span className="rule-check">{r.check}</span>
                  </div>
                  <p className="rule-detail">{r.detail}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
