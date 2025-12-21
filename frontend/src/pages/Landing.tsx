import { useState } from "react";
import {
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  CheckBadgeIcon,
  DocumentMagnifyingGlassIcon,
  CpuChipIcon,
  SparklesIcon,
  CheckCircleIcon,
  MapPinIcon,
} from "@heroicons/react/24/solid";
import { Link } from "react-router-dom";
import Button from "../components/Button";

export default function App() {
  const [open, setOpen] = useState(false);

  const features = [
    { title: "Tanya Jawab Hukum", desc: "Mengajukan pertanyaan seputar hukum pidana dengan bahasa yang mudah dipahami.", icon: ChatBubbleLeftRightIcon },
    { title: "Rekomendasi Pengacara", desc: "Memberikan daftar pengacara yang relevan dengan kasus serta mempertimbangkan jarak lokasi.", icon: UserGroupIcon },
    { title: "Jawaban Terverifikasi", desc: "Didukung integrasi RAG untuk memberikan jawaban yang terstruktur dan berbasis sumber.", icon: CheckBadgeIcon },
  ];

  const steps = [
    {
      title: "Input Pertanyaan",
      desc: "Pengguna menuliskan kronologi/pertanyaan. Sistem meminta kata kunci penting agar ringkas dan fokus.",
      icon: DocumentMagnifyingGlassIcon,
    },
    {
      title: "Proses Retrieval",
      desc: "Mesin pencari semantik mengambil pasal/UU/putusan yang relevan dari vector store & basis data hukum.",
      icon: CpuChipIcon,
    },
    {
      title: "LLM Reasoning",
      desc: "Model bahasa memaknai konteks, menilai relevansi, lalu menyusun garis besar jawaban.",
      icon: SparklesIcon,
    },
    {
      title: "RAG Synthesis",
      desc: "Konteks hasil retrieval dipadukan ke dalam jawaban final yang terstruktur, bersumber, dan mudah dipahami.",
      icon: CheckCircleIcon,
    },
    {
      title: "Rekomendasi Pengacara",
      desc: "Peringkat pengacara dihitung dari jarak dengan rumus Haversine Distance, serta kemiripan semantik profil kasus.",
      icon: MapPinIcon,
    },
  ];

  return (
    <div className="min-h-full flex flex-col">
      {/* Top nav */}
      <header className="w-full border-b border-gray-200/70 bg-white/70 backdrop-blur">
        <nav className="mx-auto max-w-7xl flex items-center justify-between px-5 py-3">
          {/* Left: brand */}
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: "var(--accent)" }}>
              <img src="/themis_logo.png" alt="ThemisAI Logo" className="h-7 w-7" />
            </div>
            <span className="font-semibold tracking-tight">ThemisAI</span>
          </div>

          {/* Center: nav links */}
          <div className="absolute left-1/2 -translate-x-1/2 hidden md:flex items-center gap-6 text-sm">
            <a href="#about" className="text-gray-700 hover:text-accent">About Us</a>
            <a href="#how" className="text-gray-700 hover:text-accent">How It Works</a>
          </div>

          {/* Right: auth */}
          <div className="flex items-center gap-2">
            <Link to="/signin"><Button variant="outline">Sign in</Button></Link>
            <Link to="/signup"><Button>Sign up</Button></Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <main className="flex-1">
         <section className="mx-auto max-w-7xl px-5 pt-16 pb-12"> {/* increased pt/pb */}
          <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center"> {/* wider gap */}
            {/* Left copy */}
            <div>
              <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs border border-accent/60 bg-accent/30 mb-4">
                Bot AI dengan pengetahuan luas tentang hukum pidana Indonesia.
              </div>
              <h1 className="text-[34px] md:text-5xl font-semibold leading-snug tracking-tight"> {/* leading-snug for more line space */}
                Bantuan hukum,<br className="hidden sm:block" /> lebih sederhana.
              </h1>
              <p className="mt-5 text-gray-600 text-[15px] leading-relaxed"> {/* larger mt + relaxed line-height */}
                ThemisAI membantu Anda mengeksplorasi pertanyaan hukum pidana, mengumpulkan konteks dengan RAG,
                serta memberikan rekomendasi pengacara yang sesuai dengan kasus dan jarak Anda. Semua disajikan
                dengan jawaban terstruktur, terverifikasi, dan mudah dipahami.
              </p>

              <div className="mt-8 flex flex-wrap gap-4"> {/* more space above and between buttons */}
                <Link to="/signin"><Button>Mulai sekarang</Button></Link>
              </div>

              <div className="mt-6 flex items-center gap-3 text-xs text-gray-500"> {/* more margin top */}
                <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                <span>Bukan layanan hukum — jawaban hanya bersifat informasi.</span>
              </div>
            </div>

            {/* Right mock chat */}
            <div className="relative">
              <div
                className="absolute -inset-2 rounded-2xl blur-xl opacity-40"
                style={{ background: "radial-gradient(550px 200px at 50% 0%, #FFD3C0, transparent)" }}
              />
              <div className="relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"> {/* more padding */}
                <div className="flex gap-2 pb-4 border-b border-gray-100">
                  <div className="h-3 w-3 rounded-full bg-red-400" />
                  <div className="h-3 w-3 rounded-full bg-yellow-400" />
                  <div className="h-3 w-3 rounded-full bg-green-400" />
                </div>
                <div className="p-4 text-sm text-gray-700"> {/* more padding */}
                  <div className="mb-3 font-medium">Contoh Percakapan</div>
                  <div className="space-y-3"> {/* extra space between bubbles */}
                    <div className="rounded-xl bg-gray-50 p-3">
                      <span className="text-gray-500">You:</span> Apa langkah awal bila jadi korban penipuan online?
                    </div>
                    <div className="rounded-xl p-3 border border-accent/50 bg-accent/30">
                      <span className="text-gray-700 font-medium">ThemisAI:</span> Laporkan ke polisi (SP2HP), kumpulkan bukti
                      transfer/chat, & simpan kronologi. Jika butuh bantuan tambahan, saya dapat berikan pengacara yang dapat
                      membantu Anda dalam kasus ini.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features strip */}
        <section id="features" className="bg-accent/20 border-y border-accent/40">
          <div className="mx-auto max-w-7xl px-5 py-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map(({ title, desc, icon: Icon }) => (
              <div key={title} className="rounded-2xl border border-accent/50 bg-white p-5 shadow-sm">
                <div className="h-8 w-8 rounded-xl mb-3 flex items-center justify-center" style={{ backgroundColor: "var(--accent)" }}>
                  <Icon className="h-5 w-5 text-gray-900" />
                </div>
                <div className="font-semibold">{title}</div>
                <div className="text-sm text-gray-600 mt-1">{desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* About Us (image-free) */}
        <section id="about" className="mx-auto max-w-7xl px-5 pt-10 pb-8">
          <div className="grid lg:grid-cols-2 gap-8 items-start">
            {/* Copy */}
            <div>
              <h2 className="text-2xl font-semibold mb-3">About Us</h2>
              <p className="text-gray-700 text-sm leading-relaxed">
                <b>ThemisAI</b> adalah prototipe sistem konsultasi hukum pidana berbasis web untuk skripsi UPN “Veteran”
                Jakarta (UPNVJ). Terinspirasi dari <b>Themis</b>, dewi keadilan dalam mitologi Yunani, platform ini dirancang
                untuk membantu masyarakat memahami isu-isu hukum pidana secara <i>accessible</i> dan <i>accountable</i>,
                sambil menjaga akurasi melalui pelacakan sumber.
              </p>
              <p className="text-gray-700 text-sm leading-relaxed mt-3">
                Di balik layar, ThemisAI memanfaatkan <b>Retrieval-Augmented Generation (RAG)</b> untuk menggabungkan kemampuan
                <b> Large Language Models (LLM)</b> dengan pengetahuan hukum terkurasi. Kami mengadopsi arsitektur modern:
                <b> LangGraph</b> untuk orkestrasi alur agen, <b>FastAPI</b> sebagai backend, <b>React</b> untuk antarmuka,
                <b> PostgreSQL</b> untuk data terstruktur, serta <b>Vector Store</b> untuk pencarian semantik.
                Integrasi <b>geospatial</b> membantu merekomendasikan pengacara berdasarkan jarak dan kecocokan kasus.
              </p>

              {/* Quick bullets */}
              <ul className="mt-4 grid sm:grid-cols-2 gap-3 text-sm">
                <li className="flex items-start gap-2">
                  <MapPinIcon className="h-4 w-4 mt-0.5 text-gray-900" />
                  <span>Fokus awal: Hukum Pidana Indonesia</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckBadgeIcon className="h-4 w-4 mt-0.5 text-gray-900" />
                  <span>Jejak sumber (traceability) pada setiap jawaban</span>
                </li>
                <li className="flex items-start gap-2">
                  <CpuChipIcon className="h-4 w-4 mt-0.5 text-gray-900" />
                  <span>RAG + LLM dengan orkestrasi LangGraph</span>
                </li>
                <li className="flex items-start gap-2">
                  <SparklesIcon className="h-4 w-4 mt-0.5 text-gray-900" />
                  <span>UI ringkas, fokus pada keterbacaan</span>
                </li>
              </ul>

              {/* Lawyer recommendation short explainer */}
              <p className="text-gray-700 text-sm leading-relaxed mt-3">
                Selain konsultasi hukum, <b>ThemisAI</b> juga dilengkapi fitur <b>rekomendasi pengacara</b>. Sistem membantu
                pengguna menemukan advokat yang sesuai dengan kasus dan lokasi mereka—menggabungkan kedekatan geografis dan
                kesesuaian keahlian, agar pengguna bisa langsung terhubung dengan pengacara yang tepat untuk tindak lanjut.
              </p>

              <p className="text-gray-700 text-sm leading-relaxed mt-3">
                <b>Catatan:</b> ThemisAI adalah prototipe akademik dan tidak menggantikan nasihat hukum profesional. Kami
                mendorong pengguna untuk berkonsultasi langsung dengan advokat berlisensi untuk tindakan legal.
              </p>
            </div>

            {/* Right: aesthetic, no images */}
            <div className="relative">
              {/* soft accent glow */}
              <div
                className="absolute -inset-1.5 rounded-3xl blur-xl opacity-50 mt-10"
                style={{ background: "radial-gradient(520px 200px at 50% 0%, var(--accent, #FFD3C0), transparent 70%)" }}
              />
              <div className="mt-10 relative rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="text-sm font-semibold mb-3">Tech Stack & Capabilities</div>

                {/* Stack pills */}
                <div className="flex flex-wrap gap-2">
                  {["RAG", "LLM", "LangGraph", "FastAPI", "React", "PostgreSQL", "FAISS", "Geospatial"].map((t) => (
                    <span
                      key={t}
                      className="px-2.5 py-1 rounded-full text-xs border border-gray-200 bg-gray-50"
                    >
                      {t}
                    </span>
                  ))}
                </div>

                {/* Mini flow (code-like) */}
                <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 text-[12px] leading-5 text-gray-700">
                  <div className="font-mono">
                    <div>Query → <b>Embed</b> → <b>Vector Search</b> → <b>Context</b> → <b>LLM</b> → Jawaban</div>
                    <div className="mt-1 opacity-80">
                      Rekomendasi pengacara dilakukan dengan peringkat berdasarkan kedekatan lokasi dan kecocokan keahlian
                    </div>
                  </div>

                  {/* 3 tiny “stat” chips */}
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-md border border-gray-200 bg-white px-2 py-1.5">
                      <div className="text-[11px] text-gray-500">Latensi</div>
                      <div className="text-xs font-semibold">Rendah</div>
                    </div>
                    <div className="rounded-md border border-gray-200 bg-white px-2 py-1.5">
                      <div className="text-[11px] text-gray-500">Jejak Sumber</div>
                      <div className="text-xs font-semibold">Aktif</div>
                    </div>
                    <div className="rounded-md border border-gray-200 bg-white px-2 py-1.5">
                      <div className="text-[11px] text-gray-500">Skalabilitas</div>
                      <div className="text-xs font-semibold">Siap</div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </section>

        {/* How It Works (aesthetic stepper) */}
        <section id="how" className="mx-auto max-w-7xl px-5 pb-12">
        <h2 className="text-2xl font-semibold mb-1">How It Works</h2>

        {/* wrapper dengan aksen lembut */}
        <div className="relative mt-5">
          <div
            className="absolute inset-0 rounded-3xl opacity-60 pointer-events-none"
          />

          {/* stepper cards */}
          <div className="relative grid md:grid-cols-2 lg:grid-cols-5 gap-4">
            {steps.map(({ title, desc, icon: Icon }, i) => (
              <div
                key={title}
                className="group relative rounded-2xl bg-white border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                {/* connector hanya layar besar */}
                {i < steps.length - 1 && (
                  <div className="hidden lg:block absolute right-[-10px] top-1/2 -translate-y-1/2 w-5 h-[2px] bg-gradient-to-r from-gray-200 to-gray-100" />
                )}

                <div className="flex items-center gap-3">
                  <div
                    className="h-9 w-9 rounded-xl flex items-center justify-center ring-1 ring-gray-900/5"
                    style={{ backgroundColor: "var(--accent)" }}
                  >
                    <Icon className="h-5 w-5 text-gray-900" />
                  </div>
                  <div className="text-sm font-semibold">{title}</div>
                </div>

                <p className="text-sm text-gray-600 mt-2">{desc}</p>
                <div className="mt-3 text-[11px] text-gray-500">Langkah {i + 1} dari {steps.length}</div>
              </div>
            ))}
          </div>

          {/* mini legend */}
          <div className="mt-5 flex flex-wrap items-center gap-2 text-[11px] text-gray-500">
            <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full border border-gray-200 bg-white">
              <span className="inline-block h-2.5 w-2.5 rounded-md" style={{ backgroundColor: "var(--accent)" }} />
              Proses terkendali (traceable)
            </span>
            <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full border border-gray-200 bg-white">
              <span className="inline-block h-2.5 w-2.5 rounded-md bg-gray-900" />
              Bukti & sumber ditampilkan
            </span>
          </div>


        </div>
      </section>
      </main>

      {/* Footer with UPNVJ logo */}
      <footer className="mx-auto max-w-7xl px-5 py-6 text-xs text-gray-600 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>© {new Date().getFullYear()} ThemisAI. All rights reserved.</span>
          <span className="text-gray-300">•</span>
          <img
            src="/logo_upnvj.png"
            alt="UPNVJ"
            className="h-6 w-6 rounded-sm shadow-sm ring-1 ring-gray-200"
            title="Universitas Pembangunan Nasional 'Veteran' Jakarta"
          />
          <span className="hidden sm:inline">Universitas Pembangunan Nasional "Veteran" Jakarta</span>
        </div>
      </footer>
    </div>
  );
}
