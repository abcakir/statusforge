import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/incidents";

export const useIncidents = () => useQuery({ queryKey: ["incidents"], queryFn: api.getIncidents });
export const useIncident = (id: string) => useQuery({ queryKey: ["incidents", id], queryFn: () => api.getIncident(id) });

export function useAcknowledgeIncident() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.acknowledgeIncident, onSuccess: () => qc.invalidateQueries({ queryKey: ["incidents"] }) });
}

export function useResolveIncident() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.resolveIncident, onSuccess: () => qc.invalidateQueries({ queryKey: ["incidents"] }) });
}
