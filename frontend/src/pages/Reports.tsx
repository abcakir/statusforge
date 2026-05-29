import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSLAReport } from "../api/reports";
import type { ServiceSLAReport } from "../types";

const DAYS_OPTIONS = [
  { label: "Last 7 days", value: 7 },
  { label: "Last 30 days", value: 30 },
  { label: "Last 90 days", value: 90 },
];

function uptimeColor(pct: number | null): string {
  if (pct === null) return "text-gray-400";
  if (pct >= 99.9) return "text-green-600";
  if (pct >= 95) return "text-yellow-600";
  return "text-red-600";
}

function exportCSV(data: ServiceSLAReport[], days: number) {
  const headers = ["Service", "URL", "Uptime %", "Avg Latency (ms)", "Total Checks", "Incidents", "Downtime (min)"];
  const rows = data.map((r) => [
    r.service_name,
    r.url,
    r.uptime_percent ?? "N/A",
    r.avg_latency_ms ?? "N/A",
    r.total_checks,
    r.incident_count,
    r.total_downtime_minutes,
  ]);
  const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sla-report-${days}d.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const [days, setDays] = useState(30);
  const { data: report = [], isLoading } = useQuery({
    queryKey: ["sla", days],
    queryFn: () => getSLAReport(days),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-900">SLA Reports</h1>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {DAYS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDays(opt.value)}
                className={`px-4 py-2 text-sm ${days === opt.value ? "bg-blue-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {report.length > 0 && (
            <button
              onClick={() => exportCSV(report, days)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-2"
            >
              Export CSV
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : report.length === 0 ? (
        <p className="text-gray-500 text-sm">No services found.</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left border-b border-gray-200">
                <tr>
                  {["Service", "Uptime", "Avg Latency", "Checks", "Incidents", "Downtime"].map((h) => (
                    <th key={h} className="px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {report.map((row) => (
                  <tr key={row.service_id} className="hover:bg-gray-50">
                    <td className="px-5 py-4">
                      <p className="font-medium text-gray-900">{row.service_name}</p>
                      <p className="text-xs text-gray-400 truncate max-w-xs">{row.url}</p>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-base font-semibold ${uptimeColor(row.uptime_percent)}`}>
                        {row.uptime_percent !== null ? `${row.uptime_percent}%` : "N/A"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-700">
                      {row.avg_latency_ms !== null ? `${row.avg_latency_ms} ms` : "N/A"}
                    </td>
                    <td className="px-5 py-4 text-gray-700">{row.total_checks.toLocaleString()}</td>
                    <td className="px-5 py-4">
                      <span className={`font-medium ${row.incident_count > 0 ? "text-red-600" : "text-gray-700"}`}>
                        {row.incident_count}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-700">
                      {row.total_downtime_minutes > 0 ? `${row.total_downtime_minutes} min` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
