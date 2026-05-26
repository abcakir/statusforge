import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/services";
import type { Service } from "../types";

export const useServices = () => useQuery({ queryKey: ["services"], queryFn: api.getServices });
export const useService = (id: string) => useQuery({ queryKey: ["services", id], queryFn: () => api.getService(id) });

export function useCreateService() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.createService, onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }) });
}

export function useUpdateService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Service> }) => api.updateService(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }),
  });
}

export function useDeleteService() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.deleteService, onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }) });
}
