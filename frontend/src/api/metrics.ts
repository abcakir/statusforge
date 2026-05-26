import type { LatencyPoint, MetricsOverview, UptimeStats } from "../types";
import api from "./client";

export const getOverview = () => api.get<MetricsOverview>("/metrics/overview").then((r) => r.data);
export const getLatencySeries = (id: string, hours = 24) =>
  api.get<LatencyPoint[]>(`/metrics/services/${id}/latency`, { params: { hours } }).then((r) => r.data);
export const getUptime = (id: string, days = 30) =>
  api.get<UptimeStats>(`/metrics/services/${id}/uptime`, { params: { days } }).then((r) => r.data);
