export type ServiceStatus = "UNKNOWN" | "UP" | "DOWN" | "DEGRADED";
export type IncidentStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";
export type IncidentSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type NotificationSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type UserRole = "ADMIN" | "OPERATOR" | "VIEWER";

export interface Service {
  id: string;
  name: string;
  url: string;
  description: string | null;
  check_interval: number;
  timeout: number;
  is_active: boolean;
  status: ServiceStatus;
  consecutive_failures: number;
  last_checked_at: string | null;
  created_at: string;
}

export interface Incident {
  id: string;
  service_id: string;
  title: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  started_at: string;
  resolved_at: string | null;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  incident_id: string;
  message: string;
  severity: NotificationSeverity;
  is_read: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface MetricsOverview {
  total_services: number;
  up: number;
  down: number;
  degraded: number;
  open_incidents: number;
}

export interface LatencyPoint {
  timestamp: string;
  latency_ms: number | null;
}

export interface UptimeStats {
  uptime_percent: number | null;
  total_checks: number;
}

export interface WSMessage {
  type: "service_update" | "incident_created" | "incident_updated" | "notification";
  [key: string]: unknown;
}
