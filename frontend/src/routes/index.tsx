import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, useCallback } from "react";
import { SpongeLayout } from "@/components/SpongeLayout";
import sandyAvatar from "@/assets/acorn-gemini.png";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Acorn AI — Sandy's Treedome Lab" },
      { name: "description", content: "Chat with Acorn AI for grounded lab planning, inventory, and research support." },
    ],
  }),
  component: ChatPage,
});

// ── Types ─────────────────────────────────────────────────────────────────────

type AgentId = "research" | "inventory" | "planner";

interface Agent {
  id: AgentId;
  name: string;
  icon: string;
}

const AGENTS: Agent[] = [
  { id: "research",  name: "Research Agent",  icon: "🔍" },
  { id: "inventory", name: "Inventory Agent", icon: "📦" },
  { id: "planner",   name: "Planner Agent",   icon: "🧠" },
];

interface Msg {
  id: number;
  role: "user" | "ai";
  text: string;
  agent?: AgentId;
  error?: boolean;
}

const SUGGESTED = [
  "Show me inventory status",
  "What experiments can I run with current stock?",
  "Tell me about the projects",
  "What should I work on today?",
  "Do I have any low-stock items?",
  "Which projects are blocked or delayed?",
  "Give me a quick action plan",
  "What should I prioritize first?",
  "What is the lab status right now?",
];

// ── Voice helpers (client-only) ────────────────────────────────────────────────

function getSandyVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find((v) => v.lang === "en-US" && /female|zira|susan|samantha|karen/i.test(v.name)) ??
    voices.find((v) => v.lang.startsWith("en") && /female|zira|susan|samantha|karen/i.test(v.name)) ??
    voices.find((v) => v.lang === "en-US") ??
    voices[0] ??
    null
  );
}

function speak(text: string) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.voice = getSandyVoice();
  utt.pitch = 1.15;
  utt.rate = 1.1;
  window.speechSynthesis.speak(utt);
}

// ── SpeechRecognition shim ───────────────────────────────────────────────────���─

interface ISpeechRecognitionEvent {
  results: { [i: number]: { [j: number]: { transcript: string } } };
}
interface ISpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  onresult: ((e: ISpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
}
interface SpeechRecognitionCtor { new(): ISpeechRecognition; }
declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionCtor;
    webkitSpeechRecognition: SpeechRecognitionCtor;
  }
}

// ── API ────────────────────────────────────────────────────────────────────────

// Use absolute URL — relative URLs go through TanStack Start's SSR server, not the backend
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

interface ChatResponse {
  reply: string;
  data_source: string;
  agent_used?: string | null;
  error?: boolean;
}

interface ChatMessagePayload {
  role: "user" | "assistant";
  content: string;
}

function normalizeAgent(agentUsed?: string | null): AgentId {
  switch (agentUsed) {
    case "inventory_agent":
      return "inventory";
    case "research_agent":
      return "research";
    default:
      return "planner";
  }
}

async function callChat(
  message: string,
  history: ChatMessagePayload[],
  signal: AbortSignal,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
    signal,
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}

// ── Component ──────────────────────────────────────────────────────────────────

