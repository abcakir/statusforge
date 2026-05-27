import { useState } from "react";
import ServiceCard from "../components/ServiceCard";
import { useCreateService, useServices } from "../hooks/useServices";

const empty = { name: "", url: "", description: "", check_interval: "60" };

export default function Services() {
  const { data: services = [] } = useServices();
  const create = useCreateService();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(empty);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await create.mutateAsync({ ...form, check_interval: Number(form.check_interval) || 60 });
    setShowForm(false);
    setForm(empty);
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Services</h1>
        <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">
          Add Service
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">New Service</h2>
          {(["name", "url", "description"] as const).map((k) => (
            <input key={k} className="w-full border rounded px-3 py-2 text-sm" placeholder={k.charAt(0).toUpperCase() + k.slice(1)} value={form[k]} onChange={set(k)} required={k !== "description"} />
          ))}
          <input type="number" className="w-full border rounded px-3 py-2 text-sm" placeholder="Check interval (seconds)" value={form.check_interval} onChange={set("check_interval")} min={10} />
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
