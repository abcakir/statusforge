import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { checkNow } from "../api/services";
import { getLatencySeries, getUptime } from "../api/metrics";
import { useAuth } from "../auth/AuthProvider";
import LatencyChart from "../components/LatencyChart";
import StatusBadge from "../components/StatusBadge";
import { useWebSocket } from "../hooks/useWebSocket";
import { useService, useUpdateService, useDeleteService } from "../hooks/useServices";
import { useRealtimeStore } from "../stores/realtimeStore";

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const canEdit = user?.role === "ADMIN" || user?.role === "OPERATOR";
  const canDelete = user?.role === "ADMIN";
  useWebSocket(id);

  const qc = useQueryClient();
  const lastMessage = useRealtimeStore((s) => s.lastMessage);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", description: "", check_interval: "60", timeout: "10", is_active: true, failure_threshold: "2", latency_threshold_ms: "2000", incident_severity: "CRITICAL" });

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
        is_active: service.is_active,
        failure_threshold: String(service.failure_threshold),
        latency_threshold_ms: String(service.latency_threshold_ms),
        incident_severity: service.incident_severity,
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
        is_active: form.is_active,
        failure_threshold: Number(form.failure_threshold) || 2,
        latency_threshold_ms: Number(form.latency_threshold_ms) || 2000,
        incident_severity: form.incident_severity,
      },
    });
    setEditing(false);
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
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
          {canEdit && (
            <button onClick={() => check.mutate()} disabled={check.isPending} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50">
              {check.isPending ? "Queued" : "Check Now"}
            </button>
          )}
          {canEdit && (
            <button onClick={() => setEditing((e) => !e)} className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50">
              {editing ? "Cancel" : "Edit"}
            </button>
          )}
          {canDelete && (
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
          )}
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
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              onClick={() => setForm((f) => ({ ...f, is_active: !f.is_active }))}
              className={`relative w-10 h-6 rounded-full transition-colors ${form.is_active ? "bg-blue-600" : "bg-gray-300"}`}
            >
              <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.is_active ? "translate-x-5" : "translate-x-1"}`} />
            </div>
            <span className="text-sm text-gray-700">Active (monitoring enabled)</span>
          </label>

          <div className="border-t pt-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Alert Rules</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Failures until DOWN</label>
                <input type="number" className="w-full border rounded px-3 py-2 text-sm" value={form.failure_threshold} onChange={set("failure_threshold")} min={1} max={10} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Latency threshold (ms)</label>
                <input type="number" className="w-full border rounded px-3 py-2 text-sm" value={form.latency_threshold_ms} onChange={set("latency_threshold_ms")} min={100} />
              </div>
            </div>
            <div className="mt-3">
              <label className="text-xs text-gray-500 mb-1 block">Incident severity</label>
              <select className="w-full border rounded px-3 py-2 text-sm" value={form.incident_severity} onChange={set("incident_severity")}>
                {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
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
        <p><span className="font-medium">Failure threshold:</span> {service.failure_threshold}</p>
        <p><span className="font-medium">Latency threshold:</span> {service.latency_threshold_ms} ms</p>
        <p><span className="font-medium">Incident severity:</span> {service.incident_severity}</p>
      </div>

      {service.url.startsWith("https://") && (
        <div className={`rounded-lg shadow p-5 text-sm ${
          service.ssl_days_remaining === null ? "bg-white text-gray-500" :
          service.ssl_days_remaining <= 7 ? "bg-red-50 border border-red-200" :
          service.ssl_days_remaining <= 30 ? "bg-yellow-50 border border-yellow-200" :
          "bg-green-50 border border-green-200"
        }`}>
          <h2 className="font-semibold text-gray-800 mb-2">SSL Certificate</h2>
          {service.ssl_expires_at === null ? (
            <p className="text-gray-400">Not checked yet — will run within the next hour.</p>
          ) : service.ssl_days_remaining !== null && service.ssl_days_remaining <= 0 ? (
            <p className="text-red-700 font-semibold">Certificate has expired!</p>
          ) : (
            <div className="space-y-0.5">
              <p>
                <span className="font-medium">Expires:</span>{" "}
                {new Date(service.ssl_expires_at!).toLocaleDateString()}
              </p>
              <p>
                <span className="font-medium">Days remaining:</span>{" "}
                <span className={
                  service.ssl_days_remaining! <= 7 ? "text-red-600 font-semibold" :
                  service.ssl_days_remaining! <= 30 ? "text-yellow-600 font-semibold" :
                  "text-green-700 font-semibold"
                }>
                  {service.ssl_days_remaining} days
                </span>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
