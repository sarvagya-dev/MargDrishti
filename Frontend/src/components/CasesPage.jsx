import { useApp } from "@/context/AppContext";
import { riskBadgeClass, statusBadgeClass, formatStatus } from "@/lib/risk";

const STATUS_OPTIONS = ["NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"];

export default function CasesPage() {
  const { cases, updateCase } = useApp();

  const total = cases.length;
  const newCount = cases.filter((c) => c.status === "NEW").length;
  const inProgressCount = cases.filter((c) => c.status === "IN_PROGRESS").length;
  const resolvedCount = cases.filter((c) => c.status === "RESOLVED").length;

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-navy">Authority Cases</h1>
        <p className="mt-1 text-sm text-slate-500">
          Manage and track road risk cases.
        </p>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryTile label="Total Cases" value={total} />
        <SummaryTile label="New" value={newCount} />
        <SummaryTile label="In Progress" value={inProgressCount} />
        <SummaryTile label="Resolved" value={resolvedCount} />
      </div>

      <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2.5">Case ID</th>
                <th className="px-4 py-2.5">Road Segment</th>
                <th className="px-4 py-2.5">Location</th>
                <th className="px-4 py-2.5">Risk Level</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Assigned To</th>
                <th className="px-4 py-2.5">Created</th>
                <th className="px-4 py-2.5">Change Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-semibold text-navy">{c.id}</td>
                  <td className="px-4 py-2.5 text-slate-700">{c.road_segment}</td>
                  <td className="px-4 py-2.5 text-slate-600">{c.location}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded border px-2 py-0.5 text-[11px] font-bold ${riskBadgeClass[c.risk_level]}`}
                    >
                      {c.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded border px-2 py-0.5 text-[11px] font-bold ${statusBadgeClass[c.status]}`}
                    >
                      {formatStatus(c.status)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">{c.assigned_to}</td>
                  <td className="px-4 py-2.5 text-slate-600">{formatDate(c.created_at)}</td>
                  <td className="px-4 py-2.5">
                    <select
                      aria-label={`Change status for ${c.id}`}
                      value={c.status}
                      onChange={(e) => updateCase(c.id, e.target.value)}
                      className="rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>
                          {formatStatus(status)}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

function SummaryTile({ label, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-navy">{value}</p>
    </div>
  );
}
