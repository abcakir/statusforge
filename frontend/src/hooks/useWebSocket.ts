import { useEffect, useRef } from "react";
import keycloak from "../auth/keycloak";
import { useRealtimeStore } from "../stores/realtimeStore";

export function useWebSocket(serviceId?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const setLastMessage = useRealtimeStore((s) => s.setLastMessage);

  useEffect(() => {
    const base = import.meta.env.VITE_WS_URL;
    const url = serviceId ? `${base}/ws/services/${serviceId}` : `${base}/ws`;

    const connect = () => {
      wsRef.current = new WebSocket(url);
      wsRef.current.onmessage = (e) => {
        try { setLastMessage(JSON.parse(e.data)); } catch { /* noop */ }
      };
      wsRef.current.onclose = () => setTimeout(connect, 3000);
    };

    connect();
    return () => wsRef.current?.close();
  }, [serviceId, setLastMessage]);
}
