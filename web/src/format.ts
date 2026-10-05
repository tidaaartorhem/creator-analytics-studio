// Pure formatting + filtering/sorting logic. No DOM, no fetch — everything
// here is unit-testable and deterministic.
import type { ChecklistItem, ChecklistKind, RatioClass, Video } from "./types";

/** 1,234,567 -> "1.2M"; 48,500 -> "48.5K"; 900 -> "900". */
export function fmtCompact(n: number): string {
  if (!Number.isFinite(n)) return "—";
  const sign = n < 0 ? "-" : "";
  const v = Math.abs(n);
  if (v >= 1_000_000_000) return `${sign}${(v / 1_000_000_000).toFixed(1)}B`;
  if (v >= 1_000_000) return `${sign}${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${sign}${(v / 1_000).toFixed(1)}K`;
  return `${sign}${Math.round(v)}`;
}

/** 2.4 -> "2.4×". */
export function fmtRatio(r: number): string {
  if (!Number.isFinite(r)) return "—";
  return `${r.toFixed(1)}×`;
}

/** 0.046 -> "4.6%" (fraction input). */
export function fmtPct(frac: number): string {
  if (!Number.isFinite(frac)) return "—";
  return `${(frac * 100).toFixed(1)}%`;
}

/** 754 -> "12:34"; 3723 -> "1:02:03". */
export function fmtDuration(totalS: number): string {
  const s = Math.max(0, Math.floor(totalS));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = h > 0 ? String(m).padStart(2, "0") : String(m);
  return `${h > 0 ? `${h}:` : ""}${mm}:${String(sec).padStart(2, "0")}`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2024-03-14T00:00:00Z" -> "Mar 14, 2024" (UTC, deterministic). */
export function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}

/** Ratio thresholds: >= 2.0 is a hit, <= 0.5 is a trough, else normal. */
export function ratioBadgeClass(ratio: number): RatioClass {
  if (ratio >= 2.0) return "hit";
  if (ratio <= 0.5) return "trough";
  return "normal";
}

export type ScoreBand = "healthy" | "mixed" | "at-risk";

/** Health score bands: >= 70 healthy, 45–69 mixed, < 45 at-risk. */
export function scoreBand(score: number): ScoreBand {
  if (score >= 70) return "healthy";
  if (score >= 45) return "mixed";
  return "at-risk";
}

export type SortKey =
  | "title"
  | "publishedAt"
  | "durationS"
  | "views"
  | "viewsPerDay"
  | "engagementRate"
  | "ratio"
  | "pillar";
export type SortDir = "asc" | "desc";

export interface VideoFilters {
  query: string;
  pillar: string; // pillar id, or "all"
  ratioClass: "all" | "hit" | "trough";
  refreshOnly: boolean;
}

export const EMPTY_FILTERS: VideoFilters = {
  query: "",
  pillar: "all",
  ratioClass: "all",
  refreshOnly: false,
};

/** Case-insensitive title substring match, plus pillar / ratio-class / refresh filters. */
export function filterVideos(videos: Video[], f: VideoFilters): Video[] {
  const q = f.query.trim().toLowerCase();
  return videos.filter((v) => {
    if (q && !v.title.toLowerCase().includes(q)) return false;
    if (f.pillar !== "all" && v.pillar !== f.pillar) return false;
    if (f.ratioClass !== "all" && v.ratioClass !== f.ratioClass) return false;
    if (f.refreshOnly && !v.refreshCandidate) return false;
    return true;
  });
}

const NUMERIC_KEYS = new Set<SortKey>([
  "durationS",
  "views",
  "viewsPerDay",
  "engagementRate",
  "ratio",
]);

/** Stable sort by the given key; strings sort via localeCompare. */
export function sortVideos(videos: Video[], key: SortKey, dir: SortDir): Video[] {
  const mul = dir === "asc" ? 1 : -1;
  const copy = [...videos];
  copy.sort((a, b) => {
    let cmp: number;
    if (NUMERIC_KEYS.has(key)) {
      cmp = (a[key] as number) - (b[key] as number);
    } else {
      cmp = String(a[key]).localeCompare(String(b[key]));
    }
    return cmp * mul;
  });
  return copy;
}

const KIND_ORDER: ChecklistKind[] = ["double-down", "refresh", "cadence", "score"];

/** Group checklist items by kind, in fixed kind order; drop empty groups. */
export function groupChecklist(
  items: ChecklistItem[]
): { kind: ChecklistKind; items: ChecklistItem[] }[] {
  return KIND_ORDER.map((kind) => ({
    kind,
    items: items.filter((i) => i.kind === kind),
  })).filter((g) => g.items.length > 0);
}

export function kindLabel(kind: ChecklistKind): string {
  switch (kind) {
    case "double-down":
      return "Double down";
    case "refresh":
      return "Refresh";
    case "cadence":
      return "Cadence";
    case "score":
      return "Score";
  }
}
