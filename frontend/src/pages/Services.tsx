import { useState } from "react";
import { useAuth } from "../auth/AuthProvider";
import ServiceCard from "../components/ServiceCard";
import { useCreateService, useServices } from "../hooks/useServices";

const empty = { name: "", url: "", description: "", check_interval: "60", failure_threshold: "2", latency_threshold_ms: "2000", incident_severity: "CRITICAL" };
const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

export default function Services() {
  const { user } = useAuth();
  const canCreate = user?.role === "ADMIN" || user?.role === "OPERATOR";
  const { data: services = [] } = useServices();
  const create = useCreateService();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(empty);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await create.mutateAsync({
      name: form.name,
      url: form.url,
      description: form.description || null,
      check_interval: Number(form.check_interval) || 60,
      failure_threshold: Number(form.failure_threshold) || 2,
      latency_threshold_ms: Number(form.latency_threshold_ms) || 2000,
      incident_severity: form.incident_severity,
    });
    setShowForm(false);
    setForm(empty);
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Services</h1>
        {canCreate && (
          <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">
            Add Service
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">New Service</h2>
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Name" value={form.name} onChange={set("name")} required />
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="URL" value={form.url} onChange={set("url")} required />
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Description (optional)" value={form.description} onChange={set("description")} />
          <input type="number" className="w-full border rounded px-3 py-2 text-sm" placeholder="Check interval (seconds)" value={form.check_interval} onChange={set("check_interval")} min={10} />

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
                {SEVERITIES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="flex gap-3">
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-md text-sm hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((s) => <ServiceCard key={s.id} service={s} />)}
      </div>
    </div>
  );
}
