"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "motion/react";
import { getSchema, getSchemaSample, schemaExportUrl } from "@/lib/api";
import type { SchemaData, SchemaExportFormat } from "@/lib/types";
import {
  EASE,
  LoadingBlocks,
  PageHeader,
  Panel,
  Readout,
  RuledGrid,
  Shimmer,
} from "@/components/ui/motion";

// Graph Schema page - step 14 of the rebuild. Parity target:
// schema_visualizer.py's SchemaVisualizer - overview metrics, a circular
// schema diagram (node types as sized circles, relationships as lines),
// entity-types + relationship-types tables, a property drill-down with
// live sample nodes, and 3 export buttons (JSON/Cypher/Markdown). The
// original used Plotly for the circular diagram; this is small/fixed
// enough (<=9 node types) that a hand-rolled SVG is simpler than pulling
// in a force-graph library for it, per the approved plan.

// Same palette as network_viz.py's color_map, kept local here so this page
// doesn't depend on the network page's endpoint just for colors.
// Tactical palette: hazard red marks the operationally significant node
// types, everything else steps down through phosphor greys. Kept in sync
// with the network page's legend by intent, not by import.
const COLOR_MAP: Record<string, string> = {
  Person: "#e61919",
  Crime: "#e61919",
  Organization: "#eaeaea",
  Location: "#8a8a8a",
  Evidence: "#eaeaea",
  Vehicle: "#8a8a8a",
  Weapon: "#e61919",
  Investigator: "#eaeaea",
  ModusOperandi: "#8a8a8a",
};
const FALLBACK_COLOR = "#4a4a4a";

const EXPORT_FORMATS: { fmt: SchemaExportFormat; label: string }[] = [
  { fmt: "json", label: "JSON" },
  { fmt: "cypher", label: "Cypher" },
  { fmt: "markdown", label: "Markdown" },
];

const DIAGRAM_SIZE = 560;
const CENTER = DIAGRAM_SIZE / 2;
const ORBIT_RADIUS = 200;

function SchemaDiagram({ data }: { data: SchemaData }) {
  const [hovered, setHovered] = useState<string | null>(null);

  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number; r: number }>();
    const maxCount = Math.max(...data.nodes.map((n) => n.count), 1);
    data.nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / data.nodes.length - Math.PI / 2;
      const r = 16 + Math.sqrt(n.count / maxCount) * 34;
      map.set(n.node_type, {
        x: CENTER + ORBIT_RADIUS * Math.cos(angle),
        y: CENTER + ORBIT_RADIUS * Math.sin(angle),
        r,
      });
    });
    return map;
  }, [data.nodes]);

  return (
    <svg viewBox={`0 0 ${DIAGRAM_SIZE} ${DIAGRAM_SIZE}`} className="w-full">
      {data.relationships.map((rel, i) => {
        const from = positions.get(rel.source_type);
        const to = positions.get(rel.target_type);
        if (!from || !to) return null;
        const key = `${rel.source_type}-${rel.relationship_type}-${rel.target_type}`;
        const isHovered = hovered === key;
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        return (
          <g key={key} onMouseEnter={() => setHovered(key)} onMouseLeave={() => setHovered(null)}>
            {/* Lines draw themselves in, staggered, rather than appearing */}
            <motion.line
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={isHovered ? "#e61919" : "rgba(234,234,234,0.18)"}
              strokeWidth={isHovered ? 2 : 1}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 0.9, delay: 0.25 + i * 0.05, ease: EASE }}
              className="transition-colors duration-300"
            />
            {isHovered && (
              <g>
                <rect
                  x={midX - 60}
                  y={midY - 12}
                  width={120}
                  height={20}
                                    fill="#0a0a0a"
                  stroke="#e61919"
                />
                <text x={midX} y={midY + 2} textAnchor="middle" className="fill-phosphor text-[9px]">
                  {rel.relationship_type} ({rel.count})
                </text>
              </g>
            )}
          </g>
        );
      })}

      {data.nodes.map((n, i) => {
        const pos = positions.get(n.node_type);
        if (!pos) return null;
        const color = COLOR_MAP[n.node_type] ?? FALLBACK_COLOR;
        return (
          <motion.g
            key={n.node_type}
            initial={{ opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 220, damping: 18, delay: i * 0.07 }}
            style={{ transformOrigin: `${pos.x}px ${pos.y}px` }}
            whileHover={{ scale: 1.12 }}
          >
            {/* Soft pulsing halo keeps the diagram alive at rest. Scaled
                via transform rather than by animating the SVG `r`
                attribute - `r` is not a transform, so motion drove it to
                `undefined` between keyframes and the browser rejected it,
                and transforms stay on the GPU besides. */}
            <motion.circle
              cx={pos.x}
              cy={pos.y}
              r={pos.r}
              fill={color}
              fillOpacity={0.18}
              style={{ transformOrigin: `${pos.x}px ${pos.y}px` }}
              animate={{ scale: [1, 1.35, 1] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.25 }}
            />
            <circle cx={pos.x} cy={pos.y} r={pos.r} fill={color} fillOpacity={0.85} stroke="#0a0a0a" strokeWidth={3} />
            <text
              x={pos.x}
              y={pos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-substrate text-[10px] font-bold"
            >
              {n.count}
            </text>
            <text
              x={pos.x}
              y={pos.y + pos.r + 16}
              textAnchor="middle"
              className="fill-phosphor-dim text-[10px] uppercase tracking-widest"
            >
              {n.node_type}
            </text>
          </motion.g>
        );
      })}
    </svg>
  );
}

