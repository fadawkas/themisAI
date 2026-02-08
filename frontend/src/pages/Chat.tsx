import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { clearAuth } from "../lib/auth";
import { PlusIcon, PaperAirplaneIcon } from "@heroicons/react/24/solid";
import MarkdownBubble from "../components/MarkdownBubble";

type Role = "user" | "bot";
type Attachment = { name: string; size: number };
type Message = { role: Role; text: string; attachments?: Attachment[] };

// ===== API types (match FastAPI responses) =====
type SessionStatus = "active" | "archived" | "closed";
type ApiSession = {
  id: string;
  person_id: string;
  title?: string | null;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
};

type ApiDocument = {
  id: string;
  path: string;
  doc_type: "statute" | "case_law" | "regulation" | "other";
  title?: string | null;
  uploaded_at: string;
};

type ApiAttachment = {
  id: string;
  message_id: string;
  document_id: string;
  caption?: string | null;
  created_at: string;
  document?: ApiDocument | null;
};

type ApiMessage = {
  id: string;
  session_id: string;
  role: "user" | "bot" | "system";
  content: string;
  sent_at: string;
  reasoning_context?: string | null;
  latency_ms?: number | null;
  attachments: ApiAttachment[];
};

// ===== API client helpers =====
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("themis:token"); // adjust if you use a different key
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) msg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      const t = await res.text().catch(() => "");
      if (t) msg = t;
    }
    if (res.status === 401) {
      throw new Error("unauthorized");
    }
    throw new Error(msg);
  }

  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

async function fetchSessions(): Promise<ApiSession[]> {
  return api<ApiSession[]>("/chat/sessions?limit=50&offset=0");
}

async function createSession(title?: string): Promise<ApiSession> {
  return api<ApiSession>("/chat/sessions", {
    method: "POST",
    body: JSON.stringify({ title: title ?? null }),
  });
}

async function deleteSession(sessionId: string): Promise<void> {
  await api<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" });
}

async function fetchMessages(sessionId: string): Promise<ApiMessage[]> {
  return api<ApiMessage[]>(`/chat/sessions/${sessionId}/messages?limit=200&offset=0`);
}

async function sendApiMessage(sessionId: string, content: string, documentIds?: string[]): Promise<ApiMessage> {
  return api<ApiMessage>("/chat/messages", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      content,
      role: "user",
      document_ids: documentIds && documentIds.length ? documentIds : null,
    }),
  });
}


async function renameSession(sessionId: string, title: string): Promise<ApiSession> {
  return api<ApiSession>(`/chat/sessions/${sessionId}`, {
    method: "PUT", // ⬅️ switch from PATCH
    body: JSON.stringify({ title }),
  });
}

async function uploadDocuments(files: File[]) {
  const token = getToken();
  const fd = new FormData();
  for (const f of files) fd.append("files", f);

  const res = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // JANGAN set Content-Type di sini!
    },
    body: fd,
  });

  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(t || `Upload failed HTTP ${res.status}`);
  }

  return (await res.json()) as { saved: { id: string }[] };
}




