import type { User } from "../types";
import api from "./client";

export const getMe = () => api.get<User>("/auth/me").then((r) => r.data);
export const getUsers = () => api.get<User[]>("/users").then((r) => r.data);
export const updateRole = (id: string, role: string) => api.patch<User>(`/users/${id}/role`, { role }).then((r) => r.data);
export const deleteUser = (id: string) => api.delete(`/users/${id}`);
