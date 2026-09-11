"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "motion/react";
import {
  AssistantPreview,
  DashboardPreview,
  EASE,
  GeoPreview,
  NetworkPreview,
  SchemaPreview,
  IncidentTicker,
  RuledGrid,
  IncidentMap,
  StatusLight,
  TypeOut,
} from "@/components/ui/motion";
import { getActivity, getCrimeLocations, getKpis, getSchema } from "@/lib/api";
import type { CrimeLocation, DashboardActivity } from "@/lib/types";
import { AnimatedNumber } from "@/components/ui/motion";

// Index page. Not a marketing hero - a terminal boot screen and a
// dispatch board of available modules, per the Tactical Telemetry
// archetype (industrial-brutalist-ui skill).

interface Module {
  id: string;
  label: string;
  href: string | null;
  desc: string;
  status: string;
  /** Which preview scene the card carries, if any. Cards with a preview
   *  slide their scene in on hover rather than flood-filling with hazard. */
  preview?: keyof typeof PREVIEWS;
}

const SAMPLE_QUESTIONS = [
  "Which crimes share the same modus operandi?",
  "Show me everyone within 2 degrees of David Rodriguez",
  "Which suspects connect to multiple gangs?",
  "Are any suspects related to each other by family?",
];

const PREVIEWS = {
  assistant: AssistantPreview,
  network: NetworkPreview,
  geo: GeoPreview,
  schema: SchemaPreview,
  dashboard: DashboardPreview,
} as const;

const MODULES: Module[] = [
  { id: "D-01", label: "AI ASSISTANT", href: "/chat", desc: "NATURAL-LANGUAGE QUERY // LANGGRAPH AGENT", status: "ONLINE", preview: "assistant" },
  { id: "D-02", label: "NETWORK", href: "/network", desc: "FORCE-DIRECTED ASSOCIATION GRAPH", status: "ONLINE", preview: "network" },
  { id: "D-03", label: "GEOSPATIAL", href: "/geo", desc: "INCIDENT MAP // DBSCAN HOTSPOTS", status: "ONLINE", preview: "geo" },
  { id: "D-04", label: "SCHEMA", href: "/schema", desc: "LIVE GRAPH STRUCTURE // EXPORTS", status: "ONLINE", preview: "schema" },
  { id: "D-05", label: "DASHBOARD", href: "/dashboard", desc: "EXECUTIVE OVERVIEW // THREAT POSTURE", status: "ONLINE", preview: "dashboard" },
  { id: "D-06", label: "TIMELINE", href: null, desc: "TEMPORAL PATTERN ANALYSIS", status: "OFFLINE" },
  { id: "D-07", label: "ALGORITHMS", href: null, desc: "CENTRALITY // COMMUNITY DETECTION", status: "OFFLINE" },
];

