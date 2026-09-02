"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowLeft, CircleNotch, ShareNetwork } from "@phosphor-icons/react";
import { getEntityTypes, getEntities, getNetworkGraph } from "@/lib/api";
import type { EntityOption, NetworkEntityType, NetworkGraph } from "@/lib/types";

// Network Visualization page - step 13 of the rebuild. Parity target:
// network_viz.py's NetworkVisualization.render() - entity-type dropdown,
// specific-entity dropdown (with a "View All" option), node/edge stats,
// force-directed graph. Backend already returns a clean {nodes, edges}
// shape (backend/app/routers/network.py), so this is a near-drop-in for
// react-force-graph-2d instead of the old D3-in-an-iframe approach.

// Canvas-based, touches window/DOM directly - must be client-only, no SSR.
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const VIEW_ALL = "__view_all__";

// Matches network_viz.py's per-type circle sizing (line 536 of the old
// D3 renderer) so node prominence carries over to the new canvas render.
const NODE_RADIUS: Record<string, number> = {
  Organization: 12,
  Location: 8,
  Investigator: 7,
  Evidence: 6,
  Crime: 6,
};
const DEFAULT_RADIUS = 5;

interface NodeObj {
  id?: string | number;
  label?: string | null;
  type?: string;
  x?: number;
  y?: number;
}

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

export default function NetworkPage() {
  const [entityTypes, setEntityTypes] = useState<NetworkEntityType[]>([]);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [selectedType, setSelectedType] = useState<NetworkEntityType | null>(null);
  const [entities, setEntities] = useState<EntityOption[]>([]);
  const [selectedId, setSelectedId] = useState<string>(VIEW_ALL);
  const [graph, setGraph] = useState<NetworkGraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 600 });

  // Load the 8 entity types + color legend once.
  useEffect(() => {
    getEntityTypes()
      .then((res) => {
        setEntityTypes(res.types);
        setColors(res.colors);
        setSelectedType(res.types[0]);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Reload the specific-entity dropdown whenever the type changes.
  useEffect(() => {
    if (!selectedType) return;
    setSelectedId(VIEW_ALL);
    getEntities(selectedType)
      .then(setEntities)
      .catch((e) => setError(e.message));
  }, [selectedType]);

  // Reload the graph whenever type or specific entity changes.
  useEffect(() => {
    if (!selectedType) return;
    setLoading(true);
    setError(null);
    getNetworkGraph(selectedType, selectedId === VIEW_ALL ? null : selectedId)
      .then(setGraph)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedType, selectedId]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      setDimensions({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(
    () => ({
      nodes: graph?.nodes ?? [],
      links: (graph?.edges ?? []).map((e) => ({ ...e })),
    }),
    [graph],
  );

  const getNodeColor = useCallback((node: { type?: string }) => colors[node.type ?? ""] ?? "#64748b", [colors]);

  const selectedName = entities.find((e) => String(e.id) === selectedId)?.name;

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
            <h1 className="text-lg font-semibold tracking-tight text-zinc-50">
              Network Visualization
            </h1>
            <p className="text-xs text-zinc-500">
              Force-directed graph of criminal network connections
            </p>
          </div>
        </div>

        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-zinc-500">Entity Type</label>
            <select
              value={selectedType ?? ""}
              onChange={(e) => setSelectedType(e.target.value as NetworkEntityType)}
              className="rounded-xl bg-white/5 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 focus:outline-none"
            >
              {entityTypes.map((t) => (
                <option key={t} value={t} className="bg-zinc-950">
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-zinc-500">Specific {selectedType}</label>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="min-w-48 rounded-xl bg-white/5 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 focus:outline-none"
            >
              <option value={VIEW_ALL} className="bg-zinc-950">
                - View All -
              </option>
              {entities.map((e) => (
                <option key={String(e.id)} value={String(e.id)} className="bg-zinc-950">
                  {String(e.name).slice(0, 50)}
                </option>
              ))}
            </select>
          </div>

          <div className="ml-auto flex gap-3 text-xs text-zinc-500">
            <span className="rounded-full bg-white/5 px-3 py-1.5 ring-1 ring-white/10">
              {graph?.nodes.length ?? 0} nodes
            </span>
            <span className="rounded-full bg-white/5 px-3 py-1.5 ring-1 ring-white/10">
              {graph?.edges.length ?? 0} edges
            </span>
          </div>
        </div>

        <p className="mb-4 text-xs text-zinc-500">
          {selectedId === VIEW_ALL
            ? `Showing: All ${selectedType}s and their connections`
            : `Showing: ${selectedName ?? selectedId} and connected entities`}
        </p>

        {error && (
          <div className="mb-4 rounded-2xl bg-red-500/10 px-4 py-2.5 text-xs text-red-300 ring-1 ring-red-500/20">
            {error}
          </div>
        )}

        <DoubleBezel className="relative flex-1">
          <div ref={containerRef} className="relative h-[640px] w-full overflow-hidden rounded-[calc(1.5rem-0.375rem)]">
            {loading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-zinc-950/60 text-xs text-zinc-400 backdrop-blur-sm">
                <CircleNotch weight="bold" className="h-4 w-4 animate-spin" />
                Loading network...
              </div>
            )}

            {!loading && graph && graph.nodes.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-zinc-600">
                <ShareNetwork weight="light" className="h-8 w-8" />
                <p className="text-sm">No data loaded for {selectedType}</p>
              </div>
            )}

            {graph && graph.nodes.length > 0 && (
              <ForceGraph2D
                graphData={graphData}
                width={dimensions.width}
                height={dimensions.height}
                backgroundColor="rgba(0,0,0,0)"
                nodeColor={getNodeColor}
                nodeRelSize={5}
                nodeCanvasObject={(node: NodeObj, ctx, globalScale) => {
                  const radius = NODE_RADIUS[node.type ?? ""] ?? DEFAULT_RADIUS;
                  ctx.beginPath();
                  ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI);
                  ctx.fillStyle = getNodeColor(node);
                  ctx.fill();
                  ctx.lineWidth = 1.5 / globalScale;
                  ctx.strokeStyle = "#050505";
                  ctx.stroke();

                  const raw = String(node.label ?? node.id ?? "");
                  const label = raw.length > 16 ? `${raw.slice(0, 16)}...` : raw;
                  const fontSize = 11 / globalScale;
                  ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "top";
                  ctx.fillStyle = "#e2e8f0";
                  ctx.fillText(label, node.x ?? 0, (node.y ?? 0) + radius + 3);
                }}
                nodePointerAreaPaint={(node: NodeObj, color, ctx) => {
                  const radius = NODE_RADIUS[node.type ?? ""] ?? DEFAULT_RADIUS;
                  ctx.fillStyle = color;
                  ctx.beginPath();
                  ctx.arc(node.x ?? 0, node.y ?? 0, radius + 2, 0, 2 * Math.PI);
                  ctx.fill();
                }}
                linkLabel={(l: { label?: string }) => l.label ?? ""}
                linkColor={() => "rgba(148, 163, 184, 0.35)"}
                linkDirectionalParticles={0}
                cooldownTicks={100}
              />
            )}
          </div>
        </DoubleBezel>

        {Object.keys(colors).length > 0 && (
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(colors)
              .filter(([type]) => graph?.nodes.some((n) => n.type === type))
              .map(([type, color]) => (
                <div key={type} className="flex items-center gap-1.5 text-xs text-zinc-400">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {type}
                </div>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}
