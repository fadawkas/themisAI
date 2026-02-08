import { ReactNode, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { API_BASE, getToken, clearAuth } from "../lib/auth";

type Props = { children: ReactNode; verify?: boolean };
type Status = "checking" | "ok" | "no" | "redir";

export default function ProtectedRoute({ children, verify = true }: Props) {
  const location = useLocation();
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    const token = getToken();

    // PUBLIC route (verify === false)
    if (!verify) {
      setStatus(token ? "redir" : "ok"); // logged-in users get sent to /chat
      return;
    }

    // PRIVATE route
    if (!token) {
      setStatus("no"); // go to landing
      return;
    }

    // Optional server verify
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        setStatus("ok");
      })
      .catch(() => {
        clearAuth();
        setStatus("no");
      });
  }, [location.key, verify]);

  if (status === "checking") {
    return (
      <div className="min-h-screen grid place-items-center text-gray-600">
        Memeriksa sesi…
      </div>
    );
  }
  if (status === "no") return <Navigate to="/" replace />;
  if (status === "redir") return <Navigate to="/chat" replace />;

  return <>{children}</>;
}
