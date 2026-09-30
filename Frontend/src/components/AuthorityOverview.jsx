import { lazy, Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ClientOnly, useNavigate } from "@tanstack/react-router";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { getHotspots, getChartData } from "@/services/api";
import { sortByRisk, riskBadgeClass, RISK_HEX } from "@/lib/risk";
import { useApp } from "@/context/AppContext";

const RiskMap = lazy(() => import("@/components/RiskMap"));

function MetricTile({ label, value, accent }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div
        className="mt-1 text-2xl font-bold text-navy"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
    </div>
  );
}

function Panel({ title, children, className = "" }) {
  return (
    <section className={`rounded-md border border-slate-200 bg-white ${className}`}>
      <div className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-navy">
        {title}
      </div>
      {children}
    </section>
  );
}

export default function AuthorityOverview() {
  const navigate = useNavigate();
  const charts = getChartData();
  const { cases } = useApp();
  const [selectedId, setSelectedId] = useState(null);
  const [riskFilter, setRiskFilter] = useState("ALL");

  // ── Async hotspot data from FastAPI backend ──────────────────────────────
  // refetchInterval keeps the map + cluster list live without a browser refresh.
  // Any new phone event processed by the backend will appear within ~3 seconds.
  const {
    data: fetchedHotspots = [],
    isLoading: hotspotsLoading,
    error: hotspotsError,
  } = useQuery({
    queryKey: ["hotspots"],
    queryFn: getHotspots,
    retry: 1,
    staleTime: 0,          // always re-validate from the server on each interval
    refetchInterval: 3000, // poll every 3 seconds for live map updates
  });

  const resolvedHotspotIds = new Set(
    cases.filter((c) => c.status === "RESOLVED").map((c) => c.hotspot_id),
  );
  const allHotspots = sortByRisk(fetchedHotspots).filter(
    (h) => !resolvedHotspotIds.has(h.id),
  );

  // Apply risk level filter
  const hotspots = riskFilter === "ALL" 
    ? allHotspots 
    : allHotspots.filter((h) => h.risk_level === riskFilter);

  const highRisk = allHotspots.filter((h) => h.risk_level === "HIGH").length;
  const events = allHotspots.reduce((s, h) => s + h.event_count, 0);
  const vehicleCount = allHotspots.reduce((s, h) => s + h.vehicle_count, 0);
  const openCases = cases.filter((c) =>
    ["NEW", "ASSIGNED", "IN_PROGRESS"].includes(c.status),
  ).length;

  const goCluster = (id) => navigate({ to: "/authority/cluster/$id", params: { id } });

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-5">
      <h1 className="sr-only">MargDrishti Authority Overview</h1>

      {/* ── Backend connection status banners ─────────────────────────────── */}
      {hotspotsLoading && (
        <div className="mb-4 rounded border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
          Loading live hotspot data from backend…
        </div>
      )}
      {hotspotsError && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          <strong>Backend unavailable:</strong> {hotspotsError.message}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <MetricTile label="High-Risk Hotspots" value={highRisk} accent={RISK_HEX.HIGH} />
        <MetricTile label="Active Clusters" value={hotspots.length} />
        <MetricTile label="Events Today" value={events} />
        <MetricTile label="Contributing Vehicles" value={vehicleCount} />
        <MetricTile label="Open Cases" value={openCases} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[65fr_35fr]">
        <Panel title="National Risk Map">
          <div className="h-[520px] w-full overflow-hidden rounded-b-md">
            <ClientOnly
              fallback={
                <div className="flex h-full items-center justify-center text-sm text-slate-500">
                  Loading map…
                </div>
              }
            >
              <Suspense
                fallback={
                  <div className="flex h-full items-center justify-center text-sm text-slate-500">
                    Loading map…
                  </div>
                }
              >
                <RiskMap
                  hotspots={hotspots}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
              </Suspense>
            </ClientOnly>
          </div>
        </Panel>

        <Panel title="Active Risk Clusters">
          {/* Risk Level Filter */}
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {["ALL", "HIGH", "MEDIUM", "LOW"].map((level) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => setRiskFilter(level)}
                    className={`rounded px-3 py-1.5 text-xs font-semibold transition-colors ${
                      riskFilter === level
                        ? level === "ALL"
                          ? "bg-navy text-white"
                          : level === "HIGH"
                          ? "bg-red-600 text-white"
                          : level === "MEDIUM"
                          ? "bg-orange-500 text-white"
                          : "bg-green-600 text-white"
                        : "border border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
              <div className="text-xs text-slate-500">
                {hotspots.length} {hotspots.length === 1 ? "cluster" : "clusters"}
              </div>
            </div>
          </div>

          <ul className="max-h-[455px] divide-y divide-slate-200 overflow-y-auto">
            {hotspots.map((h) => (
              <li key={h.id}>
                <button
                  type="button"
                  onClick={() => goCluster(h.id)}
                  onMouseEnter={() => setSelectedId(h.id)}
                  className={`w-full px-4 py-3 text-left transition-colors hover:bg-slate-50 ${
                    selectedId === h.id ? "bg-slate-50" : ""
                  }`}
                >
                  {/* Header row: name and badges */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-sm font-bold text-navy">{h.road_segment}</span>
                    <div className="flex items-center gap-1.5">
                      {h.possible_chain && (
                        <span className="rounded border border-orange-400 bg-orange-50 px-1.5 py-0.5 text-[10px] font-bold text-orange-700" title="Chain reaction detected">
                          ⚠️ CHAIN
                        </span>
                      )}
                      <span
                        className={`rounded border px-2 py-0.5 text-[11px] font-bold ${riskBadgeClass[h.risk_level]}`}
                      >
                        {h.risk_level}
                      </span>
                    </div>
                  </div>

                  {/* Location */}
                  <div className="text-xs text-slate-500 mb-2">
                    {h.location}
                  </div>

                  {/* Metrics row */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px] uppercase tracking-wide">Score</span>
                      <span className="font-bold tabular-nums" style={{ color: RISK_HEX[h.risk_level] }}>
                        {h.risk_score}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px] uppercase tracking-wide">Vehicles</span>
                      <span className="font-bold tabular-nums text-navy">
                        {h.vehicle_count}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-slate-400 text-[10px] uppercase tracking-wide">Events</span>
                      <span className="font-bold tabular-nums text-navy">
                        {h.event_count}
                      </span>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Panel title="Risk Events — Last 7 Days">
          <div className="h-56 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts.eventsOverTime}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="events"
                  stroke="#1a2744"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Event Types Today">
          <div className="h-56 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.eventTypes}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="type" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#1a2744" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Case Status">
          <div className="h-56 p-3">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.caseStatus}
                  dataKey="count"
                  nameKey="status"
                  innerRadius={38}
                  outerRadius={68}
                >
                  {charts.caseStatus.map((entry, i) => (
                    <Cell
                      key={entry.status}
                      fill={[RISK_HEX.HIGH, RISK_HEX.MEDIUM, RISK_HEX.LOW][i % 3]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend fontSize={12} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </main>
  );
}
