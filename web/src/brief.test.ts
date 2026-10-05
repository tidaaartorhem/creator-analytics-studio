// Brief grouping logic + schema validation of the channel/brief fixtures.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { groupChecklist, kindLabel } from "./format";
import type { Brief, ChannelData, ChecklistKind } from "./types";

const FIXTURE_DIR = fileURLToPath(new URL("../public/", import.meta.url));
const channel: ChannelData = JSON.parse(readFileSync(`${FIXTURE_DIR}channel.json`, "utf-8"));
const brief: Brief = JSON.parse(readFileSync(`${FIXTURE_DIR}brief.json`, "utf-8"));

describe("groupChecklist", () => {
  it("groups in fixed kind order and drops empty groups", () => {
    const groups = groupChecklist([
      { title: "c", detail: "", kind: "cadence" },
      { title: "a", detail: "", kind: "double-down" },
      { title: "b", detail: "", kind: "double-down" },
      { title: "d", detail: "", kind: "score" },
    ]);
    expect(groups.map((g) => g.kind)).toEqual(["double-down", "cadence", "score"]);
    expect(groups[0].items.map((i) => i.title)).toEqual(["a", "b"]);
  });
  it("returns an empty array for an empty checklist", () => {
    expect(groupChecklist([])).toEqual([]);
  });
});

describe("kindLabel", () => {
  it("labels every kind without color alone", () => {
    const kinds: ChecklistKind[] = ["double-down", "refresh", "cadence", "score"];
    for (const k of kinds) {
      expect(kindLabel(k)).toMatch(/\S/);
    }
    expect(kindLabel("double-down")).toBe("Double down");
  });
});

describe("channel fixture schema", () => {
  it("carries a channel object with required keys", () => {
    for (const k of ["id", "title", "subscriberCount", "videoCount", "viewCount", "source"]) {
      expect(channel.channel, `missing ${k}`).toHaveProperty(k);
    }
    expect(["sample", "youtube"]).toContain(channel.channel.source);
  });
});

describe("brief fixture schema", () => {
  it("carries the top-level contract keys", () => {
    for (const k of [
      "computedAt", "healthScore", "healthRules", "pillars", "doubleDown",
      "refresh", "cadence", "checklist", "topHit", "worstTrough", "headlineStats",
    ]) {
      expect(brief, `missing ${k}`).toHaveProperty(k);
    }
  });
  it("health rules use only valid statuses", () => {
    expect(brief.healthRules.length).toBeGreaterThan(0);
    for (const r of brief.healthRules) {
      expect(["pass", "warn", "fail"]).toContain(r.status);
      expect(r.detail).toMatch(/\S/);
    }
  });
  it("checklist items use only valid kinds", () => {
    expect(brief.checklist.length).toBeGreaterThan(0);
    for (const c of brief.checklist) {
      expect(["double-down", "refresh", "cadence", "score"]).toContain(c.kind);
    }
  });
  it("cadence covers 7 days and 24 hours", () => {
    expect(brief.cadence.dowStats).toHaveLength(7);
    expect(brief.cadence.hourStats).toHaveLength(24);
    expect(brief.cadence.dowStats.map((d) => d.dow).sort()).toEqual([0, 1, 2, 3, 4, 5, 6]);
    expect(brief.cadence.hourStats.map((h) => h.hour).sort((a, b) => a - b)).toEqual(
      Array.from({ length: 24 }, (_, i) => i)
    );
  });
  it("refresh recs are ordered by decay score descending", () => {
    const scores = brief.refresh.map((r) => r.decayScore);
    for (let i = 1; i < scores.length; i += 1) {
      expect(scores[i - 1]).toBeGreaterThanOrEqual(scores[i]);
    }
  });
});
