import { useQuery } from "@tanstack/react-query";
import { getOverview } from "../api/metrics";
import IncidentCard from "../components/IncidentCard";
import ServiceCard from "../components/ServiceCard";
import { useIncidents } from "../hooks/useIncidents";
import { useServices } from "../hooks/useServices";
import { useWebSocket } from "../hooks/useWebSocket";

const statCards = [
  { key: "total_services", label: "Total Services", bg: "bg-gray-50" },
  { key: "up", label: "Up", bg: "bg-green-50" },
  { key: "down", label: "Down", bg: "bg-red-50" },
  { key: "degraded", label: "Degraded", bg: "bg-yellow-50" },
  { key: "open_incidents", label: "Open Incidents", bg: "bg-orange-50" },
] as const;

export default function Dashboard() {
  useWebSocket();

  const { data: overview } = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  const { data: services = [] } = useServices();
  const { data: incidents = [] } = useIncidents();
  const open = incidents.filter((i) => i.status !== "RESOLVED");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {statCards.map(({ key, label, bg }) => (
            <div key={key} className={`${bg} rounded-lg p-4`}>
              <p className="text-sm text-gray-600">{label}</p>
              <p className="text-3xl font-bold text-gray-900">{overview[key]}</p>
            </div>
          ))}
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Services</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {services.map((s) => <ServiceCard key={s.id} service={s} />)}
        </div>
        {services.length === 0 && <p className="text-gray-500 text-sm">No services configured.</p>}
      </section>

      {open.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Open Incidents</h2>
          <div className="space-y-3">
            {open.map((i) => <IncidentCard key={i.id} incident={i} />)}
          </div>
        </section>
      )}
    </div>
  );
}
