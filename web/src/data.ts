// Runtime data loaders. JSON files live in web/public/ and are fetched with
// relative paths so the app works under Firebase Hosting subpaths and when
// the built dist/ is served from a file system.
import type { Brief, ChannelData, Video } from "./types";

async function loadJson<T>(name: string): Promise<T> {
  const res = await fetch(`./${name}`);
  if (!res.ok) {
    throw new Error(`Could not load ${name} (HTTP ${res.status}).`);
  }
  return (await res.json()) as T;
}

export function loadChannel(): Promise<ChannelData> {
  return loadJson<ChannelData>("channel.json");
}

export function loadVideos(): Promise<Video[]> {
  return loadJson<Video[]>("videos.json");
}

export function loadBrief(): Promise<Brief> {
  return loadJson<Brief>("brief.json");
}

export interface StudioData {
  channel: ChannelData;
  videos: Video[];
  brief: Brief;
}

export async function loadAll(): Promise<StudioData> {
  const [channel, videos, brief] = await Promise.all([
    loadChannel(),
    loadVideos(),
    loadBrief(),
  ]);
  return { channel, videos, brief };
}
