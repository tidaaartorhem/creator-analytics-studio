// Cadence: day-of-week heatmap, hour-of-day strip, publishing gap insight.
import type { Brief } from "../types";

const HOUR_FMT = (h: number) => (h === 0 ? "12a" : h < 12 ? `${h}a` : h === 12 ? "12p" : `${h - 12}p`);

export default function Cadence({ brief }: { brief: Brief }) {
  const c = brief.cadence;
  const dow = [...c.dowStats].sort((a, b) => a.dow - b.dow);
  const hours = [...c.hourStats].sort((a, b) => a.hour - b.hour);
  const maxDow = Math.max(...dow.map((d) => d.medianViewsPerDay), 1);
  const maxHour = Math.max(...hours.map((h) => h.medianViewsPerDay), 1);

  return (
    <div>
      <div className="panel-head">
        <h2>Cadence</h2>
        <span className="muted" style={{ fontSize: "12px" }}>
          When uploads land vs how they perform
        </span>
      </div>

      <h3 style={{ marginTop: 0 }}>Day of week — median views/day</h3>
      <div className="heatmap-7">
        {dow.map((d) => {
          const intensity = d.medianViewsPerDay / maxDow;
          return (
            <div
              className="heat-cell"
              key={d.dow}
              style={{ background: `rgba(15, 118, 110, ${0.04 + intensity * 0.16})` }}
            >
              <div className="heat-day">{d.label}</div>
              <div className="heat-val num">{d.medianViewsPerDay.toFixed(1)}</div>
              <div className="heat-sub">
                {d.count} video{d.count === 1 ? "" : "s"}
              </div>
            </div>
          );
        })}
      </div>

      <h3>Hour of day — median views/day</h3>
      <div className="hour-strip" role="img" aria-label="Median views per day by publish hour">
        {hours.map((h) => (
          <div
            className="hour-cell"
            key={h.hour}
            title={`${HOUR_FMT(h.hour)}: ${h.medianViewsPerDay.toFixed(1)} median views/day, ${h.count} uploads`}
            style={{
              background:
                h.count === 0 ? undefined : `rgba(15, 118, 110, ${0.06 + (h.medianViewsPerDay / maxHour) * 0.2})`,
            }}
          >
            <span className="num">{h.medianViewsPerDay > 0 ? h.medianViewsPerDay.toFixed(0) : "–"}</span>
          </div>
        ))}
      </div>
      <div className="hour-labels" aria-hidden="true">
        {hours.map((h) => (
          <span key={h.hour}>{HOUR_FMT(h.hour)}</span>
        ))}
      </div>

      <div className="two-col" style={{ marginTop: "16px" }}>
        <div className="card">
          <div className="micro-label">Best windows</div>
          <p style={{ margin: "6px 0", fontSize: "13px" }}>
            <strong>{c.bestDow.length > 0 ? c.bestDow.join(" + ") : "No day stands out"}</strong>
            {c.bestHour !== null && (
              <>
                {" "}· <strong>{HOUR_FMT(c.bestHour)}</strong>
              </>
            )}
          </p>
          <p className="muted" style={{ margin: 0, fontSize: "12px" }}>
            Days and hours with the highest median views/day in your catalog.
          </p>
        </div>
        <div className="card">
          <div className="micro-label">Median gap between uploads</div>
          <p style={{ margin: "6px 0", fontSize: "13px" }}>
            <strong className="num">{c.medianGapDays} days</strong>
          </p>
          <p className="muted" style={{ margin: 0, fontSize: "12px" }}>
            {c.medianGapDays > 45
              ? "▲ Long gaps cost momentum — tighten the rhythm."
              : "Steady rhythm. Keep releases inside 35 days."}
          </p>
        </div>
      </div>

      <div className="note-box" role="note" style={{ marginTop: "16px" }}>
        <p>
          <strong>Guidance.</strong> {c.guidance}
        </p>
      </div>
    </div>
  );
}
