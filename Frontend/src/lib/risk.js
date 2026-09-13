export const RISK_HEX = {
  HIGH: "#dc2626",
  MEDIUM: "#d97706",
  LOW: "#16a34a",
};

export const RISK_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export function sortByRisk(list) {
  return [...list].sort(
    (a, b) =>
      RISK_ORDER[a.risk_level] - RISK_ORDER[b.risk_level] || b.risk_score - a.risk_score,
  );
}

export const riskBadgeClass = {
  HIGH: "bg-risk-high/10 text-risk-high border-risk-high/30",
  MEDIUM: "bg-risk-medium/10 text-risk-medium border-risk-medium/30",
  LOW: "bg-risk-low/10 text-risk-low border-risk-low/30",
};

export const statusBadgeClass = {
  NEW: "bg-slate-100 text-slate-700 border-slate-300",
  ASSIGNED: "bg-blue-50 text-blue-700 border-blue-200",
  IN_PROGRESS: "bg-amber-50 text-amber-700 border-amber-200",
  RESOLVED: "bg-green-50 text-green-700 border-green-200",
};

export function formatStatus(status) {
  return status.replace(/_/g, " ");
}
