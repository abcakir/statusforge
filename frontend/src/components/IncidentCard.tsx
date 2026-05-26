import type { Incident } from "../types";
import StatusBadge from "./StatusBadge";

const borderColor: Record<string, string> = {
  CRITICAL: "border-l-red-500",
  HIGH: "border-l-orange-500",
  MEDIUM: "border-l-yellow-500",
  LOW: "border-l-blue-500",
};

export default function IncidentCard({ incident }: { incident: Incident }) {
  return (
    <div className={`bg-white rounded-lg shadow p-5 border-l-4 ${borderColor[incident.severity] ?? "border-l-gray-400"}`}>
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-gray-900">{incident.title}</h3>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-500 font-medium">{incident.severity}</span>
          <StatusBadge status={incident.status} />
        </div>
      </div>
      <p className="text-sm text-gray-500 mt-1">Started: {new Date(incident.started_at).toLocaleString()}</p>
      {incident.resolved_at && (
        <p className="text-sm text-gray-500">Resolved: {new Date(incident.resolved_at).toLocaleString()}</p>
      )}
    </div>
  );
}
