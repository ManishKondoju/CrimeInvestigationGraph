"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  PaperPlaneRight,
  CaretDown,
  Code,
  Database,
  CircleNotch,
} from "@phosphor-icons/react";
import { motion, AnimatePresence } from "motion/react";
import { postChat, ApiError } from "@/lib/api";
import type { ChatTurn } from "@/lib/types";

// AI Assistant page - step 12 of the FastAPI + Next.js rebuild. Parity target:
// app.py's chat_message loop (app.py:926-949) - same two-level transparency
// panel (numbered Cypher blocks, then a nested raw-JSON section), same quick
// question shortcuts (app.py:872-897). Visual language matches src/app/page.tsx
// (Ethereal Glass + Double-Bezel, per the high-end-visual-design skill).

const QUICK_QUESTIONS = [
  { label: "Database stats", question: "Give me database statistics" },
  { label: "List gangs", question: "Which criminal organizations operate in Chicago?" },
  { label: "Repeat offenders", question: "Who are the repeat offenders with multiple crimes?" },
  { label: "Armed suspects", question: "Show me armed gang members" },
  { label: "Crime hotspots", question: "Which locations have the most crimes?" },
  { label: "Investigators", question: "Show all investigators and their workload" },
];

function DoubleBezel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-[1.5rem] bg-white/5 p-1.5 ring-1 ring-white/10 ${className}`}>
      <div className="h-full rounded-[calc(1.5rem-0.375rem)] bg-zinc-950/80 shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] backdrop-blur-2xl">
        {children}
      </div>
    </div>
  );
}

function TransparencyPanel({ turn }: { turn: ChatTurn }) {
  const [open, setOpen] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  if (!turn.cypher_queries?.length) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="group flex items-center gap-2 rounded-full bg-white/5 px-3 py-1.5 text-xs font-medium text-zinc-400 ring-1 ring-white/10 transition-colors duration-500 hover:text-zinc-200"
      >
        <Code weight="light" className="h-3.5 w-3.5" />
        View Cypher Queries
        <CaretDown
          weight="bold"
          className={`h-3 w-3 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${open ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <DoubleBezel className="mt-2">
              <div className="space-y-3 p-4">
                <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                  Graph queries executed
                </p>
                {turn.cypher_queries.map((q, i) => (
                  <div key={i}>
                    <p className="mb-1 text-xs font-medium text-zinc-300">
                      {i + 1}. {q.name}
                    </p>
                    <pre className="overflow-x-auto rounded-xl bg-black/40 p-3 font-mono text-[11px] leading-relaxed text-emerald-300/90 ring-1 ring-white/5">
                      {q.cypher}
                    </pre>
                  </div>
                ))}

                <button
                  onClick={() => setShowRaw((v) => !v)}
                  className="flex items-center gap-2 pt-1 text-xs font-medium text-zinc-500 transition-colors duration-500 hover:text-zinc-300"
                >
                  <Database weight="light" className="h-3.5 w-3.5" />
                  Raw Data
                  <CaretDown
                    weight="bold"
                    className={`h-3 w-3 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${showRaw ? "rotate-180" : ""}`}
                  />
                </button>

                {showRaw && turn.context && (
                  <div className="space-y-3">
                    {Object.entries(turn.context).map(([key, value]) => {
                      if (!value || (Array.isArray(value) && value.length === 0)) return null;
                      const preview = Array.isArray(value) ? value.slice(0, 3) : value;
                      return (
                        <div key={key}>
                          <p className="mb-1 text-xs font-medium text-zinc-300">
                            {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                          </p>
                          <pre className="overflow-x-auto rounded-xl bg-black/40 p-3 font-mono text-[11px] leading-relaxed text-zinc-400 ring-1 ring-white/5">
                            {JSON.stringify(preview, null, 2)}
                          </pre>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </DoubleBezel>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ChatPage() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  async function send(question: string) {
    if (!question.trim() || loading) return;
    setError(null);

    const history = turns.map(({ role, content }) => ({ role, content }));
    setTurns((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const result = await postChat({ question, conversation_history: history });
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          cypher_queries: result.cypher_queries,
          context: result.context,
        },
      ]);
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Failed to reach the investigation agent.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-[100dvh] flex-col overflow-hidden px-4 py-10 sm:px-8">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-1/4 top-0 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-violet-600/15 blur-[120px]" />
        <div className="absolute right-0 top-1/2 h-[28rem] w-[28rem] translate-x-1/3 rounded-full bg-emerald-500/10 blur-[120px]" />
      </div>

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-white/5 ring-1 ring-white/10 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-x-0.5"
          >
            <ArrowLeft weight="light" className="h-4 w-4 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-zinc-50">
              AI Investigation Assistant
            </h1>
            <p className="text-xs text-zinc-500">
              Powered by a LangGraph agent over the Neo4j knowledge graph
            </p>
          </div>
        </div>

        {turns.length === 0 && (
          <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q.label}
                onClick={() => send(q.question)}
                className="rounded-2xl bg-white/5 px-4 py-3 text-left text-xs font-medium text-zinc-300 ring-1 ring-white/10 transition-colors duration-500 hover:bg-white/10 hover:text-zinc-50"
              >
                {q.label}
              </button>
            ))}
          </div>
        )}

        <div className="flex-1 space-y-5">
          {turns.map((turn, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              {turn.role === "user" ? (
                <div className="max-w-[80%] rounded-2xl bg-zinc-50 px-4 py-2.5 text-sm text-zinc-950">
                  {turn.content}
                </div>
              ) : (
                <div className="max-w-[85%]">
                  <DoubleBezel>
                    <div className="whitespace-pre-wrap p-4 text-sm leading-relaxed text-zinc-200">
                      {renderMarkdownBold(turn.content)}
                    </div>
                  </DoubleBezel>
                  <TransparencyPanel turn={turn} />
                </div>
              )}
            </motion.div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <CircleNotch weight="bold" className="h-3.5 w-3.5 animate-spin" />
              Investigating...
            </div>
          )}

          {error && (
            <div className="rounded-2xl bg-red-500/10 px-4 py-2.5 text-xs text-red-300 ring-1 ring-red-500/20">
              {error}
            </div>
          )}

          <div ref={scrollRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="sticky bottom-6 mt-6 flex items-center gap-2 rounded-full bg-white/5 p-1.5 ring-1 ring-white/10 backdrop-blur-2xl"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about crimes, suspects, gangs, evidence..."
            className="flex-1 bg-transparent px-4 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-50 text-zinc-950 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] disabled:opacity-30"
          >
            <PaperPlaneRight weight="bold" className="h-4 w-4" />
          </button>
        </form>
      </div>
    </main>
  );
}

// Minimal **bold** -> <strong> renderer, matching the agent's markdown-lite
// output style (see langgraph_agent.py's ANSWER_SYSTEM_PROMPT).
function renderMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-zinc-50">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}
