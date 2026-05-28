import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import StatusBadge from "../components/StatusBadge";
import { useAcknowledgeIncident, useAddComment, useIncident, useIncidentEvents, useResolveIncident } from "../hooks/useIncidents";
import { useWebSocket } from "../hooks/useWebSocket";
import { useRealtimeStore } from "../stores/realtimeStore";
import type { IncidentEventType } from "../types";
import { useQueryClient } from "@tanstack/react-query";

const severityColor: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-800",
  HIGH: "bg-orange-100 text-orange-800",
  MEDIUM: "bg-yellow-100 text-yellow-800",
  LOW: "bg-blue-100 text-blue-800",
};

const eventIcon: Record<IncidentEventType, string> = {
  CREATED: "🔴",
  ACKNOWLEDGED: "🟡",
  RESOLVED: "🟢",
  COMMENT: "💬",
};

const eventLabel: Record<IncidentEventType, string> = {
  CREATED: "Incident created",
  ACKNOWLEDGED: "Acknowledged",
  RESOLVED: "Resolved",
  COMMENT: "Comment",
};

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const canAct = user?.role === "ADMIN" || user?.role === "OPERATOR";
  const qc = useQueryClient();
  const lastMessage = useRealtimeStore((s) => s.lastMessage);
  useWebSocket();

  useEffect(() => {
    if (lastMessage?.type === "incident_updated" && (lastMessage as { incident_id?: string }).incident_id === id) {
      qc.invalidateQueries({ queryKey: ["incidents", id] });
      qc.invalidateQueries({ queryKey: ["incidents", id, "events"] });
    }
  }, [lastMessage, id, qc]);

  const { data: incident } = useIncident(id!);
  const { data: events = [] } = useIncidentEvents(id!);
  const acknowledge = useAcknowledgeIncident();
  const resolve = useResolveIncident();
  const addComment = useAddComment();

  const [comment, setComment] = useState("");

  const handleComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!comment.trim()) return;
    await addComment.mutateAsync({ id: id!, message: comment.trim() });
    setComment("");
  };

  if (!incident) return <div className="text-gray-500">Loading…</div>;

  return (
    <div className="space-y-6 max-w-3xl">
      <Link to="/incidents" className="text-sm text-blue-600 hover:underline">← Back to Incidents</Link>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-gray-900">{incident.title}</h1>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${severityColor[incident.severity] ?? "bg-gray-100 text-gray-700"}`}>
                {incident.severity}
              </span>
              <StatusBadge status={incident.status} />
            </div>
            <div className="text-sm text-gray-500 space-y-0.5">
              <p>Started: {new Date(incident.started_at).toLocaleString()}</p>
              {incident.resolved_at && <p>Resolved: {new Date(incident.resolved_at).toLocaleString()}</p>}
            </div>
          </div>

          {canAct && incident.status !== "RESOLVED" && (
            <div className="flex gap-2 shrink-0">
              {incident.status === "OPEN" && (
                <button
                  onClick={() => acknowledge.mutate(incident.id)}
                  disabled={acknowledge.isPending}
                  className="px-3 py-1.5 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 disabled:opacity-50"
                >
                  Acknowledge
                </button>
              )}
              <button
                onClick={() => resolve.mutate(incident.id)}
                disabled={resolve.isPending}
                className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
              >
                Resolve
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="font-semibold text-gray-800 mb-4">Timeline</h2>
        {events.length === 0 ? (
          <p className="text-sm text-gray-500">No events yet.</p>
        ) : (
          <ol className="relative border-l border-gray-200 space-y-4 ml-3">
            {events.map((ev) => (
              <li key={ev.id} className="ml-6">
                <span className="absolute -left-3 flex items-center justify-center w-6 h-6 rounded-full bg-white border border-gray-200 text-sm">
                  {eventIcon[ev.event_type]}
                </span>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-800">{eventLabel[ev.event_type]}</p>
                  {ev.message && <p className="text-sm text-gray-600 mt-0.5">{ev.message}</p>}
                  <p className="text-xs text-gray-400 mt-1">{new Date(ev.created_at).toLocaleString()}</p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>

      {canAct && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-800 mb-3">Add Comment</h2>
          <form onSubmit={handleComment} className="space-y-3">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Write a comment…"
              rows={3}
              className="w-full border rounded px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <button
              type="submit"
              disabled={addComment.isPending || !comment.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {addComment.isPending ? "Posting…" : "Post Comment"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
