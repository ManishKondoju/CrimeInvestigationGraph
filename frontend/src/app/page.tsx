"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { EASE, RuledGrid, StatusLight, TypeOut } from "@/components/ui/motion";

// Index page. Not a marketing hero - a terminal boot screen and a
// dispatch board of available modules, per the Tactical Telemetry
// archetype (industrial-brutalist-ui skill).

const MODULES = [
  { id: "D-01", label: "AI ASSISTANT", href: "/chat", desc: "NATURAL-LANGUAGE QUERY // LANGGRAPH AGENT", status: "ONLINE" },
  { id: "D-02", label: "NETWORK", href: "/network", desc: "FORCE-DIRECTED ASSOCIATION GRAPH", status: "ONLINE" },
  { id: "D-03", label: "GEOSPATIAL", href: "/geo", desc: "INCIDENT MAP // DBSCAN HOTSPOTS", status: "ONLINE" },
  { id: "D-04", label: "SCHEMA", href: "/schema", desc: "LIVE GRAPH STRUCTURE // EXPORTS", status: "ONLINE" },
  { id: "D-05", label: "DASHBOARD", href: "/dashboard", desc: "EXECUTIVE OVERVIEW // THREAT POSTURE", status: "ONLINE" },
  { id: "D-06", label: "TIMELINE", href: null, desc: "TEMPORAL PATTERN ANALYSIS", status: "OFFLINE" },
  { id: "D-07", label: "ALGORITHMS", href: null, desc: "CENTRALITY // COMMUNITY DETECTION", status: "OFFLINE" },
];

export default function Home() {
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
          <h1 className="display text-[clamp(3rem,13vw,11rem)] text-phosphor">
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

        {/* Dispatch board */}
        <div className="telemetry mb-2 flex items-center justify-between text-phosphor-faint">
          <span>[ MODULE INDEX ]</span>
          <span>{">>>"}</span>
        </div>

        <RuledGrid className="grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((m, i) => {
            const online = !!m.href;
            const body = (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.1 + i * 0.05 }}
                className={`group relative flex h-full flex-col justify-between bg-substrate-raised p-4 transition-colors duration-150 ${
                  online ? "hover:bg-hazard" : "opacity-45"
                }`}
              >
                <div className="flex items-start justify-between">
                  <span className="telemetry text-phosphor-faint group-hover:text-substrate">
                    {m.id}
                  </span>
                  <span
                    className={`telemetry ${
                      online ? "text-terminal group-hover:text-substrate" : "text-phosphor-faint"
                    }`}
                  >
                    {m.status}
                  </span>
                </div>

                <div className="mt-10">
                  <div className="display text-2xl text-phosphor group-hover:text-substrate">
                    {m.label}
                  </div>
                  <div className="telemetry mt-1.5 text-phosphor-dim group-hover:text-substrate/80">
                    {m.desc}
                  </div>
                </div>

                {online && (
                  <div className="telemetry mt-4 flex items-center justify-between text-phosphor-faint group-hover:text-substrate">
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
