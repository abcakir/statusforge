import { createContext, ReactNode, useContext, useEffect, useRef, useState } from "react";
import keycloak from "./keycloak";

interface AuthContextValue {
  ready: boolean;
  authenticated: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({ ready: false, authenticated: false, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const initCalled = useRef(false);

  useEffect(() => {
    if (initCalled.current) return;
    initCalled.current = true;

    keycloak
      .init({ onLoad: "login-required", checkLoginIframe: false })
      .then((auth) => { setAuthenticated(auth); setReady(true); })
      .catch(() => setReady(true));
  }, []);

  if (!ready) {
    return <div className="flex items-center justify-center h-screen text-gray-500">Loading…</div>;
  }

  return (
    <AuthContext.Provider value={{ ready, authenticated, logout: () => keycloak.logout() }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
