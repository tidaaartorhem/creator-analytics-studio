// Small shared UI components: score ring, ratio badge, stat card.
import { fmtRatio, scoreBand } from "./format";

const BAND_COLORS = {
  healthy: "#1a7f37",
  mixed: "#9a6700",
  "at-risk": "#cf222e",
} as const;

export function ScoreRing({ score }: { score: number }) {
  const band = scoreBand(score);
  const color = BAND_COLORS[band];
  const r = 42;
  const circumference = 2 * Math.PI * r;
  const frac = Math.max(0, Math.min(100, score)) / 100;
  return (
    <svg
      width="110"
      height="110"
      viewBox="0 0 110 110"
      role="img"
      aria-label={`Health score ${Math.round(score)} out of 100 (${band})`}
    >
      <circle cx="55" cy="55" r={r} fill="none" stroke="#e8edf3" strokeWidth="10" />
      <circle
        cx="55"
        cy="55"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${frac * circumference} ${circumference}`}
        transform="rotate(-90 55 55)"
      />
      <text
        x="55"
        y="52"
        textAnchor="middle"
        className="num"
        fontSize="22"
        fontWeight="700"
        fill="#1e293b"
      >
        {Math.round(score)}
      </text>
      <text x="55" y="68" textAnchor="middle" fontSize="10" fill="#64748b">
        {band}
      </text>
    </svg>
  );
}

export function RatioBadge({ ratio }: { ratio: number }) {
  if (ratio >= 2.0) {
    return (
      <span className="badge badge-green">
        <span aria-hidden="true">▲</span> {fmtRatio(ratio)}
      </span>
    );
  }
  if (ratio <= 0.5) {
    return (
      <span className="badge badge-red">
        <span aria-hidden="true">▼</span> {fmtRatio(ratio)}
      </span>
    );
  }
  return (
    <span className="badge badge-neutral">
      <span className="num">{fmtRatio(ratio)}</span>
    </span>
  );
}

export function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="stat">
      <div className="micro-label">{label}</div>
      <div className="stat-val num">{value}</div>
      {sub && <div className="muted" style={{ fontSize: "11.5px" }}>{sub}</div>}
    </div>
  );
}
