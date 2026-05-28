import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import NotificationBell from "./components/NotificationBell";
import Dashboard from "./pages/Dashboard";
import IncidentDetail from "./pages/IncidentDetail";
import Incidents from "./pages/Incidents";
import ServiceDetail from "./pages/ServiceDetail";
import Services from "./pages/Services";
import Settings from "./pages/Settings";

const qc = new QueryClient();

function Navbar() {
  const { logout, user } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <span className="font-bold text-xl text-blue-600">StatusForge</span>
        {[
          { to: "/", label: "Dashboard" },
          { to: "/services", label: "Services" },
          { to: "/incidents", label: "Incidents" },
        ].map(({ to, label }) => (
          <Link key={to} to={to} className="text-sm text-gray-600 hover:text-gray-900">
            {label}
          </Link>
        ))}
        {isAdmin && (
          <Link to="/settings" className="text-sm text-gray-600 hover:text-gray-900">
            Settings
          </Link>
        )}
      </div>
      <div className="flex items-center gap-3">
        <NotificationBell />
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-800 px-3 py-1 border border-gray-200 rounded-md hover:bg-gray-50">
          Logout
        </button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 py-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/services" element={<Services />} />
                <Route path="/services/:id" element={<ServiceDetail />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="/incidents/:id" element={<IncidentDetail />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
