import type { Notification } from "../types";
import api from "./client";

export const getNotifications = () => api.get<Notification[]>("/notifications").then((r) => r.data);
export const markRead = (id: string) => api.patch<Notification>(`/notifications/${id}/read`).then((r) => r.data);
export const markAllRead = () => api.patch("/notifications/read-all");
