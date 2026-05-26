import StatusBadge from "../components/StatusBadge";
import { useAcknowledgeIncident, useIncidents, useResolveIncident } from "../hooks/useIncidents";

export default function Incidents() {
  const { data: incidents = [] } = useIncidents();
  const acknowledge = useAcknowledgeIncident();
  const resolve = useResolveIncident();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>

      <div className="space-y-4">
        {incidents.map((incident) => (
          <div key={incident.id} className="bg-white rounded-lg shadow p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold text-gray-900">{incident.title}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500 font-medium">{incident.severity}</span>
                  <StatusBadge status={incident.status} />
                </div>
                <p className="text-sm text-gray-500 mt-1">Started: {new Date(incident.started_at).toLocaleString()}</p>
                {incident.resolved_at && (
                  <p className="text-sm text-gray-500">Resolved: {new Date(incident.resolved_at).toLocaleString()}</p>
                )}
              </div>
              {incident.status !== "RESOLVED" && (
                <div className="flex gap-2 shrink-0">
                  {incident.status === "OPEN" && (
                    <button onClick={() => acknowledge.mutate(incident.id)} className="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600">
                      Acknowledge
                    </button>
                  )}
                  <button onClick={() => resolve.mutate(incident.id)} className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                    Resolve
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {incidents.length === 0 && <p className="text-center text-gray-500 py-12">No incidents</p>}
      </div>
    </div>
  );
}
