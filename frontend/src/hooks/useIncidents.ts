import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/incidents";

export const useIncidents = () => useQuery({ queryKey: ["incidents"], queryFn: api.getIncidents });
export const useIncident = (id: string) => useQuery({ queryKey: ["incidents", id], queryFn: () => api.getIncident(id) });
export const useIncidentEvents = (id: string) => useQuery({ queryKey: ["incidents", id, "events"], queryFn: () => api.getIncidentEvents(id) });

export function useAcknowledgeIncident() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.acknowledgeIncident,
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["incidents"] });
      qc.invalidateQueries({ queryKey: ["incidents", id] });
    },
  });
}

export function useResolveIncident() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.resolveIncident,
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["incidents"] });
      qc.invalidateQueries({ queryKey: ["incidents", id] });
    },
  });
}

export function useAddComment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, message }: { id: string; message: string }) => api.commentIncident(id, message),
    onSuccess: (_, { id }) => qc.invalidateQueries({ queryKey: ["incidents", id, "events"] }),
  });
}
