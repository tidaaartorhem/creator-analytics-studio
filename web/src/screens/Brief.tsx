// Brief: the weekly studio brief as an actionable checklist (local state only).
import { useState } from "react";
import type { Brief } from "../types";
import { fmtCompact, fmtPct, groupChecklist, kindLabel } from "../format";

export default function Brief({ brief }: { brief: Brief }) {
  const [done, setDone] = useState<Set<number>>(new Set());
  const groups = groupChecklist(brief.checklist);

  const toggle = (idx: number) => {
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  let globalIdx = -1;

  return (
    <div>
      <div className="panel-head">
        <h2>Weekly brief</h2>
        <span className="muted" style={{ fontSize: "12px" }}>
          <span className="num">{done.size}</span> of {brief.checklist.length} done
        </span>
      </div>

      <h3>This week's checklist</h3>
      {groups.map((g) => (
        <div className="check-group" key={g.kind}>
          <h4>{kindLabel(g.kind)}</h4>
          <ul className="check-list">
            {g.items.map((item) => {
              globalIdx += 1;
              const idx = globalIdx;
              const isDone = done.has(idx);
              return (
                <li className={`check-item${isDone ? " done" : ""}`} key={idx}>
                  <input
                    type="checkbox"
                    id={`check-${idx}`}
                    checked={isDone}
                    onChange={() => toggle(idx)}
                    aria-label={item.title}
                  />
                  <div>
                    <label htmlFor={`check-${idx}`} className="check-title">
                      <span className="kind-tag">{kindLabel(item.kind)}</span>
                      {item.title}
                    </label>
                    <p className="check-detail">{item.detail}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ))}

      <h3>Double down</h3>
      <div className="card">
        <ul className="check-list">
          {brief.doubleDown.map((d, i) => (
            <li className="check-item" key={i} style={{ gridTemplateColumns: "1fr" }}>
              <div>
                <div className="check-title">
                  {d.pillar}{" "}
                  <span className="muted num" style={{ fontWeight: 400, fontSize: "12px" }}>
                    {d.count} videos · {d.medianViewsPerDay.toFixed(1)} median views/day ·{" "}
                    {fmtPct(d.engagement)} engagement
                  </span>
                </div>
                <p className="check-detail">{d.why}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <h3>Refresh queue</h3>
      <div className="card">
        <ul className="check-list">
          {brief.refresh.map((r) => (
            <li className="check-item" key={r.videoId} style={{ gridTemplateColumns: "1fr" }}>
              <div>
                <div className="check-title">
                  {r.title}{" "}
                  <span className="muted num" style={{ fontWeight: 400, fontSize: "12px" }}>
                    {fmtCompact(r.lifetimeViews)} views · decay {r.decayScore.toFixed(2)}
                  </span>
                </div>
                <p className="check-detail">{r.why}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <h3>Cadence guidance</h3>
      <div className="card">
        <p style={{ margin: 0, fontSize: "13px" }}>{brief.cadence.guidance}</p>
        <p className="muted" style={{ margin: "8px 0 0", fontSize: "12px" }}>
          Median gap between uploads: <span className="num">{brief.cadence.medianGapDays} days</span>
          {brief.cadence.bestHour !== null && (
            <>
              {" "}· strongest hour: <span className="num">{brief.cadence.bestHour}:00</span>
            </>
          )}
          {brief.cadence.bestDow.length > 0 && (
            <> · best days: <strong>{brief.cadence.bestDow.join(", ")}</strong></>
          )}
        </p>
      </div>
    </div>
  );
}
