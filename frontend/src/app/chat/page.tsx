"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "motion/react";
import { postChat, ApiError } from "@/lib/api";
import type { ChatTurn } from "@/lib/types";
import {
  EASE,
  LoadingBlocks,
  PageHeader,
  Panel,
  TerminalButton,
  GraphConstellation,
} from "@/components/ui/motion";

// AI Assistant terminal. Parity target: app.py's chat loop - same quick
// queries and the same two-level transparency panel (numbered Cypher, then
// raw JSON), restyled as an interrogation console.

const QUICK_QUESTIONS = [
  { code: "Q-01", label: "DATABASE STATS", question: "Give me database statistics" },
  { code: "Q-02", label: "ORGANIZATIONS", question: "Which criminal organizations operate in Chicago?" },
  { code: "Q-03", label: "REPEAT OFFENDERS", question: "Who are the repeat offenders with multiple crimes?" },
  { code: "Q-04", label: "ARMED SUSPECTS", question: "Show me armed gang members" },
  { code: "Q-05", label: "HOTSPOTS", question: "Which locations have the most crimes?" },
  { code: "Q-06", label: "INVESTIGATORS", question: "Show all investigators and their workload" },
];

function TransparencyPanel({ turn }: { turn: ChatTurn }) {
  const [open, setOpen] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  if (!turn.cypher_queries?.length) return null;

  return (
    <div className="mt-2 border-t border-rule">
      <button
        onClick={() => setOpen((v) => !v)}
        className="telemetry flex w-full items-center justify-between px-3 py-2 text-phosphor-faint transition-colors duration-150 hover:text-hazard"
      >
        <span>
          [ {open ? "-" : "+"} ] CYPHER TRACE // {turn.cypher_queries.length} QUERIES
        </span>
        <span>{open ? "COLLAPSE" : "EXPAND"}</span>
      </button>

      {/* Plain conditional, not AnimatePresence: the exit never resolved, so
          the panel expanded but could not be collapsed again. */}
      {open && (
        <div className="overflow-hidden border-t border-rule">
            <div className="space-y-3 p-3">
              {turn.cypher_queries.map((q, i) => (
                <div key={i} className="border border-rule">
                  <div className="telemetry flex items-center justify-between border-b border-rule bg-substrate px-2 py-1 text-phosphor-faint">
                    <span>
                      {String(i + 1).padStart(2, "0")} / {q.name}
                    </span>
                    <span className="text-hazard">CYPHER</span>
                  </div>
                  <pre className="overflow-x-auto bg-substrate p-2.5 text-[11px] leading-relaxed text-terminal">
                    {q.cypher}
                  </pre>
                </div>
              ))}

              <button
                onClick={() => setShowRaw((v) => !v)}
                className="telemetry text-phosphor-faint transition-colors duration-150 hover:text-hazard"
              >
                [ {showRaw ? "-" : "+"} ] RAW RECORDSET
              </button>

              {showRaw && turn.context && (
                <div className="space-y-2">
                  {Object.entries(turn.context).map(([key, value]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null;
                    const preview = Array.isArray(value) ? value.slice(0, 3) : value;
                    return (
                      <div key={key} className="border border-rule">
                        <div className="telemetry border-b border-rule bg-substrate px-2 py-1 text-phosphor-faint">
                          {key.replace(/_/g, " ")}
                          {Array.isArray(value) && ` // ${value.length} ROWS`}
                        </div>
                        <pre className="max-h-56 overflow-auto bg-substrate p-2.5 text-[11px] leading-relaxed text-phosphor-dim">
                          {JSON.stringify(preview, null, 2)}
                        </pre>
                      </div>
                    );
                  })}
                </div>
              )}
          </div>
        </div>
      )}
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
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col">
        <PageHeader
          unit="D-01"
          title="AI Assistant"
          subtitle="NATURAL-LANGUAGE INTERROGATION // LANGGRAPH AGENT OVER NEO4J"
          right={
            <span className="telemetry text-phosphor-faint">
              EXCHANGES / {String(turns.filter((t) => t.role === "user").length).padStart(3, "0")}
            </span>
          }
        />

        {/* Plain conditional rather than AnimatePresence: the exit animation
            never resolved here, so the block stayed mounted for the whole
            session instead of clearing once querying began. An instant switch
            also suits the terminal aesthetic better than an ease-out. */}
        {turns.length === 0 && (
          <div className="mb-5">
              <div className="telemetry mb-2 text-phosphor-faint">[ PRESET QUERIES ]</div>
              <div className="grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-3">
                {QUICK_QUESTIONS.map((q, i) => (
                  <motion.button
                    key={q.code}
                    onClick={() => send(q.question)}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.25, delay: i * 0.04 }}
                    className="group bg-substrate-raised p-3 text-left transition-colors duration-150 hover:bg-hazard"
                  >
                    <div className="telemetry text-phosphor-faint group-hover:text-substrate">
                      {q.code}
                    </div>
                    <div className="telemetry mt-1 text-phosphor group-hover:text-substrate">
                      {q.label}
                    </div>
                  </motion.button>
                ))}
            </div>
          </div>
        )}

        <div className="flex-1 space-y-3">
          {/* Standby visual: occupies the empty space between the presets and
              the input until the first query, then yields to the transcript. */}
          {turns.length === 0 && !loading && <GraphConstellation />}

          {turns.map((turn, i) =>
            turn.role === "user" ? (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, ease: EASE }}
                className="flex justify-end"
              >
                <div className="max-w-[85%] border border-hazard bg-hazard px-3 py-2 text-[13px] text-substrate">
                  <span className="telemetry mr-2 opacity-70">QUERY {">>"}</span>
                  {turn.content}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, ease: EASE }}
              >
                <Panel label={`RESPONSE / ${String(Math.ceil((i + 1) / 2)).padStart(2, "0")}`}>
                  <div className="whitespace-pre-wrap p-3 text-[13px] leading-relaxed text-phosphor-dim">
                    {renderMarkdownBold(turn.content)}
                  </div>
                  <TransparencyPanel turn={turn} />
                </Panel>
              </motion.div>
            ),
          )}

          {/* Plain conditional, not AnimatePresence: its exit never resolved,
              which left "INTERROGATING GRAPH" on screen after every query. */}
          {loading && (
            <div className="border border-rule bg-substrate-raised p-3">
              <LoadingBlocks label="INTERROGATING GRAPH // GENERATING CYPHER" />
            </div>
          )}

          {error && (
            <div className="border border-hazard bg-substrate-raised p-3">
              <div className="telemetry text-hazard">{"// FAULT"}</div>
              <div className="mt-1 text-[13px] text-phosphor-dim">{error}</div>
            </div>
          )}

          <div ref={scrollRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="sticky bottom-4 mt-5 flex border border-rule bg-substrate-raised"
        >
          <span className="telemetry hidden items-center border-r border-rule px-3 text-hazard sm:flex">
            {">"}
          </span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="ENTER QUERY..."
            className="flex-1 bg-transparent px-3 py-3 text-[13px] text-phosphor placeholder:text-phosphor-faint focus:outline-none"
          />
          <TerminalButton type="submit" disabled={loading || !input.trim()} accent className="border-y-0 border-r-0">
            TRANSMIT
          </TerminalButton>
        </form>
      </div>
    </main>
  );
}

// Minimal **bold** -> <strong>, matching the agent's markdown-lite output
// (see langgraph_agent.py's ANSWER_SYSTEM_PROMPT). Bold terms are the
// operative facts, so they get phosphor-white against dimmed body copy.
function renderMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-normal text-phosphor underline decoration-hazard decoration-1 underline-offset-2">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}