export default function Home() {
  // Live incidents for the dispatch ticker. Best-effort: the backend sleeps
  // on Render's free tier, so a cold start can take ~50s - the ticker simply
  // doesn't render until data arrives rather than blocking the page.
  const [incidents, setIncidents] = useState<DashboardActivity["recent_incidents"]>([]);

  // The stats fetch doubles as the health probe: if the graph answers, the
  // link is genuinely up. A separate hardcoded "ACTIVE" badge would claim
  // the backend is reachable without ever checking.
  const [link, setLink] = useState<"live" | "down" | "checking">("checking");
  const [stats, setStats] = useState<{
    nodes: number; relationships: number; crimes: number; suspects: number;
  } | null>(null);

  // Real incident coordinates for the masthead map.
  const [mapPoints, setMapPoints] = useState<CrimeLocation[]>([]);

  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getKpis(), getSchema()])
      .then(([kpis, schema]) => {
        if (cancelled) return;
        setStats({
          nodes: schema.nodes.reduce((sum, n) => sum + n.count, 0),
          relationships: schema.relationships.reduce((sum, r) => sum + r.count, 0),
          crimes: kpis.total_crimes,
          suspects: kpis.total_persons,
        });
        setLink("live");
      })
      .catch(() => {
        if (!cancelled) setLink("down");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    // Capped well below the full set - this is a backdrop, and a few hundred
    // points already render the city's footprint.
    getCrimeLocations({ limit: 400 })
      .then((res) => {
        if (!cancelled) setMapPoints(res.rows);
      })
      .catch(() => {
        /* backdrop only - never block the page on it */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    getActivity()
      .then((a) => {
        if (!cancelled) setIncidents(a.recent_incidents);
      })
      .catch(() => {
        /* ticker is decorative - a failure here must not break the page */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto w-full max-w-[1400px]">
        {/* Top bar: system identity strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule pb-3">
          <span className="telemetry text-phosphor-faint">
            CRIMEGRAPHRAG® / TACTICAL INTELLIGENCE TERMINAL / REV 2.6
          </span>
          <StatusLight
            state={link}
            labels={{ live: "NEO4J LINK ACTIVE", down: "NEO4J UNREACHABLE", checking: "LINKING..." }}
          />
        </div>

        {/* Macro-typographic masthead - viewport-bleeding, tight, uppercase */}
        <div className="relative py-10 md:py-16">
          <IncidentMap points={mapPoints} />

          <h1 className="relative z-10 display text-[clamp(3rem,13vw,11rem)] text-phosphor">
            CRIME
            <br />
            GRAPH
            <span className="text-hazard">RAG</span>
          </h1>

          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.8, ease: EASE, delay: 0.2 }}
            className="my-5 h-[3px] origin-left bg-hazard"
          />

          <div className="grid gap-6 md:grid-cols-[1fr_auto]">
            <p className="max-w-[62ch] text-[13px] leading-relaxed text-phosphor-dim">
              <TypeOut
                text="CRIMINAL ASSOCIATION ANALYSIS OVER A NEO4J KNOWLEDGE GRAPH. NATURAL-LANGUAGE INTERROGATION IS ROUTED THROUGH A LANGGRAPH AGENT THAT WRITES ITS OWN CYPHER, VALIDATES RESULTS, AND RETRIES ON FAILURE."
                speed={12}
                startDelay={400}
              />
            </p>
            {/* Live readouts, not static claims - every number here is
                fetched from the graph on load. */}
            <dl className="grid shrink-0 grid-cols-2 gap-x-8 gap-y-2 self-end">
              {[
                ["NODES", stats?.nodes],
                ["RELATIONSHIPS", stats?.relationships],
                ["CRIMES", stats?.crimes],
                ["SUSPECTS", stats?.suspects],
              ].map(([label, value]) => (
                <div key={label as string} className="md:text-right">
                  <dt className="telemetry text-phosphor-faint">{label}</dt>
                  <dd className="display text-xl tabular-nums text-phosphor">
                    {value === undefined ? (
                      <span className="text-phosphor-faint">--</span>
                    ) : (
                      <AnimatedNumber value={value as number} />
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        {/* The product is natural-language interrogation, so it should be
            usable from the front door rather than three clicks away. */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!query.trim()) return;
            router.push(`/chat?q=${encodeURIComponent(query.trim())}`);
          }}
          className="mb-8 flex border border-rule bg-substrate-raised focus-within:border-hazard"
        >
          <span className="telemetry flex items-center px-3 text-hazard">{">"}</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="INTERROGATE THE GRAPH — E.G. WHICH CRIMES SHARE A MODUS OPERANDI?"
            className="telemetry flex-1 bg-transparent py-3 text-phosphor placeholder:text-phosphor-faint focus:outline-none"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="telemetry border-l border-rule px-4 text-phosphor-dim transition-colors duration-150 hover:bg-hazard hover:text-substrate disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-phosphor-dim"
          >
            TRANSMIT
          </button>
        </form>

        {/* Endless dispatch feed of real incidents from the graph */}
        <div className="mb-8">
          <IncidentTicker incidents={incidents} />
        </div>

        {/* Briefing: what this is, how it works, and what to ask it. The
            masthead line alone assumes the reader already knows what a
            LangGraph agent or a Cypher retry loop is. */}
        <div className="telemetry mb-2 flex items-center justify-between text-phosphor-faint">
          <span>[ BRIEFING ]</span>
          <span>{"///"}</span>
        </div>

        <RuledGrid className="mb-10 grid-cols-1 lg:grid-cols-3">
          <div className="bg-substrate-raised p-5">
            <div className="telemetry mb-3 text-hazard">01 / WHAT THIS IS</div>
            <p className="text-[13px] leading-relaxed text-phosphor-dim">
              A crime investigation tool built on a{" "}
              <span className="text-phosphor">knowledge graph</span> — people,
              crimes, weapons, vehicles, evidence and locations stored as a
              network of relationships rather than rows in a table. That makes
              it possible to ask questions that span many hops, like who is
              connected to whom, and through what.
            </p>
            <p className="mt-3 text-[13px] leading-relaxed text-phosphor-dim">
              You ask in plain English. No query language required.
            </p>
          </div>

          <div className="bg-substrate-raised p-5">
            <div className="telemetry mb-3 text-hazard">02 / HOW IT WORKS</div>
            <p className="text-[13px] leading-relaxed text-phosphor-dim">
              An agent translates your question into{" "}
              <span className="text-phosphor">Cypher</span> (the graph query
              language), runs it, then checks the result. If the query errors —
              or returns nothing — it rewrites and retries.
            </p>
            <div className="telemetry mt-4 space-y-1 text-phosphor-faint">
              <div>EXTRACT ENTITIES</div>
              <div>{"↓"} GENERATE CYPHER {"←┐"}</div>
              <div>{"↓"} EXECUTE QUERY {"  │"}</div>
              <div>{"↓"} VALIDATE {"───────┘"} <span className="text-hazard">RETRY</span></div>
              <div>{"↓"} ANSWER</div>
            </div>
            <p className="mt-4 text-[13px] leading-relaxed text-phosphor-dim">
              Every answer ships with the exact queries behind it, so you can
              check the work rather than trust it.
            </p>
          </div>

          <div className="bg-substrate-raised p-5">
            <div className="telemetry mb-3 text-hazard">03 / TRY IT</div>
            <p className="mb-3 text-[13px] leading-relaxed text-phosphor-dim">
              Run one of these against the live graph:
            </p>
            <div className="space-y-px">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => router.push(`/chat?q=${encodeURIComponent(q)}`)}
                  className="group/q flex w-full items-start gap-2 border border-rule bg-substrate p-2.5 text-left text-[12px] leading-snug text-phosphor-dim transition-colors duration-150 hover:border-hazard hover:text-phosphor"
                >
                  <span className="telemetry mt-0.5 text-hazard">{">"}</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        </RuledGrid>

        {/* Data provenance - the crimes are real, the people are not, and a
            crime-data project should say so plainly rather than imply
            otherwise. */}
        <div className="telemetry mb-10 border border-rule bg-substrate-raised p-4 leading-relaxed text-phosphor-faint">
          <span className="text-phosphor-dim">DATA //</span> 493 REAL INCIDENTS
          FROM THE CHICAGO OPEN DATA PORTAL, PLUS 177 SYNTHETIC INCIDENTS.{" "}
          <span className="text-hazard">
            ALL PERSONS, ORGANIZATIONS AND EVIDENCE ARE FICTIONAL
          </span>{" "}
          — GENERATED AS AN INTELLIGENCE LAYER SO THE GRAPH CAN BE EXPLORED
          WITHOUT EXPOSING ANYONE&apos;S REAL RECORD.
        </div>

        {/* Dispatch board */}
        <div className="telemetry mb-2 flex items-center justify-between text-phosphor-faint">
          <span>
            [ MODULE INDEX ] {MODULES.filter((m) => m.href).length} / {MODULES.length} ONLINE
          </span>
          <span>{">>>"}</span>
        </div>

        <RuledGrid className="grid-cols-1 overflow-visible md:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((m, i) => {
            const online = !!m.href;
            const body = (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.1 + i * 0.05 }}
                className={`group relative flex h-full flex-col justify-between overflow-hidden bg-substrate-raised p-4 ${
                  !online
                    ? "opacity-45"
                    : m.preview
                      // Preview cards keep their original footprint and expand
                      // on hover instead. Scaling (rather than growing the grid
                      // cell) means the card lifts over its neighbours without
                      // reflowing the whole board. They also can't use the
                      // hazard flood-fill - the scene would be unreadable
                      // against it - so they take a hazard edge instead.
                      // The card itself does not move or scale - scaling read
                      // as the card popping toward the viewer. The scene
                      // slides in laterally from the right edge instead.
                      ? "transition-colors duration-300 hover:ring-1 hover:ring-inset hover:ring-hazard"
                      : "transition-colors duration-150 hover:bg-hazard"
                }`}
              >
                {m.preview && (() => { const Scene = PREVIEWS[m.preview]; return <Scene />; })()}

                <div className="relative z-10 flex items-start justify-between">
                  <span
                    className={`telemetry text-phosphor-faint ${
                      m.preview ? "" : "group-hover:text-substrate"
                    }`}
                  >
                    {m.id}
                  </span>
                  <span
                    className={`telemetry ${
                      !online
                        ? "text-phosphor-faint"
                        : m.preview
                          ? "text-terminal"
                          : "text-terminal group-hover:text-substrate"
                    }`}
                  >
                    {m.status}
                  </span>
                </div>

                <div className={`relative z-10 mt-10 ${m.preview ? "preview-copy" : ""}`}>
                  <div
                    className={`display text-2xl text-phosphor ${
                      m.preview ? "" : "group-hover:text-substrate"
                    }`}
                  >
                    {m.label}
                  </div>
                  <div
                    className={`telemetry mt-1.5 text-phosphor-dim ${
                      m.preview ? "group-hover:text-phosphor" : "group-hover:text-substrate/80"
                    }`}
                  >
                    {m.desc}
                  </div>
                </div>

                {online && (
                  <div
                    className={`telemetry relative z-10 mt-4 flex items-center justify-between text-phosphor-faint ${
                      m.preview ? "group-hover:text-hazard" : "group-hover:text-substrate"
                    }`}
                  >
                    <span>ENGAGE</span>
                    <span className="transition-transform duration-150 group-hover:translate-x-1">
                      {"->"}
                    </span>
                  </div>
                )}
              </motion.div>
            );

            return online ? (
              <Link key={m.id} href={m.href!} className="block">
                {body}
              </Link>
            ) : (
              <div key={m.id}>{body}</div>
            );
          })}
        </RuledGrid>

        <div className="telemetry mt-6 flex flex-wrap items-center justify-between gap-2 border-t border-rule pt-3 text-phosphor-faint">
          <span>DAMG 7374 // KNOWLEDGE GRAPHS WITH GENAI // NORTHEASTERN UNIVERSITY</span>
          <span>© CHICAGO OPEN DATA + SYNTHETIC INTELLIGENCE LAYER</span>
        </div>
      </div>
    </main>
  );
}
