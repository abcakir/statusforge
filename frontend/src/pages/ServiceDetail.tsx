import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { checkNow } from "../api/services";
import { getLatencySeries, getUptime } from "../api/metrics";
import LatencyChart from "../components/LatencyChart";
import StatusBadge from "../components/StatusBadge";
import { useWebSocket } from "../hooks/useWebSocket";
import { useService, useUpdateService, useDeleteService } from "../hooks/useServices";
import { useRealtimeStore } from "../stores/realtimeStore";

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  useWebSocket(id);

  const qc = useQueryClient();
  const lastMessage = useRealtimeStore((s) => s.lastMessage);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", description: "", check_interval: "60", timeout: "10" });

  const { data: service } = useService(id!);
  const { data: latency = [] } = useQuery({ queryKey: ["latency", id], queryFn: () => getLatencySeries(id!), enabled: !!id });
  const { data: uptime } = useQuery({ queryKey: ["uptime", id], queryFn: () => getUptime(id!), enabled: !!id });
  const check = useMutation({ mutationFn: () => checkNow(id!) });
  const update = useUpdateService();
  const remove = useDeleteService();

  useEffect(() => {
    if (lastMessage?.type === "service_update" && lastMessage.service_id === id) {
      qc.invalidateQueries({ queryKey: ["services", id] });
      qc.invalidateQueries({ queryKey: ["latency", id] });
      qc.invalidateQueries({ queryKey: ["uptime", id] });
    }
  }, [lastMessage, id, qc]);

  useEffect(() => {
    if (service && !editing) {
      setForm({
        name: service.name,
        url: service.url,
        description: service.description ?? "",
        check_interval: String(service.check_interval),
        timeout: String(service.timeout),
      });
    }
  }, [service, editing]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await update.mutateAsync({
      id: id!,
      data: {
        name: form.name,
        url: form.url,
        description: form.description || null,
        check_interval: Number(form.check_interval) || 60,
        timeout: Number(form.timeout) || 10,
      },
    });
    setEditing(false);
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

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
          <button onClick={() => setEditing((e) => !e)} className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50">
            {editing ? "Cancel" : "Edit"}
          </button>
          <button
            onClick={() => {
              if (confirm(`Service "${service.name}" wirklich löschen?`)) {
                remove.mutate(id!, { onSuccess: () => navigate("/services") });
              }
            }}
            className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>

      {editing && (
        <form onSubmit={handleSave} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">Edit Service</h2>
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Name" value={form.name} onChange={set("name")} required />
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="URL" value={form.url} onChange={set("url")} required />
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Description (optional)" value={form.description} onChange={set("description")} />
          <div className="grid grid-cols-2 gap-4">
            <input type="number" className="w-full border rounded px-3 py-2 text-sm" placeholder="Check interval (s)" value={form.check_interval} onChange={set("check_interval")} min={10} />
            <input type="number" className="w-full border rounded px-3 py-2 text-sm" placeholder="Timeout (s)" value={form.timeout} onChange={set("timeout")} min={1} />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={update.isPending} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50">
              {update.isPending ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setEditing(false)} className="px-4 py-2 border rounded-md text-sm hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      )}

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
