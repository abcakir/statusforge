import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LatencyPoint } from "../types";

export default function LatencyChart({ data }: { data: LatencyPoint[] }) {
  const points = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    latency: d.latency_ms,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={points}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" tick={{ fontSize: 11 }} />
        <YAxis unit="ms" />
        <Tooltip formatter={(v) => [`${v}ms`, "Latency"]} />
        <Line type="monotone" dataKey="latency" stroke="#3b82f6" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
