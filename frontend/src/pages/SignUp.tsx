// src/pages/SignUp.tsx
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import Button from "../components/Button";

type Gender = "male" | "female" | "unknown";

const API_BASE = import.meta.env.VITE_API_URL ?? ""; // e.g. "http://localhost:8000"

export default function SignUp() {
  const nav = useNavigate();

  // Step control
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);

  // Step 1: Identity fields
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [dob, setDob] = useState(""); // yyyy-mm-dd
  const [gender, setGender] = useState<Gender>("unknown");
  const [pw, setPw] = useState("");

  // Step 2: Address fields
  const [alamat, setAlamat] = useState("");
  const [kota, setKota] = useState("");
  const [provinsi, setProvinsi] = useState("");
  const [negara, setNegara] = useState("");
  const [kodePos, setKodePos] = useState("");

  const [err, setErr] = useState("");

  function nextStep(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    if (!name || !email || !pw || !dob || !gender) {
      setErr("Semua kolom pada langkah ini wajib diisi.");
      return;
    }
    setStep(2);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    if (!alamat || !kota || !provinsi || !negara || !kodePos) {
      setErr("Semua kolom alamat wajib diisi.");
      return;
    }

    try {
      setLoading(true);

      // Your FastAPI function parameters are plain args -> read from querystring.
      const qs = new URLSearchParams();
      qs.set("full_name", name.trim());
      qs.set("email", email.trim().toLowerCase());
      qs.set("password", pw);
      qs.set("gender", gender);
      if (dob) qs.set("date_of_birth", dob); // "YYYY-MM-DD"

      // Address (optional in backend, but we send them now from Step 2)
      qs.set("line1", alamat);
      qs.set("city", kota);
      qs.set("state", provinsi);         // mapped to "state" in backend
      qs.set("postal_code", kodePos);
      qs.set("country", negara);

      const res = await fetch(`${API_BASE}/auth/signup?${qs.toString()}`, {
        method: "POST",
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof data?.detail === "string" ? data.detail : "Gagal mendaftar"
        );
      }

      // Save token & user; proceed
      localStorage.setItem("themis:token", data.access_token);
      localStorage.setItem("themis:user", JSON.stringify(data.user));
      nav("/chat");
    } catch (e: any) {
      setErr(e.message || "Terjadi kesalahan saat mendaftar");
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

        <h2 className="text-2xl font-semibold mb-1">Daftar</h2>
        <p className="text-sm text-gray-600 mb-2">Mulai percakapan pertama Anda</p>
        <div className="text-xs text-gray-500 mb-6">Langkah {step} dari 2</div>

        {/* STEP 1: Identity */}
        {step === 1 && (
          <form className="space-y-4" onSubmit={nextStep}>
            {/* Nama */}
            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Nama</div>
              <input
                className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                placeholder="Nama lengkap"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </label>

            {/* Email */}
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

            {/* Tanggal Lahir */}
            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Tanggal lahir</div>
              <input
                type="date"
                className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                required
              />
            </label>

            {/* Gender */}
            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Jenis kelamin</div>
              <select
                className="w-full h-11 px-3 rounded-2xl border bg-white focus:ring-2 focus:ring-gray-200 outline-none"
                value={gender}
                onChange={(e) => setGender(e.target.value as Gender)}
                required
              >
                <option value="unknown">Pilih salah satu</option>
                <option value="male">Laki-laki</option>
                <option value="female">Perempuan</option>
              </select>
            </label>

            {/* Kata sandi */}
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
              {loading ? "Memproses..." : "Selanjutnya"}
            </Button>

            <div className="mt-4 text-sm text-gray-600">
              Sudah punya akun? <Link to="/signin" className="underline">Masuk</Link>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Bukan layanan hukum — jawaban hanya bersifat informasi.
            </div>
          </form>
        )}

        {/* STEP 2: Address */}
        {step === 2 && (
          <form className="space-y-4" onSubmit={onSubmit}>
            {/* Alamat (full street) */}
            <label className="block text-sm">
              <div className="mb-1 text-gray-700">Alamat</div>
              <input
                className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                placeholder="Jalan, nomor rumah, RT/RW, kelurahan"
                value={alamat}
                onChange={(e) => setAlamat(e.target.value)}
                required
              />
            </label>

            {/* Kota & Provinsi */}
            <div className="grid sm:grid-cols-2 gap-3">
              <label className="block text-sm">
                <div className="mb-1 text-gray-700">Kota</div>
                <input
                  className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                  placeholder="Contoh: Jakarta Selatan"
                  value={kota}
                  onChange={(e) => setKota(e.target.value)}
                  required
                />
              </label>

              <label className="block text-sm">
                <div className="mb-1 text-gray-700">Provinsi</div>
                <input
                  className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                  placeholder="Contoh: DKI Jakarta"
                  value={provinsi}
                  onChange={(e) => setProvinsi(e.target.value)}
                  required
                />
              </label>
            </div>

            {/* Negara & Kode Pos */}
            <div className="grid sm:grid-cols-2 gap-3">
              <label className="block text-sm">
                <div className="mb-1 text-gray-700">Negara</div>
                <input
                  className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                  placeholder="Contoh: Indonesia"
                  value={negara}
                  onChange={(e) => setNegara(e.target.value)}
                  required
                />
              </label>

              <label className="block text-sm">
                <div className="mb-1 text-gray-700">Kode Pos</div>
                <input
                  inputMode="numeric"
                  className="w-full h-11 px-3 rounded-2xl border focus:ring-2 focus:ring-gray-200 outline-none"
                  placeholder="Contoh: 12940"
                  value={kodePos}
                  onChange={(e) => setKodePos(e.target.value.replace(/\D/g, ""))}
                  required
                />
              </label>
            </div>

            {err && <div className="text-sm text-red-600">{err}</div>}

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="h-11 px-4 rounded-2xl border text-sm hover:bg-gray-50"
                onClick={() => setStep(1)}
              >
                Kembali
              </button>
              <Button className="w-full" type="submit" disabled={loading}>
                {loading ? "Mendaftar..." : "Daftar"}
              </Button>
            </div>

            <div className="mt-4 text-sm text-gray-600">
              Sudah punya akun? <Link to="/signin" className="underline">Masuk</Link>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Bukan layanan hukum — jawaban hanya bersifat informasi.
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
