// Filtering/sorting logic tests + schema validation of the videos fixture.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { filterVideos, sortVideos, type VideoFilters } from "./format";
import type { Video } from "./types";

const FIXTURE_DIR = fileURLToPath(new URL("../public/", import.meta.url));
const videos: Video[] = JSON.parse(readFileSync(`${FIXTURE_DIR}videos.json`, "utf-8"));

const baseFilters: VideoFilters = { query: "", pillar: "all", ratioClass: "all", refreshOnly: false };

describe("filterVideos", () => {
  it("returns everything with empty filters", () => {
    expect(filterVideos(videos, baseFilters)).toHaveLength(videos.length);
  });
  it("matches titles case-insensitively", () => {
    const rows = filterVideos(videos, { ...baseFilters, query: "THUMBNAIL" });
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((v) => v.title.toLowerCase().includes("thumbnail"))).toBe(true);
  });
  it("filters by pillar id", () => {
    const rows = filterVideos(videos, { ...baseFilters, pillar: "gear" });
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((v) => v.pillar === "gear")).toBe(true);
  });
  it("filters hits and troughs separately", () => {
    const hits = filterVideos(videos, { ...baseFilters, ratioClass: "hit" });
    const troughs = filterVideos(videos, { ...baseFilters, ratioClass: "trough" });
    expect(hits.every((v) => v.ratioClass === "hit")).toBe(true);
    expect(troughs.every((v) => v.ratioClass === "trough")).toBe(true);
    expect(hits.length + troughs.length).toBeLessThanOrEqual(videos.length);
  });
  it("refresh-only returns only flagged candidates", () => {
    const rows = filterVideos(videos, { ...baseFilters, refreshOnly: true });
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((v) => v.refreshCandidate)).toBe(true);
  });
  it("returns an empty list when nothing matches", () => {
    expect(filterVideos(videos, { ...baseFilters, query: "zzz-no-such-title" })).toHaveLength(0);
  });
});

describe("sortVideos", () => {
  it("sorts numeric keys descending", () => {
    const rows = sortVideos(videos, "views", "desc");
    for (let i = 1; i < rows.length; i += 1) {
      expect(rows[i - 1].views).toBeGreaterThanOrEqual(rows[i].views);
    }
  });
  it("sorts numeric keys ascending", () => {
    const rows = sortVideos(videos, "viewsPerDay", "asc");
    for (let i = 1; i < rows.length; i += 1) {
      expect(rows[i - 1].viewsPerDay).toBeLessThanOrEqual(rows[i].viewsPerDay);
    }
  });
  it("sorts string keys alphabetically", () => {
    const rows = sortVideos(videos, "title", "asc");
    const titles = rows.map((v) => v.title);
    expect([...titles].sort((a, b) => a.localeCompare(b))).toEqual(titles);
  });
  it("does not mutate the input array", () => {
    const first = videos[0];
    sortVideos(videos, "views", "asc");
    expect(videos[0]).toBe(first);
  });
});

const REQUIRED_KEYS = [
  "id", "title", "publishedAt", "durationS", "views", "likes", "comments",
  "ageDays", "viewsPerDay", "engagementRate", "ratio", "ratioClass",
  "pillar", "pillarLabel", "peakVelocity30", "trailingVelocity30",
  "decayScore", "refreshCandidate",
] as const;

describe("videos fixture schema", () => {
  it("every video carries all required keys", () => {
    expect(videos.length).toBeGreaterThan(0);
    for (const v of videos) {
      for (const k of REQUIRED_KEYS) {
        expect(v, `missing key ${k} on ${v.id}`).toHaveProperty(k);
      }
    }
  });
  it("ratio classes use only valid values", () => {
    for (const v of videos) {
      expect(["hit", "trough", "normal"]).toContain(v.ratioClass);
    }
  });
  it("engagementRate is a fraction in 0..1", () => {
    for (const v of videos) {
      expect(v.engagementRate).toBeGreaterThanOrEqual(0);
      expect(v.engagementRate).toBeLessThanOrEqual(1);
    }
  });
});