function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: 1,
      role: "ai",
      text: "Hi Sandy. I am Acorn AI. Ask me about inventory, project risks, experiments, or what to work on today.",
      agent: "planner",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceOn, setVoiceOn] = useState(false);
  // hasSR starts false on server AND client — set in useEffect to avoid hydration mismatch
  const [hasSR, setHasSR] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const recogRef = useRef<ISpeechRecognition | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setHasSR(!!(window.SpeechRecognition || window.webkitSpeechRecognition));
    if ("speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.addEventListener("voiceschanged", () =>
        window.speechSynthesis.getVoices()
      );
    }
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  // Stream the reply word-by-word after receiving full text
  const streamReply = useCallback(
    (text: string, agent: AgentId) => {
      const id = Date.now() + 1;
      setMessages((m) => [...m, { id, role: "ai", text: "", agent }]);
      const words = text.split(" ");
      let i = 0;
      const tick = setInterval(() => {
        i++;
        setMessages((m) =>
          m.map((msg) => (msg.id === id ? { ...msg, text: words.slice(0, i).join(" ") } : msg))
        );
        if (i >= words.length) {
          clearInterval(tick);
          setBusy(false);
          if (voiceOn) speak(text.replace(/[*_`#[\]>]/g, ""));
        }
      }, 30);
    },
    [voiceOn]
  );

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || busy) return;
      setInput("");
      setBusy(true);
      setMessages((m) => [...m, { id: Date.now(), role: "user", text: trimmed }]);

      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      const timer = setTimeout(() => ctrl.abort(), 20000); // 20s hard timeout

      const history = [...messages, { id: Date.now(), role: "user", text: trimmed }]
        .slice(-8)
        .map((msg) => ({
          role: msg.role === "ai" ? ("assistant" as const) : ("user" as const),
          content: msg.text,
        }));

      try {
        const data = await callChat(trimmed, history, ctrl.signal);
        streamReply(data.reply, normalizeAgent(data.agent_used));
      } catch (err) {
        setBusy(false);
        const isTimeout = err instanceof Error && err.name === "AbortError";
        setMessages((m) => [
          ...m,
          {
            id: Date.now() + 2,
            role: "ai",
            text: isTimeout
              ? "Took too long — is the backend running? Start it with: uvicorn main:app --reload"
              : `Error: ${err instanceof Error ? err.message : "unknown"}\n\nMake sure the backend is running on port 8000.`,
            agent: "planner",
            error: true,
          },
        ]);
      } finally {
        clearTimeout(timer);
      }
    },
    [busy, streamReply]
  );

  const toggleListen = useCallback(() => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Ctor) return;
    if (listening) {
      recogRef.current?.stop();
      setListening(false);
      return;
    }
    const recog = new Ctor();
    recog.lang = "en-US";
    recog.interimResults = false;
    recog.maxAlternatives = 1;
    recog.onresult = (e: ISpeechRecognitionEvent) => {
      const t = e.results[0][0].transcript;
      setInput(t);
      setListening(false);
      send(t);
    };
    recog.onerror = () => setListening(false);
    recog.onend = () => setListening(false);
    recogRef.current = recog;
    recog.start();
    setListening(true);
  }, [listening, send]);

  return (
    <SpongeLayout fullBleed>
      <div className="flex h-screen w-full overflow-hidden">
        <aside
          className={`relative flex flex-col border-r-[4px] border-[var(--ink)] bg-[var(--sand)]/88 backdrop-blur-sm transition-all duration-300 ${
            sidebarOpen ? "w-72" : "w-0 overflow-hidden"
          }`}
        >
          <div className="flex h-full flex-col gap-4 overflow-y-auto p-4 cartoon-scroll">
            <div className="rounded-[1.75rem] border-[3px] border-[var(--ink)] bg-white/75 p-4 shadow-[4px_4px_0_var(--ink)]">
              <div className="flex items-center gap-3">
                <img
                  src={sandyAvatar}
                  alt="Sandy"
                  width={52}
                  height={52}
                  className="h-12 w-12 rounded-2xl border-[3px] border-[var(--ink)] bg-white object-contain shadow-[2px_2px_0_var(--ink)]"
                />
                <div>
                  <div className="text-[10px] uppercase tracking-[0.28em] text-[var(--coral)]">Sandy&apos;s side</div>
                  <h2 className="text-2xl text-[var(--ink)]">You ask, bot answers</h2>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-[var(--ink)]/78">
                Keep Sandy as the person talking to the assistant. The bot stays on the right side of the logic and the UI simply presents the conversation cleanly.
              </p>
            </div>

            <button
              onClick={() =>
                setMessages([
                  { id: Date.now(), role: "ai", text: "Fresh start! I am Acorn AI and ready for your next lab question.", agent: "planner" },
                ])
              }
              className="w-full rounded-xl border-[3px] border-[var(--ink)] bg-[var(--coral)] px-3 py-2.5 text-sm uppercase tracking-wider text-white shadow-[3px_3px_0_var(--ink)] transition-transform hover:-translate-y-0.5"
              style={{ fontFamily: "var(--font-display)" }}
            >
              + New Chat
            </button>
            <button
              onClick={() => setVoiceOn((v) => !v)}
              className={`w-full rounded-xl border-[3px] border-[var(--ink)] px-3 py-2.5 text-sm uppercase tracking-wider shadow-[3px_3px_0_var(--ink)] transition-transform hover:-translate-y-0.5 ${
                voiceOn ? "bg-[var(--teal)] text-white" : "bg-white text-[var(--ink)]"
              }`}
              style={{ fontFamily: "var(--font-display)" }}
            >
              {voiceOn ? "🔊 Voice On" : "🔇 Voice Off"}
            </button>
          </div>
        </aside>

        <button
          onClick={() => setSidebarOpen((v) => !v)}
          className="absolute top-1/2 z-30 -translate-y-1/2 rounded-r-xl border-[3px] border-l-0 border-[var(--ink)] bg-[var(--coral)] px-1.5 py-3 text-white shadow-[3px_3px_0_var(--ink)]"
          style={{ left: sidebarOpen ? 288 : 0 }}
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? "◀" : "▶"}
        </button>

        <section className="relative flex h-full flex-1 flex-col bg-[var(--bubble)]/20 backdrop-blur-sm">
          <div className="border-b-[3px] border-[var(--ink)] bg-[var(--sand)]/70 px-4 py-3 md:px-6 md:py-3">
            <div className="mx-auto flex max-w-5xl flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border-[2px] border-[var(--ink)] bg-white px-3 py-1 text-[10px] uppercase tracking-[0.28em] text-[var(--coral)] shadow-[2px_2px_0_var(--ink)]">
                  <span className="h-2 w-2 rounded-full bg-[var(--teal)] animate-pulse" />
                  Sandy is chatting with Acorn AI
                </div>
                <h1 className="mt-2 text-3xl text-[var(--ink)] md:text-4xl">
                  Acorn AI
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ink)]/75 md:text-base">
                  The interface stays playful, but the answers stay grounded in the live data.
                </p>
              </div>
              <div className="grid gap-2 sm:grid-cols-3 lg:w-[28rem]">
                {[
                  { label: "Grounded data", value: "API first" },
                  { label: "Voice input", value: hasSR ? "Ready" : "Not supported" },
                  { label: "Follow-ups", value: "Context aware" },
                ].map((item) => (
                  <div key={item.label} className="rounded-[1.25rem] border-[2px] border-[var(--ink)] bg-white/80 px-4 py-3 shadow-[2px_2px_0_var(--ink)]">
                    <div className="text-[10px] uppercase tracking-[0.24em] text-[var(--ink)]/50">{item.label}</div>
                    <div className="mt-1 text-sm font-semibold text-[var(--ink)]">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col px-4 py-3 md:px-6 md:py-3">
            {busy && (
              <div className="animate-pop-in mb-4 rounded-[1.25rem] border-[3px] border-[var(--ink)] bg-[var(--coral)] px-4 py-2 text-center text-sm font-bold text-white shadow-[3px_3px_0_var(--ink)]">
                Acorn AI is thinking...
              </div>
            )}

            <div ref={scrollRef} className="cartoon-scroll mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 overflow-y-auto rounded-[2rem] border-[3px] border-[var(--ink)] bg-white/55 p-4 shadow-[4px_4px_0_var(--ink)] md:p-6">
              {messages.map((m) => (
                <Bubble key={m.id} msg={m} />
              ))}
              {busy && <TypingBubble />}
            </div>

            <div className="mx-auto mt-3 flex w-full max-w-5xl gap-2 overflow-x-auto rounded-[1.5rem] border-[3px] border-[var(--ink)] bg-[var(--sand)]/65 px-4 py-2 shadow-[3px_3px_0_var(--ink)]">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={busy}
                  className="shrink-0 rounded-full border-[2px] border-[var(--ink)] bg-white px-3 py-1 text-xs text-[var(--ink)] shadow-[2px_2px_0_var(--ink)] transition-transform hover:-translate-y-0.5 disabled:opacity-40"
                >
                  {s}
                </button>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="mx-auto mt-4 w-full max-w-5xl rounded-[1.75rem] border-[3px] border-[var(--ink)] bg-white/90 p-3 shadow-[4px_4px_0_var(--ink)] md:p-4"
            >
              <div className="flex items-end gap-3">
                {hasSR && (
                  <button
                    type="button"
                    onClick={toggleListen}
                    disabled={busy}
                    className={`shrink-0 rounded-2xl border-[3px] border-[var(--ink)] px-3 py-3 text-lg shadow-[3px_3px_0_var(--ink)] transition-transform hover:-translate-y-0.5 disabled:opacity-50 ${
                      listening ? "bg-[var(--tie-red)] text-white animate-pulse" : "bg-[var(--sand)] text-[var(--ink)]"
                    }`}
                    aria-label={listening ? "Stop listening" : "Start voice input"}
                  >
                    🎤
                  </button>
                )}
                <div className="flex-1 rounded-2xl border-[3px] border-[var(--ink)] bg-[var(--bubble)]/60 shadow-[inset_3px_3px_0_oklch(0.92_0.04_80)]">
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={listening ? "Listening…" : "Sandy, ask Acorn AI something..."}
                    className="w-full bg-transparent px-4 py-3 text-base outline-none placeholder:text-[var(--ink)]/40"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!input.trim() || busy}
                  className="rounded-2xl border-[3px] border-[var(--ink)] bg-[var(--teal)] px-5 py-3 text-base uppercase tracking-wider text-white shadow-[3px_3px_0_var(--ink)] transition-transform active:translate-x-1 active:translate-y-1 active:shadow-none hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </SpongeLayout>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  const agent = AGENTS.find((a) => a.id === msg.agent);
  return (
    <div className={`flex animate-pop-in gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {isUser && (
        <img
          src={sandyAvatar}
          alt=""
          width={40}
          height={40}
          className="h-10 w-10 shrink-0 rounded-full border-[3px] border-[var(--ink)] bg-white object-contain shadow-[2px_2px_0_var(--ink)]"
        />
      )}
      <div
        className={`relative max-w-[78%] rounded-2xl border-[3px] border-[var(--ink)] px-4 py-3 shadow-[4px_4px_0_var(--ink)] ${
          isUser
            ? "bg-[var(--teal)] text-white"
            : msg.error
              ? "bg-[var(--tie-red)]/20 text-[var(--ink)]"
              : "bg-[var(--sand)] text-[var(--ink)]"
        }`}
      >
        <div className={`mb-1 text-[10px] font-bold uppercase tracking-widest ${isUser ? "text-white/80" : "text-[var(--coral)]"}`}>
          {isUser ? "Sandy" : "Acorn AI"}
        </div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</div>
        {!isUser && agent && msg.text && (
          <div className="mt-2 inline-flex items-center gap-1 rounded-full border-[2px] border-[var(--ink)] bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--ink)]">
            <span>{agent.icon}</span>
            <span>{agent.name}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex animate-pop-in gap-3">
      <img
        src={sandyAvatar}
        alt=""
        width={40}
        height={40}
        className="h-10 w-10 shrink-0 rounded-full border-[3px] border-[var(--ink)] bg-white object-contain shadow-[2px_2px_0_var(--ink)]"
      />
      <div className="rounded-2xl border-[3px] border-[var(--ink)] bg-[var(--sand)] px-5 py-4 shadow-[4px_4px_0_var(--ink)]">
        <div className="flex items-end gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="block h-2.5 w-2.5 rounded-full border-[1.5px] border-[var(--ink)] bg-[var(--coral)]"
              style={{ animation: `typing-dot 1.1s ${i * 0.18}s infinite` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
