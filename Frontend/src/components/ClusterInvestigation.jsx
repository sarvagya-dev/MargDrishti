import { lazy, Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ClientOnly, Link } from "@tanstack/react-router";
import { getHotspotDetails } from "@/services/api";
import { useApp } from "@/context/AppContext";
import { riskBadgeClass, RISK_HEX } from "@/lib/risk";

const ClusterMap = lazy(() => import("@/components/ClusterMap"));

function minutesOf(t) {
  const [h, m] = String(t).split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

function Panel({ title, children, className = "" }) {
  return (
    <section className={`rounded-md border border-slate-200 bg-white p-5 ${className}`}>
      {title ? (
        <h2 className="mb-4 text-sm font-bold tracking-wide text-navy uppercase">{title}</h2>
      ) : null}
      {children}
    </section>
  );
}

function Detail({ label, value }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 py-2 text-sm last:border-0">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-navy">{value}</span>
    </div>
  );
}

function EventPill({ children }) {
  return (
    <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[11px] font-medium text-slate-600">
      {children}
    </span>
  );
}

export default function ClusterInvestigation({ id }) {
  // ── Async hotspot + event data from FastAPI backend ──────────────────────────
  const {
    data: hotspot,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["hotspot", id],
    queryFn: () => getHotspotDetails(id),
    retry: 1,
    staleTime: 30_000,
  });

  const { addCase } = useApp();
  const [createdCase, setCreatedCase] = useState(null);
  const [evidence, setEvidence] = useState(null);

  // ── Loading state ─────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <main className="mx-auto max-w-[1600px] px-5 py-10 text-slate-600">
        <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          Loading cluster data from backend…
        </div>
      </main>
    );
  }

  // ── Error state ───────────────────────────────────────────────────────────────
  if (error) {
    return (
      <main className="mx-auto max-w-[1600px] px-5 py-10 text-slate-600">
        <Link
          to="/authority"
          className="mb-4 inline-block rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-navy hover:bg-slate-50"
        >
          ← Overview
        </Link>
        <div className="mt-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <strong>Backend unavailable:</strong> {error.message}
        </div>
      </main>
    );
  }

  // ── Not found (hotspot_id not in backend) ─────────────────────────────────────
  if (!hotspot) {
    return (
      <main className="mx-auto max-w-[1600px] px-5 py-10 text-slate-600">
        No cluster found for {id}.
      </main>
    );
  }

  const vehicleList = hotspot.vehicles ?? [];
  const times = vehicleList.map((v) => minutesOf(v.timestamp));
  const min = Math.min(...times);
  const max = Math.max(...times);
  const span = max - min || 1;

  // Confidence: derived as mean of contributing event confidences in api.js.
  // null when no events were found (backend returned no nearby events).
  const confidenceDisplay =
    hotspot.confidence != null ? `${Math.round(hotspot.confidence * 100)}%` : "—";

  function handleCreateCase() {
    const created = addCase(hotspot.id);
    setCreatedCase(created);
  }

  function handleExport() {
    const blob = new Blob(
      [
        JSON.stringify(
          { cluster_id: hotspot.id, road_segment: hotspot.road_segment, vehicles: vehicleList },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${hotspot.id}-evidence.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-6">
      <div className="mb-5 flex flex-wrap items-center gap-4">
        <Link
          to="/authority"
          className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-navy hover:bg-slate-50"
        >
          ← Overview
        </Link>
        <h1 className="text-xl font-bold text-navy">
          {hotspot.id} · {hotspot.road_segment}
        </h1>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_400px]">
        {/* LEFT */}
        <div className="space-y-5">
          <Panel title="Risk Summary">
            <div className="flex flex-wrap items-end gap-8">
              <div>
                <div
                  className="text-5xl font-bold leading-none"
                  style={{ color: RISK_HEX[hotspot.risk_level] }}
                >
                  {hotspot.risk_score}
                </div>
                <div className="mt-1 text-xs text-slate-500">Risk Score</div>
              </div>
              <div>
                <span
                  className={`rounded border px-2.5 py-1 text-xs font-bold ${riskBadgeClass[hotspot.risk_level]}`}
                >
                  {hotspot.risk_level}
                </span>
                <div className="mt-1 text-xs text-slate-500">Risk Level</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-navy">{confidenceDisplay}</div>
                <div className="mt-1 text-xs text-slate-500">Avg. Event Confidence</div>
              </div>
            </div>
          </Panel>

          <Panel title="Location Details">
            <Detail label="Cluster ID" value={hotspot.id} />
            <Detail label="Centroid" value={hotspot.location} />
            <Detail label="Direction" value={hotspot.direction} />
            <Detail label="First Observed" value={hotspot.first_observed.replace("T", " ")} />
            <Detail label="Last Observed" value={hotspot.last_observed.replace("T", " ")} />
          </Panel>

          <Panel title="Collective Vehicle Intelligence">
            <p className="text-sm text-slate-600">
              {vehicleList.length} independent vehicles reported abnormal behaviour on the same
              road segment.
            </p>
            <ul className="mt-4 grid gap-2 sm:grid-cols-2">
              {[
                "Same road segment",
                "Same direction",
                "Compatible time window",
                "Multiple event types",
              ].map((c) => (
                <li key={c} className="flex items-center gap-2 text-sm text-slate-700">
                  <span className="font-bold text-risk-low">✓</span>
                  {c}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Contributing Vehicles">
            {vehicleList.length === 0 ? (
              <p className="text-sm text-slate-500">No events found near this hotspot.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {vehicleList.map((v) => (
                  <div key={`${v.id}-${v.event_id}`} className="flex items-center justify-between gap-3 py-2.5">
                    <span className="text-sm font-semibold text-navy">{v.id}</span>
                    <EventPill>{v.event_type}</EventPill>
                    <span className="text-sm tabular-nums text-slate-500">{v.timestamp}</span>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Event Timeline">
            <div className="relative mt-6 mb-2 h-24 px-6">
              <div className="absolute top-12 right-6 left-6 h-0.5 bg-slate-200" />
              {vehicleList.map((v) => {
                const pct = ((minutesOf(v.timestamp) - min) / span) * 100;
                return (
                  <div
                    key={`${v.id}-${v.event_id}`}
                    className="absolute top-0 flex w-24 -translate-x-1/2 flex-col items-center"
                    style={{ left: `calc(24px + (100% - 48px) * ${pct / 100})` }}
                  >
                    <span className="text-[11px] font-medium tabular-nums text-slate-500">
                      {v.timestamp}
                    </span>
                    <span
                      className="mt-2 h-3.5 w-3.5 rounded-full border-2 border-white ring-2"
                      style={{
                        backgroundColor: RISK_HEX[hotspot.risk_level],
                        boxShadow: "0 0 0 2px #fff",
                      }}
                    />
                    <span className="mt-2 text-[11px] font-semibold text-navy">{v.id}</span>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>

        {/* RIGHT */}
        <div className="space-y-5">
          <div className="h-64 overflow-hidden rounded-md border border-slate-200 bg-white">
            <ClientOnly
              fallback={
                <div className="flex h-full items-center justify-center text-sm text-slate-400">
                  Loading map…
                </div>
              }
            >
              <ClusterMap hotspot={hotspot} />
            </ClientOnly>
          </div>

          <Panel title="Evidence">
            <div className="space-y-3">
              {vehicleList.map((v) => (
                <div key={`${v.id}-${v.event_id}`} className="rounded border border-slate-200 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-navy">{v.id}</span>
                    <span className="text-xs tabular-nums text-slate-500">{v.timestamp}</span>
                  </div>
                  <div className="mt-1.5">
                    <EventPill>{v.event_type}</EventPill>
                  </div>
                  {/* Show button only when backend evidence exists for this event */}
                  {v.evidence && v.evidence.length > 0 ? (
                    <button
                      type="button"
                      onClick={() => setEvidence(v)}
                      className="mt-3 w-full rounded bg-navy px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90"
                    >
                      ▶ View Evidence ({v.evidence.length} clip{v.evidence.length !== 1 ? "s" : ""})
                    </button>
                  ) : (
                    <p className="mt-3 text-center text-[11px] text-slate-400">
                      No evidence recorded
                    </p>
                  )}
                </div>
              ))}
              {vehicleList.length === 0 && (
                <p className="text-sm text-slate-500">No events found near this hotspot.</p>
              )}
            </div>
          </Panel>

          <Panel title="Authority Actions">
            <div className="space-y-3">
              <div>
                <button
                  type="button"
                  onClick={handleCreateCase}
                  disabled={!!createdCase}
                  className="w-full rounded bg-navy px-3 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Create Authority Case
                </button>
                {createdCase ? (
                  <p className="mt-1.5 text-xs font-medium text-risk-low">
                    Case {createdCase.id} created
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={handleExport}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm font-semibold text-navy hover:bg-slate-50"
              >
                View / Export Evidence
              </button>
            </div>
          </Panel>
        </div>
      </div>

      {/* ── Evidence modal — uses real backend video URLs ─────────────────────── */}
      {evidence ? (
        <div
          className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-900/50 p-4"
          onClick={() => setEvidence(null)}
        >
          <div
            className="w-full max-w-2xl rounded-md border border-slate-200 bg-white p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-start justify-between gap-4">
              <h3 className="text-base font-bold text-navy">
                {evidence.id} · {evidence.event_type}
              </h3>
              <button
                type="button"
                aria-label="Close"
                onClick={() => setEvidence(null)}
                className="rounded px-2 text-lg leading-none text-slate-500 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {/* ── Video player: streams from backend evidence endpoint ─────────── */}
            {evidence.evidence && evidence.evidence.length > 0 ? (
              evidence.evidence.map((clip) => (
                <video
                  key={clip.id}
                  controls
                  autoPlay
                  className="w-full rounded bg-slate-900"
                  src={clip.url}
                />
              ))
            ) : (
              <div className="flex h-40 items-center justify-center rounded bg-slate-900 text-sm text-slate-400">
                No evidence clips recorded for this event.
              </div>
            )}

            <p className="mt-2 text-xs text-slate-500">
              Recorded {evidence.full_timestamp ?? evidence.timestamp} · {hotspot.location}
            </p>
          </div>
        </div>
      ) : null}
    </main>
  );
}
