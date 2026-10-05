// Data contract for creator-analytics-studio.
// channel.json / videos.json / brief.json are read from web/public/ at runtime
// via relative fetch paths. The Python pipeline owns these files; the shapes
// below must stay in sync with services/main.py.

export type RatioClass = "hit" | "trough" | "normal";
export type ChannelSource = "sample" | "youtube";
export type RuleStatus = "pass" | "warn" | "fail";
export type ChecklistKind = "double-down" | "refresh" | "cadence" | "score";

export interface Channel {
  id: string;
  title: string;
  description: string;
  subscriberCount: number;
  videoCount: number;
  viewCount: number;
  publishedAt: string; // ISO 8601
  fetchedAt: string; // ISO 8601
  source: ChannelSource;
}

export interface ChannelData {
  channel: Channel;
  computedAt: string; // ISO 8601
}

export interface Video {
  id: string;
  title: string;
  publishedAt: string; // ISO 8601
  durationS: number;
  views: number;
  likes: number;
  comments: number;
  ageDays: number;
  viewsPerDay: number;
  /** Fraction in 0..1, e.g. 0.046 for 4.6%. */
  engagementRate: number;
  /** Lifetime views vs catalog median views-per-day, e.g. 2.4. */
  ratio: number;
  ratioClass: RatioClass;
  pillar: string;
  pillarLabel: string;
  peakVelocity30: number;
  trailingVelocity30: number;
  /** 0..1, higher = faster decay. */
  decayScore: number;
  refreshCandidate: boolean;
}

export interface HealthRule {
  rule: string;
  check: string;
  status: RuleStatus;
  detail: string;
}

export interface PillarStat {
  id: string;
  label: string;
  count: number;
  medianViewsPerDay: number;
  /** Fraction in 0..1. */
  medianEngagementRate: number;
  shareOfCatalogPct: number;
}

export interface DoubleDown {
  pillar: string;
  medianViewsPerDay: number;
  /** Fraction in 0..1. */
  engagement: number;
  count: number;
  why: string;
}

export interface RefreshRec {
  videoId: string;
  title: string;
  decayScore: number;
  lifetimeViews: number;
  why: string;
}

export interface DowStat {
  /** 0 = Monday, 6 = Sunday. */
  dow: number;
  label: string;
  count: number;
  medianViewsPerDay: number;
}

export interface HourStat {
  /** 0..23 local hour. */
  hour: number;
  count: number;
  medianViewsPerDay: number;
}

export interface Cadence {
  bestDow: string[];
  bestHour: number | null;
  medianGapDays: number;
  guidance: string;
  dowStats: DowStat[];
  hourStats: HourStat[];
}

export interface ChecklistItem {
  title: string;
  detail: string;
  kind: ChecklistKind;
}

export interface Brief {
  computedAt: string; // ISO 8601
  healthScore: number; // 0..100
  healthRules: HealthRule[];
  pillars: PillarStat[];
  doubleDown: DoubleDown[];
  refresh: RefreshRec[];
  cadence: Cadence;
  checklist: ChecklistItem[];
  topHit: { videoId: string; title: string; ratio: number };
  worstTrough: { videoId: string; title: string; ratio: number };
  headlineStats: {
    videoCount: number;
    totalViews: number;
    medianViewsPerDay: number;
    hitCount: number;
    troughCount: number;
    refreshCount: number;
  };
}
