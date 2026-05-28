import { createContext, ReactNode, useContext, useEffect, useRef, useState } from "react";
import type { User } from "../types";
import keycloak from "./keycloak";

interface AuthContextValue {
  ready: boolean;
  authenticated: boolean;
  user: User | null;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({ ready: false, authenticated: false, user: null, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const initCalled = useRef(false);

  useEffect(() => {
    if (initCalled.current) return;
    initCalled.current = true;

    keycloak
      .init({ onLoad: "login-required", checkLoginIframe: false })
      .then(async (auth) => {
        setAuthenticated(auth);
        if (auth && keycloak.token) {
          try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/me`, {
              headers: { Authorization: `Bearer ${keycloak.token}` },
            });
            if (res.ok) setUser(await res.json());
          } catch {
            // non-fatal, app still works without user role
          }
        }
        setReady(true);
      })
      .catch(() => setReady(true));
  }, []);

  if (!ready) {
    return <div className="flex items-center justify-center h-screen text-gray-500">Loading…</div>;
  }

  return (
    <AuthContext.Provider value={{ ready, authenticated, user, logout: () => keycloak.logout() }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
