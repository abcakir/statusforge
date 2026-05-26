import type { Service } from "../types";
import api from "./client";

export const getServices = () => api.get<Service[]>("/services").then((r) => r.data);
export const getService = (id: string) => api.get<Service>(`/services/${id}`).then((r) => r.data);
export const createService = (data: Partial<Service>) => api.post<Service>("/services", data).then((r) => r.data);
export const updateService = (id: string, data: Partial<Service>) => api.patch<Service>(`/services/${id}`, data).then((r) => r.data);
export const deleteService = (id: string) => api.delete(`/services/${id}`);
export const checkNow = (id: string) => api.post(`/services/${id}/check-now`);
export const getHealthHistory = (id: string) => api.get(`/services/${id}/health-history`).then((r) => r.data);
