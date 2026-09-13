import { useEffect, useRef, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
// @ts-expect-error - JS module
import { useApp } from "@/context/AppContext";

export const Route = createFileRoute("/driver")({
  head: () => ({
    meta: [
      { title: "Driver Alerts — MargDrishti" },
      {
        name: "description",
        content: "In-vehicle road risk alerts for upcoming high-risk highway segments.",
      },
      { property: "og:title", content: "Driver Alerts — MargDrishti" },
      {
        property: "og:description",
        content: "Live road risk status for drivers on Indian highways.",
      },
    ],
  }),
  component: DriverPage,
});

type AlertState = "CLEAR" | "CAUTION" | "HIGH_RISK";

type TabKey = "hazard" | "reroute";

const STATES: Record<
  AlertState,
  {
    surface: string;
    icon: string;
    pulse: boolean;
    heading: string;
    headingColor: string;
    subtext?: string;
    distance?: string;
    pill?: { label: string; className: string };
    action?: string;
    actionColor?: string;
    direction?: string;
    road?: string;
  }
> = {
  CLEAR: {
    surface: "driver-surface-clear",
    icon: "driver-dot-clear",
    pulse: false,
    heading: "ROAD CLEAR",
    headingColor: "text-driver-clear",
    subtext: "No hazards detected on your route.",
  },
  CAUTION: {
    surface: "driver-surface-caution",
    icon: "driver-dot-caution",
    pulse: false,
    heading: "CAUTION AHEAD",
    headingColor: "text-driver-caution",
    distance: "500 m",
    pill: { label: "MODERATE RISK", className: "driver-pill-caution" },
    action: "SLOW DOWN",
    actionColor: "text-driver-caution",
    direction: "→ AHEAD",
  },
  HIGH_RISK: {
    surface: "driver-surface-danger",
    icon: "driver-dot-danger",
    pulse: true,
    heading: "ROAD HAZARD AHEAD",
    headingColor: "text-driver-danger",
    distance: "300 m",
    pill: { label: "HIGH RISK", className: "driver-pill-danger" },
    action: "REDUCE SPEED IMMEDIATELY",
    actionColor: "text-driver-danger",
    direction: "→ AHEAD",
    road: "NH-48 · Gurugram, Haryana",
  },
};

function DriverPage() {
  const { driverAlertState, setDriverAlert } = useApp();
  const [activeTab, setActiveTab] = useState<TabKey>("hazard");
  const [RerouteMap, setRerouteMap] = useState<any>(null);
  const state: AlertState = (
    ["CLEAR", "CAUTION", "HIGH_RISK"].includes(driverAlertState)
      ? driverAlertState
      : "CLEAR"
  ) as AlertState;
  const view = STATES[state];

  useEffect(() => {
    let active = true;
    // @ts-expect-error - JSX component without declaration file
    import("@/components/DriverRerouteMap").then((mod) => {
      if (active) setRerouteMap(() => mod.default);
    });
    return () => {
      active = false;
    };
  }, []);

  const prevState = useRef<AlertState | null>(null);
  useEffect(() => {
    if (prevState.current === state) return;
    const previous = prevState.current;
    prevState.current = state;
    if (previous === null) return;
    if (state === "CLEAR") return;

    type AudioCtor = typeof AudioContext;
    const Ctx: AudioCtor | undefined =
      typeof window === "undefined"
        ? undefined
        : window.AudioContext ??
          (window as unknown as { webkitAudioContext?: AudioCtor }).webkitAudioContext;
    if (!Ctx) return;

    const ctx = new Ctx();
    const beep = (freq: number, start: number, duration: number) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      const t = ctx.currentTime + start;
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(0.25, t + 0.02);
      gain.gain.linearRampToValueAtTime(0, t + duration);
      osc.connect(gain).connect(ctx.destination);
      osc.start(t);
      osc.stop(t + duration + 0.02);
    };

    if (state === "CAUTION") {
      beep(700, 0, 0.4);
    } else {
      beep(1100, 0, 0.3);
      beep(1100, 0.45, 0.3);
      beep(1100, 0.9, 0.3);
    }

    const timer = window.setTimeout(() => void ctx.close(), 2000);
    return () => {
      window.clearTimeout(timer);
    };
  }, [state]);

  return (
    <div
      className={`relative flex min-h-screen flex-col px-6 py-20 text-center ${view.surface}`}
    >
      <Link
        to="/authority"
        className="absolute left-4 top-4 text-xs font-medium text-muted-foreground hover:underline"
      >
        ← Authority Portal
      </Link>

      <div className="mt-10 flex justify-center">
        <div className="inline-flex items-center rounded-full bg-white/70 p-1 shadow-sm backdrop-blur-sm">
          <button
            type="button"
            onClick={() => setActiveTab("hazard")}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
              activeTab === "hazard"
                ? "bg-navy text-white shadow-sm"
                : "bg-white text-navy hover:bg-white/80"
            }`}
          >
            ⚠️ Hazard Alert
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("reroute")}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
              activeTab === "reroute"
                ? "bg-navy text-white shadow-sm"
                : "bg-white text-navy hover:bg-white/80"
            }`}
          >
            🗺️ Reroute
          </button>
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto">
        {activeTab === "hazard" ? (
          <div className="flex flex-1 flex-col items-center justify-center pb-28">
            <div
              className={`driver-dot ${view.icon} ${view.pulse ? "driver-pulse" : ""}`}
              aria-hidden="true"
            />

            <h1
              className={`mt-6 text-3xl font-extrabold tracking-tight sm:text-5xl ${view.headingColor}`}
            >
              {view.heading}
            </h1>

            {view.subtext ? (
              <p className="mt-4 max-w-sm text-lg font-medium text-muted-foreground sm:text-xl">
                {view.subtext}
              </p>
            ) : null}

            {view.distance ? (
              <div className="mt-6 text-6xl font-black tracking-tight text-foreground sm:text-7xl">
                {view.distance}
              </div>
            ) : null}

            {view.pill ? (
              <span
                className={`mt-5 inline-flex items-center rounded-full px-4 py-1.5 text-sm font-bold tracking-wide ${view.pill.className}`}
              >
                {view.pill.label}
              </span>
            ) : null}

            {view.action ? (
              <p
                className={`mt-6 text-2xl font-bold uppercase tracking-wide sm:text-3xl ${view.actionColor}`}
              >
                {view.action}
              </p>
            ) : null}

            {view.direction ? (
              <p className="mt-3 text-xl font-bold text-foreground sm:text-2xl">
                {view.direction}
              </p>
            ) : null}

            {view.road ? (
              <p className="mt-4 text-base font-semibold text-muted-foreground">
                {view.road}
              </p>
            ) : null}
          </div>
        ) : (
          <ReroutePanel state={state} RerouteMap={RerouteMap} />
        )}
      </div>

      <div className="fixed inset-x-0 bottom-0 flex flex-col items-center gap-2 pb-4">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground/70">
          Demo Controls
        </span>
        <div className="flex gap-2">
          {(
            [
              ["Clear", "CLEAR"],
              ["Caution", "CAUTION"],
              ["High Risk", "HIGH_RISK"],
            ] as const
          ).map(([label, value]) => (
            <button
              key={value}
              type="button"
              onClick={() => setDriverAlert(value)}
              className="rounded-md border border-border bg-background/70 px-3 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReroutePanel({
  state,
  RerouteMap,
}: {
  state: AlertState;
  RerouteMap: any;
}) {
  if (state === "CLEAR") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-28">
        <p className="text-lg font-medium text-muted-foreground">
          No rerouting needed. Road is clear ahead.
        </p>
      </div>
    );
  }

  return (
    <div className="flex w-full flex-1 flex-col items-center gap-4 pb-28 pt-6">
      <div className="w-full max-w-md rounded-lg border border-border bg-white/80 p-3 text-sm font-medium text-foreground shadow-sm backdrop-blur-sm">
        ⚠️ Road disruption detected on NH-48 ahead. Alternate route suggested.
      </div>

      <div className="h-[220px] w-full max-w-md overflow-hidden rounded-lg border border-border shadow-sm">
        {RerouteMap ? (
          <RerouteMap />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-muted text-xs text-muted-foreground">
            Loading map…
          </div>
        )}
      </div>

      <div className="w-full max-w-md rounded-lg border border-border bg-white/80 p-4 text-left shadow-sm backdrop-blur-sm">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-base font-bold text-foreground">Via Manesar Bypass</p>
            <p className="mt-1 text-sm text-muted-foreground">
              +4 min additional · Saves approx. 20 min of jam
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-risk-low/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-risk-low">
            Recommended Route
          </span>
        </div>
        <p className="mt-3 text-sm font-semibold text-navy">
          Turn LEFT in 500m onto Sector 37 Road
        </p>
      </div>
    </div>
  );
}
