import type { SystemStatus } from "../types";

export const getSystemStatus = async (): Promise<SystemStatus> => {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/status`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
};
