import { Link } from "react-router-dom";
import type { Service } from "../types";
import StatusBadge from "./StatusBadge";

function SSLBadge({ days }: { days: number | null }) {
  if (days === null) return null;
  if (days > 30) return null;
  const color = days <= 7 ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700";
  const label = days <= 0 ? "SSL expired" : `SSL ${days}d`;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

export default function ServiceCard({ service }: { service: Service }) {
  return (
    <Link
      to={`/services/${service.id}`}
      className="block bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{service.name}</h3>
          <p className="text-sm text-gray-500 truncate">{service.url}</p>
          {service.description && <p className="text-sm text-gray-600 mt-1 line-clamp-2">{service.description}</p>}
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={service.status} />
          <SSLBadge days={service.ssl_days_remaining} />
        </div>
      </div>
      {service.last_checked_at && (
        <p className="text-xs text-gray-400 mt-3">Last checked: {new Date(service.last_checked_at).toLocaleString()}</p>
      )}
    </Link>
  );
}
