"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { EASE, PageHeader, Panel, Reveal, RuledGrid } from "@/components/ui/motion";

// About. The Streamlit original had one; this replaces it and gives the
// launch film somewhere to live inside the product rather than only in the
// repo README.

const PIPELINE = ["EXTRACT", "GENERATE", "EXECUTE", "VALIDATE", "ANSWER"];

const STACK = [
  ["GRAPH", "Neo4j Aura", "1,868 nodes · 2,738 relationships across 9 entity types"],
  ["AGENT", "LangGraph + Groq", "Writes its own Cypher, validates results, retries on failure"],
  ["API", "FastAPI", "Read-only query layer; every filter is $-parameterised"],
  ["CLIENT", "Next.js 16 · React 19", "This interface. Tailwind 4, no component library"],
  ["HOSTING", "Vercel + Render", "Frontend, API, and a managed graph database"],
];

export default function AboutPage() {
  // The film is ~8MB. preload="none" keeps it off the critical path - the
  // poster stands in until someone actually asks for it.
  const [armed, setArmed] = useState(false);

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto w-full max-w-[1400px]">
        <PageHeader
          unit="D-00"
          title="About"
          subtitle="WHAT THIS IS, HOW IT WORKS, AND WHAT IS ACTUALLY UNDERNEATH IT"
        />

        {/* ---------------- the film ---------------- */}
        <Panel label="LAUNCH FILM" right="24s" className="mb-4">
          <div className="relative aspect-video w-full bg-substrate">
            {armed ? (
              <video
                src="/crimegraphrag-demo.mp4"
                poster="/crimegraphrag-poster.jpg"
                controls
                autoPlay
                playsInline
                className="h-full w-full"
              />
            ) : (
              <button
                onClick={() => setArmed(true)}
                className="group relative h-full w-full"
                aria-label="Play the launch film"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/crimegraphrag-poster.jpg"
                  alt=""
                  className="h-full w-full object-cover opacity-70 transition-opacity duration-300 group-hover:opacity-90"
                />
                <span className="absolute inset-0 flex items-center justify-center">
                  <motion.span
                    whileHover={{ scale: 1.06 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className="flex items-center gap-4 border border-hazard bg-substrate/85 px-7 py-4 backdrop-blur-sm"
                  >
                    <span className="text-hazard">▶</span>
                    <span className="telemetry text-phosphor">PLAY WITH SOUND</span>
                  </motion.span>
                </span>
              </button>
            )}
          </div>
          <div className="telemetry border-t border-rule px-4 py-2.5 text-phosphor-faint">
            EVERY FIGURE, COORDINATE AND QUERY IN THE FILM IS PULLED FROM THE LIVE
            GRAPH — NOTHING IS MOCKED UP
          </div>
        </Panel>

        {/* ---------------- what / why ---------------- */}
        <RuledGrid className="mb-4 grid-cols-1 lg:grid-cols-2">
          <div className="bg-substrate-raised p-6">
            <div className="telemetry mb-3 text-hazard">01 / WHAT THIS IS</div>
            <p className="text-[13px] leading-relaxed text-phosphor-dim">
              Crime records are usually rows in a table, which makes the
              connections between them invisible. Here they are a{" "}
              <span className="text-phosphor">knowledge graph</span> — people,
              crimes, weapons, vehicles, evidence, locations and the
              relationships between them — so a question can cross many hops at
              once.
            </p>
            <p className="mt-3 text-[13px] leading-relaxed text-phosphor-dim">
              You ask in plain English. No query language required.
            </p>
          </div>

          <div className="bg-substrate-raised p-6">
            <div className="telemetry mb-3 text-hazard">02 / WHY IT IS DIFFERENT</div>
            <p className="text-[13px] leading-relaxed text-phosphor-dim">
              Most tools ask you to trust the answer. This one hands you the
              evidence: every response ships with the{" "}
              <span className="text-phosphor">exact Cypher</span> the agent
              wrote and the raw rows it got back, so you can check the work
              instead of taking it on faith.
            </p>
            <p className="mt-3 text-[13px] leading-relaxed text-phosphor-dim">
              It is also willing to be wrong. A query that errors — or returns
              nothing — is treated as a failure and rewritten.
            </p>
          </div>
        </RuledGrid>

        {/* ---------------- the loop ---------------- */}
        <Panel label="THE AGENT LOOP" right="LANGGRAPH" className="mb-4">
          <div className="p-6">
            <div className="flex flex-wrap items-center gap-2">
              {PIPELINE.map((step, i) => (
                <Reveal key={step} index={i} className="flex items-center gap-2">
                  <span
                    className={`telemetry border px-4 py-2.5 ${
                      step === "VALIDATE"
                        ? "border-hazard text-hazard"
                        : "border-rule text-phosphor-dim"
                    }`}
                  >
                    {step}
                  </span>
                  {i < PIPELINE.length - 1 && (
                    <span className="telemetry text-phosphor-faint">→</span>
                  )}
                </Reveal>
              ))}
            </div>
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.4, ease: EASE }}
              className="telemetry mt-4 flex items-center gap-2 text-hazard"
            >
              <span>└─</span> VALIDATE LOOPS BACK TO GENERATE — UP TO 2 RETRIES
            </motion.div>
            <p className="mt-5 max-w-[80ch] text-[13px] leading-relaxed text-phosphor-dim">
              <span className="text-phosphor">Zero rows counts as a failure</span>, not
              just an error. A query can be perfectly valid Cypher and still be
              the wrong question — so on a retry the previous query and its
              failure reason are fed back, and the agent loosens its matching.
              In practice that turns an exact-name match which found nothing
              into a case-insensitive one that finds the record.
            </p>
            <p className="mt-3 max-w-[80ch] text-[13px] leading-relaxed text-phosphor-dim">
              Every generated query passes a read-only guard that rejects
              CREATE, MERGE, DELETE, SET, REMOVE, DROP and procedure calls, so
              a generated query can never modify the graph.
            </p>
          </div>
        </Panel>

        {/* ---------------- stack ---------------- */}
        <Panel label="STACK" className="mb-4">
          <div className="divide-y divide-rule/60">
            {STACK.map(([k, v, note]) => (
              <div key={k} className="flex flex-wrap gap-x-6 gap-y-1 px-5 py-3.5">
                <span className="telemetry w-24 shrink-0 text-phosphor-faint">{k}</span>
                <span className="w-56 shrink-0 text-[13px] text-phosphor">{v}</span>
                <span className="telemetry flex-1 text-phosphor-dim">{note}</span>
              </div>
            ))}
          </div>
        </Panel>

        {/* ---------------- provenance ---------------- */}
        <Panel label="DATA PROVENANCE" accent className="mb-4">
          <div className="p-5 text-[13px] leading-relaxed text-phosphor-dim">
            <span className="text-phosphor">493 real incidents</span> come from
            the Chicago Open Data Portal, plus 177 synthetic incidents for
            coverage.{" "}
            <span className="text-hazard">
              All persons, organizations, weapons, vehicles and evidence are
              fictional
            </span>{" "}
            — generated as an intelligence layer so the graph can be explored
            without exposing anyone&apos;s real record. Nothing here should be
            read as a claim about a real individual.
          </div>
        </Panel>

        <div className="telemetry flex flex-wrap items-center justify-between gap-2 border-t border-rule pt-3 text-phosphor-faint">
          <span>DAMG 7374 // KNOWLEDGE GRAPHS WITH GENAI // NORTHEASTERN UNIVERSITY</span>
          <a
            href="https://github.com/ManishKondoju/CrimeInvestigationGraph"
            className="transition-colors duration-150 hover:text-hazard"
          >
            SOURCE ON GITHUB →
          </a>
        </div>
      </div>
    </main>
  );
}
