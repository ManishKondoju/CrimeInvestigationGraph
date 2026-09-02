"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { ArrowLeft, DownloadSimple, CircleNotch } from "@phosphor-icons/react";
import { getSchema, getSchemaSample, schemaExportUrl } from "@/lib/api";
import type { SchemaData, SchemaExportFormat } from "@/lib/types";

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
const COLOR_MAP: Record<string, string> = {
  Person: "#F97316",
  Crime: "#3B82F6",
  Organization: "#EAB308",
  Location: "#10B981",
  Evidence: "#EC4899",
  Vehicle: "#06B6D4",
  Weapon: "#DC2626",
  Investigator: "#8B5CF6",
  ModusOperandi: "#F59E0B",
};
const FALLBACK_COLOR = "#64748b";

const EXPORT_FORMATS: { fmt: SchemaExportFormat; label: string }[] = [
  { fmt: "json", label: "JSON" },
  { fmt: "cypher", label: "Cypher" },
  { fmt: "markdown", label: "Markdown" },
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
            <line
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={isHovered ? "#e2e8f0" : "rgba(148,163,184,0.25)"}
              strokeWidth={isHovered ? 2 : 1}
              className="transition-all duration-300"
            />
            {isHovered && (
              <g>
                <rect
                  x={midX - 60}
                  y={midY - 12}
                  width={120}
                  height={20}
                  rx={10}
                  fill="rgba(9,9,11,0.95)"
                  stroke="rgba(255,255,255,0.15)"
                />
                <text x={midX} y={midY + 2} textAnchor="middle" className="fill-zinc-200 text-[9px] font-medium">
                  {rel.relationship_type} ({rel.count})
                </text>
              </g>
            )}
          </g>
        );
      })}

      {data.nodes.map((n) => {
        const pos = positions.get(n.node_type);
        if (!pos) return null;
        const color = COLOR_MAP[n.node_type] ?? FALLBACK_COLOR;
        return (
          <g key={n.node_type}>
            <circle cx={pos.x} cy={pos.y} r={pos.r} fill={color} fillOpacity={0.85} stroke="#050505" strokeWidth={3} />
            <text
              x={pos.x}
              y={pos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-zinc-950 text-[10px] font-bold"
            >
              {n.count}
            </text>
            <text
              x={pos.x}
              y={pos.y + pos.r + 16}
              textAnchor="middle"
              className="fill-zinc-300 text-[11px] font-medium"
            >
              {n.node_type}
            </text>
          </g>
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
    setSampleLoading(true);
    getSchemaSample(selectedLabel)
      .then((res) => setSamples(res.samples))
      .catch((e) => setError(e.message))
      .finally(() => setSampleLoading(false));
  }, [selectedLabel]);

  const totalNodes = data?.nodes.reduce((sum, n) => sum + n.count, 0) ?? 0;
  const totalRels = data?.relationships.reduce((sum, r) => sum + r.count, 0) ?? 0;

  return (
    <main className="relative flex min-h-[100dvh] flex-col overflow-hidden px-4 py-10 sm:px-8">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-1/4 top-0 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-violet-600/15 blur-[120px]" />
        <div className="absolute right-0 top-1/2 h-[28rem] w-[28rem] translate-x-1/3 rounded-full bg-emerald-500/10 blur-[120px]" />
      </div>

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col">
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-white/5 ring-1 ring-white/10 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-x-0.5"
          >
            <ArrowLeft weight="light" className="h-4 w-4 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-zinc-50">Graph Schema</h1>
            <p className="text-xs text-zinc-500">Live-queried Neo4j node and relationship structure</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-2xl bg-red-500/10 px-4 py-2.5 text-xs text-red-300 ring-1 ring-red-500/20">
            {error}
          </div>
        )}

        {!data ? (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <CircleNotch weight="bold" className="h-4 w-4 animate-spin" />
            Loading schema...
          </div>
        ) : (
          <>
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: "Entity Types", value: data.nodes.length },
                { label: "Relationship Types", value: data.relationships.length },
                { label: "Total Nodes", value: totalNodes.toLocaleString() },
                { label: "Total Relationships", value: totalRels.toLocaleString() },
              ].map((m) => (
                <DoubleBezel key={m.label}>
                  <div className="p-4">
                    <p className="text-[10px] uppercase tracking-[0.15em] text-zinc-500">{m.label}</p>
                    <p className="mt-1 text-2xl font-semibold text-zinc-50">{m.value}</p>
                  </div>
                </DoubleBezel>
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
              <DoubleBezel>
                <div className="p-6">
                  <SchemaDiagram data={data} />
                </div>
              </DoubleBezel>

              <div className="space-y-6">
                <DoubleBezel>
                  <div className="p-5">
                    <p className="mb-3 text-xs font-medium text-zinc-400">Property Drill-Down</p>
                    <select
                      value={selectedLabel ?? ""}
                      onChange={(e) => setSelectedLabel(e.target.value)}
                      className="mb-3 w-full rounded-xl bg-white/5 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 focus:outline-none"
                    >
                      {data.nodes.map((n) => (
                        <option key={n.node_type} value={n.node_type} className="bg-zinc-950">
                          {n.node_type}
                        </option>
                      ))}
                    </select>

                    <div className="mb-3 flex flex-wrap gap-1.5">
                      {(data.properties[selectedLabel ?? ""] ?? []).map((prop) => (
                        <span
                          key={prop}
                          className="rounded-full bg-white/5 px-2 py-0.5 font-mono text-[10px] text-zinc-400 ring-1 ring-white/10"
                        >
                          {prop}
                        </span>
                      ))}
                    </div>

                    {sampleLoading ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <CircleNotch weight="bold" className="h-3.5 w-3.5 animate-spin" />
                        Loading samples...
                      </div>
                    ) : (
                      <pre className="max-h-64 overflow-auto rounded-xl bg-black/40 p-3 font-mono text-[10px] leading-relaxed text-zinc-400 ring-1 ring-white/5">
                        {JSON.stringify(samples, null, 2)}
                      </pre>
                    )}
                  </div>
                </DoubleBezel>

                <DoubleBezel>
                  <div className="p-5">
                    <p className="mb-3 text-xs font-medium text-zinc-400">Export Schema</p>
                    <div className="flex flex-col gap-2">
                      {EXPORT_FORMATS.map(({ fmt, label }) => (
                        <a
                          key={fmt}
                          href={schemaExportUrl(fmt)}
                          download
                          className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2 text-xs font-medium text-zinc-300 ring-1 ring-white/10 transition-colors duration-500 hover:bg-white/10 hover:text-zinc-50"
                        >
                          {label}
                          <DownloadSimple weight="light" className="h-3.5 w-3.5" />
                        </a>
                      ))}
                    </div>
                  </div>
                </DoubleBezel>
              </div>
            </div>

            <DoubleBezel className="mt-6">
              <div className="overflow-x-auto p-5">
                <p className="mb-3 text-xs font-medium text-zinc-400">Relationship Types</p>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-zinc-500">
                      <th className="pb-2 font-medium">Source</th>
                      <th className="pb-2 font-medium">Relationship</th>
                      <th className="pb-2 font-medium">Target</th>
                      <th className="pb-2 text-right font-medium">Count</th>
                    </tr>
                  </thead>
                  <tbody className="text-zinc-300">
                    {data.relationships.map((r) => (
                      <tr key={`${r.source_type}-${r.relationship_type}-${r.target_type}`} className="border-t border-white/5">
                        <td className="py-1.5">{r.source_type}</td>
                        <td className="py-1.5 font-mono text-emerald-300/80">{r.relationship_type}</td>
                        <td className="py-1.5">{r.target_type}</td>
                        <td className="py-1.5 text-right">{r.count.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </DoubleBezel>
          </>
        )}
      </div>
    </main>
  );
}
