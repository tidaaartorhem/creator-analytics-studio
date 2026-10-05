// Videos: sortable catalog table with search + pillar / ratio-class / refresh filters.
import { useMemo, useState } from "react";
import type { Video } from "../types";
import {
  EMPTY_FILTERS,
  filterVideos,
  fmtCompact,
  fmtDate,
  fmtDuration,
  fmtPct,
  sortVideos,
  type SortDir,
  type SortKey,
} from "../format";
import { RatioBadge } from "../components";

const COLUMNS: { key: SortKey; label: string; right?: boolean }[] = [
  { key: "title", label: "Title" },
  { key: "publishedAt", label: "Published" },
  { key: "durationS", label: "Duration", right: true },
  { key: "views", label: "Views", right: true },
  { key: "viewsPerDay", label: "Views/day", right: true },
  { key: "engagementRate", label: "Engagement", right: true },
  { key: "ratio", label: "Ratio", right: true },
  { key: "pillar", label: "Pillar" },
];

function cellValue(v: Video, key: SortKey): string {
  switch (key) {
    case "title":
      return v.title;
    case "publishedAt":
      return fmtDate(v.publishedAt);
    case "durationS":
      return fmtDuration(v.durationS);
    case "views":
      return fmtCompact(v.views);
    case "viewsPerDay":
      return v.viewsPerDay.toFixed(1);
    case "engagementRate":
      return fmtPct(v.engagementRate);
    case "ratio":
      return "";
    case "pillar":
      return v.pillarLabel;
  }
}

export default function Videos({ videos }: { videos: Video[] }) {
  const [query, setQuery] = useState(EMPTY_FILTERS.query);
  const [pillar, setPillar] = useState(EMPTY_FILTERS.pillar);
  const [ratioClass, setRatioClass] = useState< "all" | "hit" | "trough">(EMPTY_FILTERS.ratioClass);
  const [refreshOnly, setRefreshOnly] = useState(EMPTY_FILTERS.refreshOnly);
  const [sortKey, setSortKey] = useState<SortKey>("viewsPerDay");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const pillars = useMemo(() => {
    const map = new Map<string, string>();
    for (const v of videos) map.set(v.pillar, v.pillarLabel);
    return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1]));
  }, [videos]);

  const rows = useMemo(
    () => sortVideos(filterVideos(videos, { query, pillar, ratioClass, refreshOnly }), sortKey, sortDir),
    [videos, query, pillar, ratioClass, refreshOnly, sortKey, sortDir]
  );

  const onSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "title" || key === "pillar" ? "asc" : "desc");
    }
  };

  return (
    <div>
      <div className="panel-head">
        <h2>Videos</h2>
        <span className="muted num" style={{ fontSize: "12px" }}>
          {rows.length} of {videos.length} shown
        </span>
      </div>

      <div className="controls">
        <input
          className="search-input"
          type="search"
          placeholder="Search titles…"
          aria-label="Search video titles"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="select"
          aria-label="Filter by pillar"
          value={pillar}
          onChange={(e) => setPillar(e.target.value)}
        >
          <option value="all">All pillars</option>
          {pillars.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
        <div className="segmented" role="group" aria-label="Filter by performance class">
          {(["all", "hit", "trough"] as const).map((c) => (
            <button
              key={c}
              className={ratioClass === c ? "active" : ""}
              aria-pressed={ratioClass === c}
              onClick={() => setRatioClass(c)}
            >
              {c === "all" ? "All" : c === "hit" ? "▲ Hits" : "▼ Troughs"}
            </button>
          ))}
        </div>
        <label className="toggle">
          <input
            type="checkbox"
            checked={refreshOnly}
            onChange={(e) => setRefreshOnly(e.target.checked)}
          />
          Refresh candidates only
        </label>
      </div>

      {rows.length === 0 ? (
        <div className="card empty">No videos match these filters.</div>
      ) : (
        <div className="table-wrap">
          <table className="t">
            <thead>
              <tr>
                {COLUMNS.map((c) => (
                  <th key={c.key} className={c.right ? "cell-r" : ""}>
                    <button className="th-sort" onClick={() => onSort(c.key)}>
                      {c.label}
                      {sortKey === c.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((v) => (
                <tr key={v.id}>
                  {COLUMNS.map((c) => (
                    <td key={c.key} className={c.right ? "cell-r num" : c.key === "ratio" ? "cell-r" : ""}>
                      {c.key === "title" ? (
                        <span className="row-title">{cellValue(v, c.key)}</span>
                      ) : c.key === "ratio" ? (
                        <RatioBadge ratio={v.ratio} />
                      ) : (
                        <span className="num">{cellValue(v, c.key)}</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="footnote">
        Ratio compares a video's views/day to the catalog median: ▲ 2.0× or better is a
        hit, ▼ 0.5× or worse is a trough.
      </p>
    </div>
  );
}
