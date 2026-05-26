import { create } from "zustand";
import type { WSMessage } from "../types";

interface RealtimeStore {
  lastMessage: WSMessage | null;
  setLastMessage: (msg: WSMessage) => void;
}

export const useRealtimeStore = create<RealtimeStore>((set) => ({
  lastMessage: null,
  setLastMessage: (msg) => set({ lastMessage: msg }),
}));
