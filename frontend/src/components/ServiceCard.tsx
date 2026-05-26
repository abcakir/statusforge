import { Link } from "react-router-dom";
import type { Service } from "../types";
import StatusBadge from "./StatusBadge";

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
        <StatusBadge status={service.status} />
      </div>
      {service.last_checked_at && (
        <p className="text-xs text-gray-400 mt-3">Last checked: {new Date(service.last_checked_at).toLocaleString()}</p>
      )}
    </Link>
  );
}
