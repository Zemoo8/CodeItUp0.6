import { useEffect, useRef, useState } from "react";
import spongeMascot from "@/assets/sponge-mascot.png";

type Role = "bot" | "user";
interface Msg {
  id: number;
  role: Role;
  text: string;
}

const STARTERS: Msg[] = [
  { id: 1, role: "bot", text: "Howdy partner! I'm SpongeBot SquareChat 🍍 Ask me ANYTHING from Bikini Bottom!" },
  { id: 2, role: "bot", text: "I make Krabby Patties, terrible jokes, and questionable life choices. What'll it be?" },
];

const SPONGE_REPLIES = [
  "AYE AYE CAPTAIN! 🧽 That's a great question!",
  "Barnacles! Let me jellyfish that idea for ya...",
  "Patrick says hi from under his rock 🪨",
  "I'M READY! I'M READY! I'M READY!",
  "Order up! One fresh response, hold the pickles! 🍔",
  "Oh tartar sauce, that's a tough one... but I got you!",
  "Did somebody say... KRUSTY KRAB?? 🦀",
  "F is for friends who do stuff together! 🎶",
];

export function ChatBot() {
  const [messages, setMessages] = useState<Msg[]>(STARTERS);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typing]);

  const send = () => {
    const text = input.trim();
    if (!text) return;
    const userMsg: Msg = { id: Date.now(), role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      const reply = SPONGE_REPLIES[Math.floor(Math.random() * SPONGE_REPLIES.length)];
      setMessages((m) => [...m, { id: Date.now() + 1, role: "bot", text: reply }]);
      setTyping(false);
    }, 900 + Math.random() * 700);
  };

  return (
    <div className="relative z-10 mx-auto flex h-[78vh] w-full flex-col overflow-hidden rounded-[36px] outline-cartoon-thick shadow-[10px_10px_0_0_var(--ink)] bg-sponge-tex-tight">
      {/* Title bar — fan vibe, no fake OS dots */}
      <div className="relative flex items-center justify-between gap-4 border-b-[5px] border-[var(--ink)] bg-patrick-tex px-5 py-3">
        <div className="flex items-center gap-3">
          <img
            src={spongeMascot}
            alt=""
            width={56}
            height={56}
            className="h-14 w-14 animate-wobble drop-shadow-[3px_3px_0_var(--ink)]"
          />
          <div className="leading-tight">
            <h1 className="text-2xl md:text-3xl tracking-wider text-[var(--ink)] drop-shadow-[2px_2px_0_oklch(0.99_0_0)]">
              SpongeBot SquareChat
            </h1>
            <p className="text-xs md:text-sm text-[var(--ink)]/80">
              Powered by jellyfish, friendship & Krabby Patties 🍔
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border-[3px] border-[var(--ink)] bg-[var(--bubble)] px-3 py-1.5 shadow-[3px_3px_0_var(--ink)]">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[oklch(0.78_0.2_140)] opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full border-2 border-[var(--ink)] bg-[oklch(0.78_0.2_140)]" />
          </span>
          <span className="text-sm font-bold uppercase tracking-wider text-[var(--ink)]">
            I'm Ready!
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar with mascot */}
        <aside className="hidden md:flex w-[220px] flex-col items-center justify-between border-r-[5px] border-[var(--ink)] bg-[var(--bubble)] p-4">
          <div className="text-center">
            <p className="font-[var(--font-display)] text-2xl text-[var(--ink)]">Best Friends</p>
            <p className="text-xs text-[var(--ink)]/70">always online 🪼</p>
          </div>
          <img
            src={spongeMascot}
            alt="SpongeBot mascot waving hello"
            width={180}
            height={180}
            className="animate-bob drop-shadow-[4px_4px_0_var(--ink)]"
          />
          <div className="rounded-2xl border-[3px] border-[var(--ink)] bg-[var(--sponge)] px-3 py-2 text-center text-sm shadow-[3px_3px_0_var(--ink)]">
            "Ask me anything, neighbor!"
          </div>
        </aside>

        {/* Messages — sponge-textured chat surface */}
        <div className="flex flex-1 flex-col min-h-0 bg-sponge-tex relative">
          <div className="absolute inset-0 bg-[oklch(0.95_0.12_100)]/30" />
          <div
            ref={scrollRef}
            className="cartoon-scroll relative flex-1 overflow-y-auto px-4 py-6 md:px-8 space-y-5"
          >
            {messages.map((m) => (
              <Bubble key={m.id} msg={m} />
            ))}
            {typing && <TypingBubble />}
          </div>

          {/* Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
            className="relative flex items-center gap-3 border-t-[5px] border-[var(--ink)] bg-[var(--bubble)] p-4"
          >
            <div className="flex-1 rounded-2xl border-[4px] border-[var(--ink)] bg-white shadow-[inset_3px_3px_0_oklch(0.9_0.04_100)]">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message to SpongeBot..."
                className="w-full bg-transparent px-4 py-3 text-lg outline-none placeholder:text-[oklch(0.55_0.05_250)]"
              />
            </div>
            <button
              type="submit"
              className="group relative rounded-2xl border-[4px] border-[var(--ink)] bg-[var(--tie-red)] px-6 py-3 text-lg uppercase tracking-wider text-white shadow-[4px_4px_0_var(--ink)] transition-transform active:translate-x-1 active:translate-y-1 active:shadow-none hover:-translate-y-0.5"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Send! 🫧
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isBot = msg.role === "bot";
  return (
    <div className={`flex animate-pop-in ${isBot ? "justify-start" : "justify-end"}`}>
      <div
        className={`relative max-w-[78%] rounded-[28px] outline-cartoon px-5 py-3 shadow-[4px_4px_0_var(--ink)] ${
          isBot
            ? "bg-[var(--bubble)] text-[var(--ink)] bubble-tail-left"
            : "bg-[var(--patrick)] text-[var(--ink)] bubble-tail-right"
        }`}
      >
        <div className={`mb-1 text-xs font-bold uppercase tracking-widest ${isBot ? "text-[var(--tie-red)]" : "text-[var(--pants-brown)]"}`}>
          {isBot ? "SpongeBot" : "You"}
        </div>
        <p className="text-lg leading-snug">{msg.text}</p>
      </div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex justify-start animate-pop-in">
      <div className="relative rounded-[28px] outline-cartoon bg-[var(--bubble)] px-5 py-4 shadow-[4px_4px_0_var(--ink)] bubble-tail-left">
        <div className="flex items-end gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="block h-3 w-3 rounded-full bg-[var(--tie-red)] border-2 border-[var(--ink)]"
              style={{ animation: `typing-dot 1.1s ${i * 0.18}s infinite` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
