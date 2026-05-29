import { useEffect, useState } from "react";
import { getSystemStatus } from "../api/status";
import type { SystemStatus } from "../types";

const overallConfig = {
  operational: { label: "All Systems Operational", color: "bg-green-500", text: "text-green-700", bg: "bg-green-50", border: "border-green-200" },
  partial_outage: { label: "Partial Outage", color: "bg-yellow-500", text: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200" },
  major_outage: { label: "Major Outage", color: "bg-red-500", text: "text-red-700", bg: "bg-red-50", border: "border-red-200" },
};

const statusColor: Record<string, string> = {
  UP: "bg-green-100 text-green-800",
  DOWN: "bg-red-100 text-red-800",
  DEGRADED: "bg-yellow-100 text-yellow-800",
  UNKNOWN: "bg-gray-100 text-gray-700",
};

const severityColor: Record<string, string> = {
  CRITICAL: "text-red-600",
  HIGH: "text-orange-500",
  MEDIUM: "text-yellow-600",
  LOW: "text-blue-500",
};

export default function StatusPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getSystemStatus().then(setStatus).catch(() => setError(true));
    const interval = setInterval(() => {
      getSystemStatus().then(setStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Could not load status. Please try again later.</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">Loading…</p>
      </div>
    );
  }

  const cfg = overallConfig[status.overall];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">StatusForge</h1>
          <p className="text-gray-500 mt-1 text-sm">System Status</p>
        </div>

        <div className={`rounded-xl p-6 border ${cfg.bg} ${cfg.border} flex items-center gap-4`}>
          <span className={`w-4 h-4 rounded-full ${cfg.color} shrink-0`} />
          <span className={`text-lg font-semibold ${cfg.text}`}>{cfg.label}</span>
          <span className="ml-auto text-xs text-gray-400">
            Updated {new Date(status.checked_at).toLocaleTimeString()}
          </span>
        </div>

        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Services</h2>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {status.services.length === 0 && (
              <p className="px-5 py-4 text-sm text-gray-500">No services configured.</p>
            )}
            {status.services.map((svc) => (
              <div key={svc.name} className="px-5 py-4 flex items-center justify-between">
                <span className="font-medium text-gray-800">{svc.name}</span>
                <div className="flex items-center gap-3">
                  {svc.last_checked_at && (
                    <span className="text-xs text-gray-400 hidden sm:block">
                      {new Date(svc.last_checked_at).toLocaleTimeString()}
                    </span>
                  )}
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor[svc.status] ?? "bg-gray-100 text-gray-700"}`}>
                    {svc.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {status.active_incidents.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Active Incidents</h2>
            <div className="space-y-3">
              {status.active_incidents.map((inc, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className={`text-xs font-semibold ${severityColor[inc.severity]}`}>{inc.severity}</p>
                      <p className="font-medium text-gray-800 mt-0.5">{inc.title}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        Since {new Date(inc.started_at).toLocaleString()}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                      inc.status === "ACKNOWLEDGED" ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800"
                    }`}>
                      {inc.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <p className="text-center text-xs text-gray-400">
          Powered by StatusForge · Auto-refreshes every 30 seconds
        </p>
      </div>
    </div>
  );
}