export default function SchemaPage() {
  const [data, setData] = useState<SchemaData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const [samples, setSamples] = useState<Record<string, unknown>[] | null>(null);
  const [sampleLoading, setSampleLoading] = useState(false);

  useEffect(() => {
    getSchema()
      .then((res) => {
        setData(res);
        setSelectedLabel(res.nodes[0]?.node_type ?? null);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selectedLabel) return;
    let cancelled = false;
    (async () => {
      setSampleLoading(true);
      try {
        const res = await getSchemaSample(selectedLabel);
        if (!cancelled) setSamples(res.samples);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setSampleLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedLabel]);

  const totalNodes = data?.nodes.reduce((sum, n) => sum + n.count, 0) ?? 0;
  const totalRels = data?.relationships.reduce((sum, r) => sum + r.count, 0) ?? 0;

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto flex w-full max-w-[1400px] flex-1 flex-col">
        <PageHeader
          unit="D-04"
          title="Schema"
          subtitle="LIVE-QUERIED NEO4J STRUCTURE // NODE + RELATIONSHIP TOPOLOGY"
        />

        {error && (
          <div className="mb-3 border border-hazard bg-substrate-raised p-3">
            <div className="telemetry text-hazard">{"// FAULT"}</div>
            <div className="mt-1 text-[13px] text-phosphor-dim">{error}</div>
          </div>
        )}

        {!data ? (
          <div className="grid grid-cols-2 gap-px border border-rule bg-rule sm:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Shimmer key={i} className="h-[104px] border-0" />
            ))}
          </div>
        ) : (
          <>
            <RuledGrid className="mb-4 grid-cols-2 sm:grid-cols-4">
              <Readout label="ENTITY TYPES" value={data.nodes.length} max={12} index={0} />
              <Readout label="REL TYPES" value={data.relationships.length} max={20} index={1} />
              <Readout label="TOTAL NODES" value={totalNodes} max={2500} index={2} />
              <Readout label="TOTAL RELS" value={totalRels} max={3500} index={3} />
            </RuledGrid>

            <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
              <Panel label="TOPOLOGY MAP" right={`${data.nodes.length} TYPES`}>
                <div className="p-4">
                  <SchemaDiagram data={data} />
                </div>
              </Panel>

              <div className="space-y-4">
                <Panel label="PROPERTY DRILL-DOWN" right={selectedLabel?.toUpperCase()}>
                  <div className="p-3">
                    <select
                      value={selectedLabel ?? ""}
                      onChange={(e) => setSelectedLabel(e.target.value)}
                      className="mb-3 w-full border border-rule bg-substrate px-2 py-1.5 text-[12px] text-phosphor focus:border-hazard focus:outline-none"
                    >
                      {data.nodes.map((n) => (
                        <option key={n.node_type} value={n.node_type}>
                          {n.node_type.toUpperCase()}
                        </option>
                      ))}
                    </select>

                    <div className="mb-3 flex flex-wrap gap-px bg-rule">
                      {(data.properties[selectedLabel ?? ""] ?? []).map((prop) => (
                        <span
                          key={prop}
                          className="telemetry bg-substrate px-2 py-1 text-phosphor-dim"
                        >
                          {prop}
                        </span>
                      ))}
                    </div>

                    {sampleLoading ? (
                      <LoadingBlocks label="FETCHING SAMPLES" />
                    ) : (
                      <pre className="max-h-64 overflow-auto border border-rule bg-substrate p-2.5 text-[10px] leading-relaxed text-phosphor-dim">
                        {JSON.stringify(samples, null, 2)}
                      </pre>
                    )}
                  </div>
                </Panel>

                <Panel label="EXPORT SCHEMA">
                  <div className="grid gap-px bg-rule">
                    {EXPORT_FORMATS.map(({ fmt, label }) => (
                      <a
                        key={fmt}
                        href={schemaExportUrl(fmt)}
                        download
                        className="telemetry group flex items-center justify-between bg-substrate-raised px-3 py-2.5 text-phosphor-dim transition-colors duration-150 hover:bg-hazard hover:text-substrate"
                      >
                        {label}
                        <span className="transition-transform duration-150 group-hover:translate-y-0.5">
                          {"[ DL ]"}
                        </span>
                      </a>
                    ))}
                  </div>
                </Panel>
              </div>
            </div>

            <Panel label="RELATIONSHIP MANIFEST" right={`${data.relationships.length} TYPES`} className="mt-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="telemetry border-b border-rule text-phosphor-faint">
                      <th className="px-3 py-2 font-normal">SOURCE</th>
                      <th className="px-3 py-2 font-normal">RELATIONSHIP</th>
                      <th className="px-3 py-2 font-normal">TARGET</th>
                      <th className="px-3 py-2 text-right font-normal">COUNT</th>
                    </tr>
                  </thead>
                  <tbody className="text-[12px]">
                    {data.relationships.map((r, i) => (
                      <motion.tr
                        key={`${r.source_type}-${r.relationship_type}-${r.target_type}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2, delay: i * 0.025 }}
                        className="border-b border-rule/60 text-phosphor-dim transition-colors duration-150 hover:bg-hazard hover:text-substrate"
                      >
                        <td className="px-3 py-1.5">{r.source_type}</td>
                        <td className="px-3 py-1.5 text-phosphor">{r.relationship_type}</td>
                        <td className="px-3 py-1.5">{r.target_type}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums">
                          {r.count.toLocaleString()}
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          </>
        )}
      </div>
    </main>
  );
}
