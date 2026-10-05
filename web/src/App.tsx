// App shell: topbar with product name + sample badge, tab nav, footer.
import { useEffect, useState } from "react";
import type { StudioData } from "./data";
import { loadAll } from "./data";
import { fmtCompact, fmtDate } from "./format";
import Overview from "./screens/Overview";
import Videos from "./screens/Videos";
import Pillars from "./screens/Pillars";
import Refresh from "./screens/Refresh";
import Cadence from "./screens/Cadence";
import Brief from "./screens/Brief";

type Tab = "overview" | "videos" | "pillars" | "refresh" | "cadence" | "brief";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "videos", label: "Videos" },
  { id: "pillars", label: "Pillars" },
  { id: "refresh", label: "Refresh" },
  { id: "cadence", label: "Cadence" },
  { id: "brief", label: "Brief" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [data, setData] = useState<StudioData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAll()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            ▶
          </span>
          <div>
            <h1>Creator Analytics Studio</h1>
            <p className="tagline">
              {data ? (
                <>
                  {data.channel.channel.title} ·{" "}
                  <span className="num">{fmtCompact(data.channel.channel.subscriberCount)}</span>{" "}
                  subscribers · <span className="num">{data.videos.length}</span> videos · updated{" "}
                  {fmtDate(data.channel.computedAt)}
                </>
              ) : (
                "the content-portfolio audit for the solo YouTube creator"
              )}
            </p>
          </div>
          {data?.channel.channel.source === "sample" && (
            <span className="badge badge-amber" title="Illustrative data — connect YouTube for real numbers">
              Sample channel
            </span>
          )}
        </div>
        <nav className="tabs" aria-label="Studio views">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab${tab === t.id ? " active" : ""}`}
              aria-current={tab === t.id ? "page" : undefined}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">
        {error && (
          <div className="alert alert-error" role="alert">
            <strong>Couldn't load studio data.</strong> {error} Make sure channel.json,
            videos.json and brief.json exist in the app's public folder.
          </div>
        )}
        {!error && !data && <div className="card empty">Loading studio data…</div>}
        {data && tab === "overview" && <Overview brief={data.brief} />}
        {data && tab === "videos" && <Videos videos={data.videos} />}
        {data && tab === "pillars" && <Pillars brief={data.brief} />}
        {data && tab === "refresh" && <Refresh brief={data.brief} videos={data.videos} />}
        {data && tab === "cadence" && <Cadence brief={data.brief} />}
        {data && tab === "brief" && <Brief brief={data.brief} />}
      </main>

      <footer className="footer">
        Pillars are keyword-based, not semantic topic modeling. Decay velocities are modeled,
        not measured. Public API data excludes CTR/retention/revenue.
      </footer>
    </div>
  );
}
