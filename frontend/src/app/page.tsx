"use client";

import { useEffect, useState } from "react";
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
  SirenBeacon,
  StatusLight,
  TypeOut,
} from "@/components/ui/motion";
import { getActivity } from "@/lib/api";
import type { DashboardActivity } from "@/lib/types";

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
          <StatusLight label="NEO4J LINK ACTIVE" />
        </div>

        {/* Macro-typographic masthead - viewport-bleeding, tight, uppercase */}
        <div className="relative py-10 md:py-16">
          <div className="flex items-start gap-4">
            <h1 className="display text-[clamp(3rem,13vw,11rem)] text-phosphor">
              CRIME
              <br />
              GRAPH
              <span className="text-hazard">RAG</span>
            </h1>
            <div className="mt-2 md:mt-4">
              <SirenBeacon size={56} />
            </div>
          </div>

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
            <dl className="telemetry grid grid-cols-2 gap-x-6 gap-y-1 self-end text-phosphor-faint md:text-right">
              <dt>SUBSTRATE</dt>
              <dd className="text-phosphor-dim">NEO4J AURA</dd>
              <dt>AGENT</dt>
              <dd className="text-phosphor-dim">LANGGRAPH</dd>
              <dt>MODULES</dt>
              <dd className="text-phosphor-dim">5 / 7 ONLINE</dd>
            </dl>
          </div>
        </div>

        {/* Endless dispatch feed of real incidents from the graph */}
        <div className="mb-8">
          <IncidentTicker incidents={incidents} />
        </div>

        {/* Dispatch board */}
        <div className="telemetry mb-2 flex items-center justify-between text-phosphor-faint">
          <span>[ MODULE INDEX ]</span>
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
