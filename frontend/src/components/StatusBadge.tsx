const styles: Record<string, string> = {
  UP: "bg-green-100 text-green-800",
  DOWN: "bg-red-100 text-red-800",
  DEGRADED: "bg-yellow-100 text-yellow-800",
  UNKNOWN: "bg-gray-100 text-gray-700",
  OPEN: "bg-red-100 text-red-800",
  ACKNOWLEDGED: "bg-yellow-100 text-yellow-800",
  RESOLVED: "bg-green-100 text-green-800",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status}
    </span>
  );
}
