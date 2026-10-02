"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { EASE, PageHeader, Panel, Reveal, RuledGrid } from "@/components/ui/motion";

// About. The Streamlit original had one; this replaces it and gives the
// launch film somewhere to live inside the product rather than only in the
// repo README.

const PIPELINE = ["EXTRACT", "GENERATE", "EXECUTE", "VALIDATE", "ANSWER"];

// Versions are the ones actually pinned in backend/requirements.txt and
// frontend/package.json - a stack list that drifts from the lockfile is
// worse than none.
const STACK: [string, [string, string, string][]][] = [
  ["DATA", [
    ["Neo4j Aura", "5.18", "Managed graph database — 1,868 nodes, 2,738 relationships, 9 entity types"],
    ["Chicago Open Data", "—", "493 real incidents, geocoded, pulled from the city portal"],
  ]],
  ["AGENT", [
    ["LangGraph", "0.2.60", "The state machine: extract → generate → execute → validate → answer"],
    ["langchain-core", "0.3.29", "Message plumbing and the Neo4j query tool wrapper"],
    ["langchain-groq", "0.2.3", "Model client"],
    ["Groq", "gpt-oss-120b", "Inference for entity extraction, Cypher generation and answer synthesis"],
  ]],
  ["API", [
    ["FastAPI", "0.115.6", "20 read-only endpoints; every filter passed as a Cypher $parameter"],
    ["Uvicorn", "0.34.0", "ASGI server"],
    ["Pydantic", "2.x", "Request and response schemas"],
    ["pandas · NumPy", "2.2 · 1.26", "Aggregation for the dashboard and timeline endpoints"],
    ["scikit-learn", "1.4.1", "DBSCAN clustering behind the geospatial hotspots"],
  ]],
  ["CLIENT", [
    ["Next.js", "16.3.4", "App Router; server-side proxy keeps the API key off the browser"],
    ["React", "19.2.8", "—"],
    ["TypeScript", "5.x", "Strict; types mirror the Pydantic models"],
    ["Tailwind CSS", "4.x", "No component library — the design system is hand-built"],
    ["Motion", "13.1.1", "Entry animation and layout transitions"],
    ["react-force-graph-2d", "1.29.1", "Canvas force layout for the network module"],
    ["MapLibre GL", "5.24", "Vector maps, no API key — replaced a token-gated Mapbox setup"],
  ]],
  ["INFRASTRUCTURE", [
    ["Vercel", "—", "Frontend and the proxy route"],
    ["Render", "—", "FastAPI service"],
    ["GitHub Actions", "—", "Daily keep-alive so the free-tier database never idles out"],
  ]],
  ["VERIFICATION", [
    ["pytest", "8.3.4", "36 tests across the API surface and the agent's decision logic"],
    ["eval_agent.py", "—", "10 questions checked against ground-truth Cypher — currently 10/10"],
  ]],
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
        <Panel label="TECH STACK" right="PINNED VERSIONS" className="mb-4">
          <div className="divide-y divide-rule">
            {STACK.map(([group, rows]) => (
              <div key={group} className="grid gap-x-6 px-5 py-4 lg:grid-cols-[150px_1fr]">
                <div className="telemetry mb-2 text-hazard lg:mb-0">{group}</div>
                <div className="divide-y divide-rule/40">
                  {rows.map(([name, ver, note]) => (
                    <div
                      key={name}
                      className="flex flex-wrap items-baseline gap-x-4 gap-y-0.5 py-2 first:pt-0 last:pb-0"
                    >
                      <span className="w-52 shrink-0 text-[13px] text-phosphor">{name}</span>
                      <span className="telemetry w-28 shrink-0 tabular-nums text-phosphor-faint">
                        {ver}
                      </span>
                      {note !== "—" && (
                        <span className="telemetry flex-1 text-phosphor-dim">{note}</span>
                      )}
                    </div>
                  ))}
                </div>
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
