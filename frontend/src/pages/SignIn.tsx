// src/pages/SignIn.tsx
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import Button from "../components/Button";

const API_BASE = import.meta.env.VITE_API_URL ?? ""; // e.g. "http://localhost:8000"

export default function SignIn() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    if (!email || !pw) {
      setErr("Email dan kata sandi wajib diisi.");
      return;
    }

    try {
      setLoading(true);

      // Build x-www-form-urlencoded body for OAuth2PasswordRequestForm
      const form = new URLSearchParams();
      form.set("username", email.trim().toLowerCase());
      form.set("password", pw);

      const res = await fetch(`${API_BASE}/auth/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || "Gagal masuk");

      const token: string = data.access_token;
      localStorage.setItem("themis:token", token);

      // Load current user profile
      const meRes = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const me = await meRes.json().catch(() => ({}));
      if (!meRes.ok) {
        // If /me fails, still continue to chat but surface a warning
        console.warn("/auth/me failed:", me);
      } else {
        localStorage.setItem("themis:user", JSON.stringify(me));
      }

      nav("/chat");
    } catch (e: any) {
      setErr(e?.message || "Terjadi kesalahan saat masuk");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center px-4 bg-accent/20 border-y border-accent/40">
      <div className="w-full max-w-md bg-white border rounded-2xl p-6">
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <Link to="/">
              <div
                className="h-8 w-8 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: "var(--accent)" }}
              >
                <img src="/themis_logo.png" className="h-7 w-7" alt="ThemisAI" />
              </div>
            </Link>
            <Link to="/">
              <span className="font-semibold">ThemisAI</span>
            </Link>
          </div>
        </div>

        <h2 className="text-2xl font-semibold mb-1">Masuk</h2>
        <p className="text-sm text-gray-600 mb-6">Lanjutkan ke ruang obrolan Anda</p>

        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm">
            <div className="mb-1 text-gray-700">Email</div>
            <input
              type="email"
              className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
              placeholder="nama@contoh.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>

          <label className="block text-sm">
            <div className="mb-1 text-gray-700">Kata sandi</div>
            <input
              type="password"
              className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
              placeholder="••••••••"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              required
            />
          </label>

          {err && <div className="text-sm text-red-600">{err}</div>}

          <Button className="w-full" type="submit" disabled={loading}>
            {loading ? "Memproses..." : "Masuk"}
          </Button>
        </form>

        <div className="mt-4 text-sm text-gray-600">
          Belum punya akun? <Link to="/signup" className="underline">Daftar</Link>
        </div>

        <div className="mt-4 text-xs text-gray-500">
          Bukan layanan hukum — jawaban hanya bersifat informasi.
        </div>
      </div>
    </div>
  );
}
