import type { Incident } from "../types";
import api from "./client";

export const getIncidents = () => api.get<Incident[]>("/incidents").then((r) => r.data);
export const getIncident = (id: string) => api.get<Incident>(`/incidents/${id}`).then((r) => r.data);
export const acknowledgeIncident = (id: string) => api.post<Incident>(`/incidents/${id}/acknowledge`).then((r) => r.data);
export const resolveIncident = (id: string) => api.post<Incident>(`/incidents/${id}/resolve`).then((r) => r.data);
export const commentIncident = (id: string, message: string) => api.post(`/incidents/${id}/comment`, { message }).then((r) => r.data);
