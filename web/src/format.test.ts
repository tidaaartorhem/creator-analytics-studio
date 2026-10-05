// Unit tests for format.ts formatters and thresholds.
import { describe, expect, it } from "vitest";
import {
  fmtCompact,
  fmtDate,
  fmtDuration,
  fmtPct,
  fmtRatio,
  ratioBadgeClass,
  scoreBand,
} from "./format";

describe("fmtCompact", () => {
  it("compacts millions to one decimal", () => {
    expect(fmtCompact(1_234_567)).toBe("1.2M");
  });
  it("compacts thousands to one decimal", () => {
    expect(fmtCompact(48_500)).toBe("48.5K");
  });
  it("leaves small numbers whole", () => {
    expect(fmtCompact(900)).toBe("900");
  });
  it("handles zero", () => {
    expect(fmtCompact(0)).toBe("0");
  });
  it("handles billions", () => {
    expect(fmtCompact(2_400_000_000)).toBe("2.4B");
  });
});

describe("fmtRatio", () => {
  it("renders one decimal with × suffix", () => {
    expect(fmtRatio(2.4)).toBe("2.4×");
  });
  it("renders sub-1 ratios", () => {
    expect(fmtRatio(0.38)).toBe("0.4×");
  });
});

describe("fmtPct", () => {
  it("converts a fraction to a percent string", () => {
    expect(fmtPct(0.046)).toBe("4.6%");
  });
  it("handles whole percents", () => {
    expect(fmtPct(0.08)).toBe("8.0%");
  });
});

describe("fmtDuration", () => {
  it("formats minutes and seconds", () => {
    expect(fmtDuration(754)).toBe("12:34");
  });
  it("pads seconds", () => {
    expect(fmtDuration(65)).toBe("1:05");
  });
  it("includes hours when present", () => {
    expect(fmtDuration(3723)).toBe("1:02:03");
  });
});

describe("fmtDate", () => {
  it("formats an ISO timestamp in UTC", () => {
    expect(fmtDate("2024-03-14T00:00:00Z")).toBe("Mar 14, 2024");
  });
  it("ignores the time portion across midnight boundaries", () => {
    expect(fmtDate("2025-06-10T23:59:59Z")).toBe("Jun 10, 2025");
  });
});

describe("ratioBadgeClass", () => {
  it("classifies exactly 2.0 as a hit", () => {
    expect(ratioBadgeClass(2.0)).toBe("hit");
  });
  it("classifies just below 2.0 as normal", () => {
    expect(ratioBadgeClass(1.99)).toBe("normal");
  });
  it("classifies exactly 0.5 as a trough", () => {
    expect(ratioBadgeClass(0.5)).toBe("trough");
  });
  it("classifies just above 0.5 as normal", () => {
    expect(ratioBadgeClass(0.51)).toBe("normal");
  });
});

describe("scoreBand", () => {
  it("calls 70 healthy", () => {
    expect(scoreBand(70)).toBe("healthy");
  });
  it("calls 69 mixed", () => {
    expect(scoreBand(69)).toBe("mixed");
  });
  it("calls 45 mixed", () => {
    expect(scoreBand(45)).toBe("mixed");
  });
  it("calls 44 at-risk", () => {
    expect(scoreBand(44)).toBe("at-risk");
  });
});
