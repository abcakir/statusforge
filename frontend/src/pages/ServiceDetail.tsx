import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { checkNow } from "../api/services";
import { getLatencySeries, getUptime } from "../api/metrics";
import LatencyChart from "../components/LatencyChart";
import StatusBadge from "../components/StatusBadge";
import { useWebSocket } from "../hooks/useWebSocket";
import { useService } from "../hooks/useServices";
import { useRealtimeStore } from "../stores/realtimeStore";

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  useWebSocket(id);

  const qc = useQueryClient();
  const lastMessage = useRealtimeStore((s) => s.lastMessage);

  useEffect(() => {
    if (lastMessage?.type === "service_update" && lastMessage.service_id === id) {
      qc.invalidateQueries({ queryKey: ["services", id] });
      qc.invalidateQueries({ queryKey: ["latency", id] });
      qc.invalidateQueries({ queryKey: ["uptime", id] });
    }
  }, [lastMessage, id, qc]);

  const { data: service } = useService(id!);
  const { data: latency = [] } = useQuery({ queryKey: ["latency", id], queryFn: () => getLatencySeries(id!), enabled: !!id });
  const { data: uptime } = useQuery({ queryKey: ["uptime", id], queryFn: () => getUptime(id!), enabled: !!id });
  const check = useMutation({ mutationFn: () => checkNow(id!) });

  if (!service) return <div className="text-gray-500">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{service.name}</h1>
          <p className="text-gray-500 text-sm">{service.url}</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={service.status} />
          <button onClick={() => check.mutate()} disabled={check.isPending} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50">
            {check.isPending ? "Queued" : "Check Now"}
          </button>
        </div>
      </div>

      {uptime && (
        <div className="bg-white rounded-lg shadow p-5">
          <h2 className="font-semibold text-gray-800 mb-1">30-day Uptime</h2>
          <p className="text-3xl font-bold text-green-600">{uptime.uptime_percent !== null ? `${uptime.uptime_percent}%` : "N/A"}</p>
          <p className="text-xs text-gray-500 mt-1">{uptime.total_checks} total checks</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold text-gray-800 mb-4">Latency (24h)</h2>
        {latency.length > 0 ? <LatencyChart data={latency} /> : <p className="text-sm text-gray-500">No data yet</p>}
      </div>

      <div className="bg-white rounded-lg shadow p-5 text-sm text-gray-600 space-y-1">
        <p><span className="font-medium">Check interval:</span> {service.check_interval}s</p>
        <p><span className="font-medium">Timeout:</span> {service.timeout}s</p>
        <p><span className="font-medium">Active:</span> {service.is_active ? "Yes" : "No"}</p>
        <p><span className="font-medium">Consecutive failures:</span> {service.consecutive_failures}</p>
      </div>
    </div>
  );
}
