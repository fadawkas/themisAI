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
  const [showForgot, setShowForgot] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [prefillToken, setPrefillToken] = useState("");



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
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => setShowForgot(true)}
              className="text-sm underline text-gray-700 hover:opacity-80"
            >
              Lupa kata sandi?
            </button>
          </div>


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
      {showForgot && (
        <ForgotPasswordModal
          onClose={() => setShowForgot(false)}
          onHaveToken={() => {
            setShowForgot(false);
            setShowReset(true);
          }}
        />
      )}

      {showReset && (
        <ResetPasswordModal
          onClose={() => setShowReset(false)}
          tokenPrefill={prefillToken}
        />
      )}


    </div>
  );
}

function ForgotPasswordModal({
  onClose,
  onHaveToken,
}: {
  onClose: () => void;
  onHaveToken: () => void;
}) {

  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    if (!email.trim()) {
      setErr("Email wajib diisi.");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || "Gagal mengirim email");

      setDone(true);
    } catch (e: any) {
      setErr(e?.message || "Terjadi kesalahan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-white rounded-2xl p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>

        <h3 className="text-lg font-semibold mb-1">Lupa kata sandi</h3>
        <p className="text-sm text-gray-600 mb-4">
          Masukkan email Anda. Kami akan mengirim token reset.
        </p>

        {done ? (
          <div className="text-sm text-gray-700 space-y-3">
            <p>
              Jika email terdaftar, token reset telah dikirim. Cek inbox/spam.
            </p>
            <button
              type="button"
              onClick={onHaveToken}
              className="underline text-left"
            >
              Saya sudah punya token
            </button>

          </div>
        ) : (
          <form className="space-y-4" onSubmit={onSubmit}>
            <input
              type="email"
              className="w-full h-11 px-3 rounded-xl border focus:ring-2 focus:ring-gray-200 outline-none"
              placeholder="nama@contoh.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            {err && <div className="text-sm text-red-600">{err}</div>}

            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? "Mengirim..." : "Kirim Token"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}

function ResetPasswordModal({
  onClose,
  tokenPrefill = "",
}: {
  onClose: () => void;
  tokenPrefill?: string;
}) {
  const [token, setToken] = useState(tokenPrefill);
  const [pw1, setPw1] = useState("");
  const [pw2, setPw2] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    const t = token.trim();
    const p1 = pw1; // jangan trim password (biar user kontrol), tapi boleh kalau kamu mau
    const p2 = pw2;

    if (!t) return setErr("Token wajib diisi.");
    if (p1.length < 8) return setErr("Password minimal 8 karakter.");
    if (p1 !== p2) return setErr("Konfirmasi password tidak sama.");

    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: t, new_password: p1 }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || "Reset password gagal");

      setDone(true);
    } catch (e: any) {
      setErr(e?.message || "Terjadi kesalahan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-sm bg-white rounded-2xl p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
          aria-label="Tutup"
        >
          ✕
        </button>

        <h3 className="text-lg font-semibold mb-1">Reset kata sandi</h3>
        <p className="text-sm text-gray-600 mb-4">
        </p>

        {done ? (
          <div className="text-sm text-gray-700 space-y-3">
            <p>Password berhasil diubah. Silakan masuk dengan password baru.</p>
            <Button className="w-full" type="button" onClick={onClose}>
              Kembali ke login
            </Button>
          </div>
        ) : (
          <form className="space-y-4" onSubmit={onSubmit}>
            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Token</div>
              <input
                className="w-full h-11 px-3 rounded-xl border focus:ring-2 focus:ring-gray-200 outline-none"
                placeholder="Tempel token di sini"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
              />
            </label>

            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Password baru</div>
              <input
                type="password"
                className="w-full h-11 px-3 rounded-xl border focus:ring-2 focus:ring-gray-200 outline-none"
                placeholder="••••••••"
                value={pw1}
                onChange={(e) => setPw1(e.target.value)}
                required
              />
            </label>

            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Ulangi password baru</div>
              <input
                type="password"
                className="w-full h-11 px-3 rounded-xl border focus:ring-2 focus:ring-gray-200 outline-none"
                placeholder="••••••••"
                value={pw2}
                onChange={(e) => setPw2(e.target.value)}
                required
              />
            </label>

            {err && <div className="text-sm text-red-600">{err}</div>}

            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? "Menyimpan..." : "Simpan password"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
