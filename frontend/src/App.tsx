import { Routes, Route, Navigate } from "react-router-dom";
import Landing from "./pages/Landing";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import Chat from "./pages/Chat";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* PUBLIC routes (render when logged out; redirect to /chat when logged in) */}
      <Route
        path="/"
        element={
          <ProtectedRoute verify={false}>
            <Landing />
          </ProtectedRoute>
        }
      />
      <Route
        path="/signin"
        element={
          <ProtectedRoute verify={false}>
            <SignIn />
          </ProtectedRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <ProtectedRoute verify={false}>
            <SignUp />
          </ProtectedRoute>
        }
      />

      {/* PRIVATE route */}
      <Route
        path="/chat"
        element={
          <ProtectedRoute verify>
            <Chat />
          </ProtectedRoute>
        }
      />

      {/* Fallback: go to landing, not /chat (avoids loops when logged out) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