// ===== Component =====
export default function Chat() {
  const nav = useNavigate();

  // Sidebar sessions
  const [sessions, setSessions] = useState<ApiSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  // Kebab menu + inline rename state
  const [menuFor, setMenuFor] = useState<string | null>(null);       // which session id has menu open
  const [renamingId, setRenamingId] = useState<string | null>(null); // which session is being renamed
  const [draftTitle, setDraftTitle] = useState<string>("");          // temp title for rename


  // Messages area
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const canSend = useMemo(() => input.trim().length > 0 || pendingFiles.length > 0, [input, pendingFiles]);

  // Refs
  const listRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // StrictMode double-mount guard
  const bootstrapped = useRef(false);

  // UI helpers
  const MAX_TXTAREA_H = 160;
  function resizeTextarea(el?: HTMLTextAreaElement | null) {
    const ta = el ?? textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    const next = Math.min(ta.scrollHeight, MAX_TXTAREA_H);
    ta.style.height = `${next}px`;
    ta.style.overflowY = ta.scrollHeight > MAX_TXTAREA_H ? "auto" : "hidden";
  }
  useEffect(() => resizeTextarea(), [input]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isTyping]);

  // Load sessions on mount (idempotent)
  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;

    (async () => {
      try {
        const list = await fetchSessions();
        if (list.length) {
          setSessions(list);
          setCurrentSessionId(list[0].id);
          return;
        }
        const s = await createSession("Percakapan baru");
        setSessions([s]);
        setCurrentSessionId(s.id);
        setMessages([{ role: "bot", text: "Halo, saya ThemisAI. Apa pertanyaan hukum Anda?" }]);
      } catch (e: any) {
        if (e?.message === "unauthorized") {
          clearAuth();
          nav("/", { replace: true });
        } else {
          console.error("Failed to load sessions:", e);
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load messages when session changes (race-safe)
  useEffect(() => {
    if (!currentSessionId) return;

    let cancelled = false;
    (async () => {
      try {
        const data = await fetchMessages(currentSessionId);
        if (cancelled) return;
        setMessages(
          data.length
            ? data.map((m) => ({
                role: m.role === "user" ? "user" : ("bot" as Role),
                text: m.content,
                attachments:
                  m.attachments?.length
                    ? m.attachments.map((att) => ({
                        name: att.document?.title || att.document?.path?.split("/").pop() || "Dokumen",
                        size: 0,
                      }))
                    : undefined,
              }))
            : [{ role: "bot", text: "Halo, saya ThemisAI. Apa pertanyaan hukum Anda?" }]
        );
      } catch (e: any) {
        // If session vanished (deleted elsewhere), refresh sessions
        if ((e.message || "").includes("404")) {
          try {
            const list = await fetchSessions();
            setSessions(list);
            setCurrentSessionId(list[0]?.id ?? null);
          } catch (err) {
            console.error("Failed to recover after 404:", err);
          }
        } else if (e?.message === "unauthorized") {
          clearAuth(); nav("/", { replace: true });
        } else {
          console.error("Failed to load messages:", e);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [currentSessionId]);

  // Sidebar actions
  async function handleNewChat() {
    try {
      const s = await createSession("Percakapan baru");
      setSessions((prev) => [s, ...prev]);
      setCurrentSessionId(s.id);
      setMessages([{ role: "bot", text: "Halo, saya ThemisAI. Apa pertanyaan hukum Anda?" }]);
    } catch (e) {
      console.error("Failed to create session:", e);
    }
  }

  async function handleDeleteSession(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    try {
      await deleteSession(id);
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        setCurrentSessionId((prevId) => (prevId === id ? next[0]?.id ?? null : prevId));
        if (!next.length) {
          (async () => {
            const s = await createSession("Percakapan baru");
            setSessions([s]);
            setCurrentSessionId(s.id);
            setMessages([{ role: "bot", text: "Halo, saya ThemisAI. Apa pertanyaan hukum Anda?" }]);
          })();
        }
        return next;
      });
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  }

  // Composer actions
  function triggerFileDialog() {
    fileInputRef.current?.click();
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length) setPendingFiles((prev) => [...prev, ...files]);
    e.currentTarget.value = "";
  }

  function removePending(idx: number) {
    setPendingFiles((p) => p.filter((_, i) => i !== idx));
  }

  function formatSize(n: number) {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!canSend) return;

    const text = input.trim();
    const filesToUpload = pendingFiles; // simpan dulu, karena nanti state di-clear
    const atts: Attachment[] = filesToUpload.map((f) => ({ name: f.name, size: f.size }));

    // Ensure a session exists
    let sessId = currentSessionId;
    if (!sessId) {
      const s = await createSession("Percakapan baru");
      setSessions((prev) => [s, ...prev]);
      setCurrentSessionId(s.id);
      sessId = s.id;
    }

    // Optimistic append user message
    setMessages((prev) => [...prev, { role: "user", text, attachments: atts }]);
    setInput("");
    setPendingFiles([]);
    setIsTyping(true);

    try {
      let documentIds: string[] = [];

      if (filesToUpload.length > 0) {
        const up = await uploadDocuments(filesToUpload); // POST /documents/upload (multipart)
        documentIds = up.saved.map((x) => x.id);
      }

      await sendApiMessage(sessId!, text, documentIds.length ? documentIds : undefined);
      const data = await fetchMessages(sessId!);
      setMessages(
        data.map((m) => ({
          role: m.role === "user" ? "user" : ("bot" as Role),
          text: m.content,
          attachments:
            m.attachments?.length
              ? m.attachments.map((att) => ({
                  name: att.document?.title || att.document?.path?.split("/").pop() || "Dokumen",
                  size: 0,
                }))
              : undefined,
        }))
      );
    } catch (err: any) {
      if (err?.message === "unauthorized") {
        clearAuth(); nav("/", { replace: true });
      } else {
        console.error("Failed to send message:", err);
        setMessages((prev) => [...prev, { role: "bot", text: "Maaf, pesan gagal dikirim." }]);
      }
    } finally {
      setIsTyping(false);
    }
  }

  // Profile / auth
  const user = useMemo(() => {
    try {
      const raw = localStorage.getItem("themis:user");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }, []);
  const displayName: string = user?.email || "Pengguna";
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const profileBtnRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!menuOpen) return;
      const t = e.target as Node;
      if (menuRef.current && !menuRef.current.contains(t) && !profileBtnRef.current?.contains(t)) {
        setMenuOpen(false);
      }
      if (menuFor) setMenuFor(null);
      if (renamingId) { setRenamingId(null); setDraftTitle(""); }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-[color:rgb(247_248_249)]/90 border-r border-gray-200/80 backdrop-blur-sm flex flex-col">
        <div className="p-4">
          <Link to="/chat" className="flex items-center gap-2 group">
            <div className="h-9 w-9 rounded-xl grid place-items-center ring-1 ring-gray-200 bg-white shadow-sm" style={{ backgroundColor: "var(--accent, #A3E1B0)" }}>
              <img src="/themis_logo.png" alt="ThemisAI" className="h-7 w-7" />
            </div>
            <span className="font-semibold tracking-wide group-hover:opacity-90">ThemisAI</span>
          </Link>

          <button
            type="button"
            onClick={handleNewChat}
            className="mt-6 w-full text-left p-2 rounded-lg hover:bg-accent/30 active:bg-gray-100 transition flex items-center gap-2 text-sm ring-1 ring-gray-200"
            aria-label="Mulai percakapan baru"
          >
            <PlusIcon className="h-4 w-4" />
            New Chat
          </button>
        </div>

        <div className="-mt-2 -mb-2 px-4 py-1 text-[11px] uppercase tracking-wide text-gray-500">
          Riwayat Chat
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-0 text-sm">
          {sessions.map((s) => {
            const isActive = currentSessionId === s.id;
            const isRenaming = renamingId === s.id;

            return (
              <div key={s.id} className="group relative flex items-center gap-2">
                {/* Title button OR inline rename input */}
                {!isRenaming ? (
                  <button
                    className={`flex-1 text-left p-2 rounded-lg transition ${isActive ? "bg-accent/30" : "hover:bg-accent/30"}`}
                    onClick={() => setCurrentSessionId(s.id)}
                    title={s.title || "Untitled"}
                  >
                    {s.title || "Untitled"}
                  </button>
                ) : (
                  <form
                    className="flex-1"
                    onSubmit={async (e) => {
                      e.preventDefault();
                      const newTitle = draftTitle.trim() || "Untitled";
                      try {
                        const updated = await renameSession(s.id, newTitle);
                        setSessions((prev) =>
                          prev.map((x) => (x.id === s.id ? { ...x, title: updated.title ?? newTitle } : x))
                        );
                      } catch (err) {
                        console.error("Failed to rename:", err);
                      } finally {
                        setRenamingId(null);
                        setDraftTitle("");
                        setMenuFor(null);
                      }
                    }}
                  >
                    <input
                      autoFocus
                      value={draftTitle}
                      onChange={(e) => setDraftTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          setRenamingId(null);
                          setDraftTitle("");
                        }
                      }}
                      placeholder={s.title || "Untitled"}
                      className={`w-full px-2 py-1.5 rounded-lg border ring-1 ring-gray-200 focus:outline-none focus:ring-2 focus:ring-[var(--accent,#A3E1B0)] ${isActive ? "bg-accent/20" : "bg-white"}`}
                    />
                  </form>
                )}

                {/* Kebab button */}
                <button
                  type="button"
                  className="h-8 w-8 rounded-lg text-gray-500 hover:bg-gray-100 grid place-items-center"
                  title="Menu"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuFor((prev) => (prev === s.id ? null : s.id));
                    // if switching to a different menu while editing, cancel rename
                    if (renamingId && renamingId !== s.id) {
                      setRenamingId(null);
                      setDraftTitle("");
                    }
                  }}
                >
                  {/* 3 dots icon (vertical) */}
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5" r="2" />
                    <circle cx="12" cy="12" r="2" />
                    <circle cx="12" cy="19" r="2" />
                  </svg>
                </button>

                {/* Kebab menu popover */}
                {menuFor === s.id && (
                  <div
                    className="absolute right-0 top-9 z-50 w-40 rounded-xl border bg-white shadow-lg ring-1 ring-black/5 p-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-accent/30"
                      onClick={() => {
                        setRenamingId(s.id);
                        setDraftTitle(s.title || "");
                      }}
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      className="w-full text-left px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50"
                      onClick={(e) => {
                        handleDeleteSession(e as any, s.id);
                        setMenuFor(null);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="p-3 border-t border-gray-200/80">
          <div className="relative">
            <button
              ref={profileBtnRef}
              type="button"
              className="w-full flex items-center gap-2 text-sm text-gray-700 hover:opacity-80"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span className="h-6 w-6 rounded-full bg-gray-100 ring-1 ring-gray-200 grid place-items-center">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4 text-gray-600" aria-hidden="true">
                  <path d="M12 2a5 5 0 110 10 5 5 0 010-10Zm0 12c4.418 0 8 2.239 8 5v1a1 1 0 01-1 1H5a1 1 0 01-1-1v-1c0-2.761 3.582-5 8-5Z" />
                </svg>
              </span>
              <span className="truncate">{displayName}</span>
            </button>

            {menuOpen && (
              <div ref={menuRef} role="menu" className="absolute right-0 bottom-10 z-50 w-44 rounded-xl border bg-white shadow-lg ring-1 ring-black/5 p-1">
                <button
                  type="button"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-accent/30 transition text-gray-800"
                  onClick={() => {
                    clearAuth();
                    nav("/", { replace: true });
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 text-gray-600" aria-hidden="true">
                    <path d="M13 3H7a2 2 0 00-2 2v14a2 2 0 002 2h6" />
                    <path d="M10 12h10" />
                    <path d="M17 9l3 3-3 3" />
                  </svg>
                  <span>Keluar</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Chat area */}
      <main className="relative flex-1 flex flex-col bg-white">
        <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-white/95 to-transparent pointer-events-none" />
        <div ref={listRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-4 pb-36" aria-live="polite" aria-label="Daftar pesan">
          {messages.map((m, i) => {
            const isLastMessage = i === messages.length - 1;
            const isLastBotBeforeTyping = isTyping && isLastMessage && m.role === "bot";

            return m.role === "user" ? (
              <div className="flex justify-end" key={i}>
                <div className="flex items-end gap-2 max-w-[80%]">
                  <div
                    className="px-4 py-2 rounded-2xl shadow-sm border whitespace-pre-wrap break-words"
                    style={{ backgroundColor: "#e2c693", borderColor: "#d8b86e", color: "#1a1a1a" }}
                  >
                    {m.text}
                  </div>
                </div>
              </div>
            ) : (
              <div
                key={i}
                className={`flex justify-start ${isLastBotBeforeTyping ? "mb-4" : ""}`}
              >
                <div className="max-w-[80%]">
                  <div
                    className="pl-3 border-l-4"
                    style={{ borderLeftColor: "var(--accent, #A3E1B0)" }}
                  >
                    <MarkdownBubble
                      text={m.text}
                      className="text-[15px] leading-relaxed text-gray-800"
                    />
                  </div>
                </div>
              </div>
            );
          })}


          {isTyping && (
            <div className="flex justify-start">
              <div className="max-w-[80%] pl-3 border-l-4" style={{ borderLeftColor: "var(--accent, #A3E1B0)" }}>
                <div className="text-gray-500">
                  <span className="inline-flex items-center gap-1">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-gray-400 animate-pulse" />
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-gray-300 animate-pulse [animation-delay:120ms]" />
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-gray-200 animate-pulse [animation-delay:240ms]" />
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Composer */}
        <form
          onSubmit={sendMessage}
          className="fixed bottom-0 left-64 right-0 px-4 pb-4 pt-2 bg-gradient-to-t from-white/95 to-transparent z-50"
        >

          <div className="mx-auto max-w-3xl flex items-center gap-2 rounded-2xl border bg-white/95 shadow-lg ring-1 ring-gray-200 px-3 py-2 backdrop-blur supports-[backdrop-filter]:bg-white/70">
            <input ref={fileInputRef} type="file" multiple className="hidden" onChange={onFileChange} aria-hidden="true" />
            <button
              type="button"
              onClick={triggerFileDialog}
              className="h-11 w-11 rounded-xl border border-gray-200 bg-gray-50 hover:bg-gray-100 flex items-center justify-center transition"
              title="Tambahkan file"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor" className="h-5 w-5 text-gray-600">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.44 11.05l-9.19 9.19a5.25 5.25 0 01-7.42-7.42l9.19-9.19a3.75 3.75 0 015.3 5.3l-9.2 9.2a2.25 2.25 0 01-3.18-3.19l8.48-8.48" />
              </svg>
            </button>

            <textarea
              ref={textareaRef}
              className="flex-1 min-h-[44px] px-3 py-2 resize-none rounded-xl outline-none placeholder:text-gray-400"
              style={{ maxHeight: MAX_TXTAREA_H }}
              placeholder="Tulis pertanyaan Anda..."
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                resizeTextarea(e.currentTarget);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (canSend) (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
                }
              }}
              aria-label="Kolom input pesan"
            />

            <button
              type="submit"
              className={[
                "h-11 w-11 rounded-xl grid place-items-center transition ring-1",
                canSend ? "bg-[var(--accent,#A3E1B0)] hover:opacity-90 text-gray-900 ring-[var(--accent,#A3E1B0)]/60" : "bg-gray-100 text-gray-400 ring-gray-200 cursor-not-allowed",
              ].join(" ")}
              title="Kirim"
              aria-disabled={!canSend}
              disabled={!canSend}
            >
              <PaperAirplaneIcon className="mb-0.5 h-5 w-5 -rotate-45" />
            </button>
          </div>

          {pendingFiles.length > 0 && (
            <div className="mx-auto max-w-3xl mt-2 flex flex-wrap gap-2 px-1">
              {pendingFiles.map((f, i) => (
                <span key={`${f.name}-${i}`} className="inline-flex items-center gap-2 px-2 py-1 rounded-lg border text-xs bg-white border-gray-200 text-gray-700">
                  <span className="truncate max-w-[14rem]" title={f.name}>
                    {f.name}
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className="whitespace-nowrap">{formatSize(f.size)}</span>
                  <button type="button" onClick={() => removePending(i)} className="ml-1 px-1 rounded hover:bg-gray-100 text-gray-500" aria-label={`Hapus ${f.name}`} title="Hapus">
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="mx-auto max-w-3xl mt-2 text-[12px] text-gray-500 px-1">
            Tekan <kbd className="px-1.5 py-0.5 rounded border bg-gray-50">Enter</kbd> untuk kirim,{" "}
            <kbd className="px-1.5 py-0.5 rounded border bg-gray-50">Shift</kbd>+<kbd className="px-1.5 py-0.5 rounded border bg-gray-50">Enter</kbd> untuk baris baru.
          </div>
        </form>
      </main>
    </div>
  );
}
