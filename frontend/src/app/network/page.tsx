"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import dynamic from "next/dynamic";

import { getEntityTypes, getEntities, getNetworkGraph } from "@/lib/api";
import type { EntityOption, NetworkEntityType, NetworkGraph } from "@/lib/types";
import {
  AnimatedNumber,
  LoadingBlocks,
  PageHeader,
  Panel,
} from "@/components/ui/motion";

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

// react-force-graph types its accessors against an index-signature object,
// so our narrower shape has to include one to be assignable.
interface NodeObj {
  [others: string]: unknown;
  id?: string | number;
  label?: string | null;
  type?: string;
  x?: number;
  y?: number;
}

interface LinkObj {
  [others: string]: unknown;
  label?: string;
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
    let cancelled = false;
    (async () => {
      setSelectedId(VIEW_ALL);
      try {
        const rows = await getEntities(selectedType);
        if (!cancelled) setEntities(rows);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedType]);

  // Reload the graph whenever type or specific entity changes. The
  // cancelled flag stops a slow earlier response from clobbering a newer
  // selection's data.
  useEffect(() => {
    if (!selectedType) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getNetworkGraph(selectedType, selectedId === VIEW_ALL ? null : selectedId);
        if (!cancelled) setGraph(data);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
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

  const getNodeColor = useCallback(
    (node: NodeObj) => colors[node.type ?? ""] ?? "#64748b",
    [colors],
  );

  const selectedName = entities.find((e) => String(e.id) === selectedId)?.name;

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto flex w-full max-w-[1400px] flex-1 flex-col">
        <PageHeader
          unit="D-02"
          title="Network"
          subtitle="FORCE-DIRECTED ASSOCIATION GRAPH // ENTITY LINK ANALYSIS"
          right={
            <span className="telemetry text-phosphor-faint">
              <AnimatedNumber value={graph?.nodes.length ?? 0} className="text-phosphor" /> NODES
              {" / "}
              <AnimatedNumber value={graph?.edges.length ?? 0} className="text-phosphor" /> EDGES
            </span>
          }
        />

        <div className="mb-3 grid gap-px border border-rule bg-rule md:grid-cols-2">
          <label className="flex items-center gap-3 bg-substrate-raised px-3 py-2">
            <span className="telemetry w-24 shrink-0 text-phosphor-faint">ENTITY TYPE</span>
            <select
              value={selectedType ?? ""}
              onChange={(e) => setSelectedType(e.target.value as NetworkEntityType)}
              className="w-full border border-rule bg-substrate px-2 py-1.5 text-[12px] text-phosphor focus:border-hazard focus:outline-none"
            >
              {entityTypes.map((t) => (
                <option key={t} value={t}>
                  {t.toUpperCase()}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-3 bg-substrate-raised px-3 py-2">
            <span className="telemetry w-24 shrink-0 text-phosphor-faint">SUBJECT</span>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full border border-rule bg-substrate px-2 py-1.5 text-[12px] text-phosphor focus:border-hazard focus:outline-none"
            >
              <option value={VIEW_ALL}>[ ALL ]</option>
              {entities.map((e) => (
                <option key={String(e.id)} value={String(e.id)}>
                  {String(e.name).slice(0, 50).toUpperCase()}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="telemetry mb-3 flex items-center justify-between text-phosphor-faint">
          <span>
            {">>>"} SCOPE /{" "}
            {selectedId === VIEW_ALL
              ? `ALL ${String(selectedType).toUpperCase()} ENTITIES`
              : String(selectedName ?? selectedId).toUpperCase()}
          </span>
          <span>DRAG // SCROLL TO ZOOM</span>
        </div>

        {error && (
          <div className="mb-3 border border-hazard bg-substrate-raised p-3">
            <div className="telemetry text-hazard">{"// FAULT"}</div>
            <div className="mt-1 text-[13px] text-phosphor-dim">{error}</div>
          </div>
        )}

        <Panel label="ASSOCIATION GRAPH" right={loading ? "SYNCING" : "RENDERED"} className="relative flex-1">
          <div ref={containerRef} className="relative h-[640px] w-full overflow-hidden">
            {loading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-substrate/70">
                <LoadingBlocks label="BUILDING GRAPH" />
              </div>
            )}

            {!loading && graph && graph.nodes.length === 0 && (
              <div className="telemetry flex h-full items-center justify-center text-phosphor-faint">
                NO RECORDS // {String(selectedType).toUpperCase()}
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
                  ctx.strokeStyle = "#0a0a0a";
                  ctx.stroke();

                  const raw = String(node.label ?? node.id ?? "");
                  const label = raw.length > 16 ? `${raw.slice(0, 16)}...` : raw;
                  const fontSize = 11 / globalScale;
                  ctx.font = `${fontSize}px "JetBrains Mono", ui-monospace, monospace`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "top";
                  ctx.fillStyle = "#eaeaea";
                  ctx.fillText(label.toUpperCase(), node.x ?? 0, (node.y ?? 0) + radius + 3);
                }}
                nodePointerAreaPaint={(node: NodeObj, color, ctx) => {
                  const radius = NODE_RADIUS[node.type ?? ""] ?? DEFAULT_RADIUS;
                  ctx.fillStyle = color;
                  ctx.beginPath();
                  ctx.arc(node.x ?? 0, node.y ?? 0, radius + 2, 0, 2 * Math.PI);
                  ctx.fill();
                }}
                linkLabel={(l: LinkObj) => l.label ?? ""}
                linkColor={() => "rgba(234, 234, 234, 0.22)"}
                linkDirectionalParticles={0}
                cooldownTicks={100}
              />
            )}
          </div>
        </Panel>

        {Object.keys(colors).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 border-t border-rule pt-3">
            {Object.entries(colors)
              .filter(([type]) => graph?.nodes.some((n) => n.type === type))
              .map(([type, color]) => (
                <span key={type} className="telemetry flex items-center gap-2 text-phosphor-dim">
                  <span className="h-2.5 w-2.5" style={{ backgroundColor: color }} />
                  {type}
                  <span className="text-phosphor-faint">
                    {graph?.nodes.filter((n) => n.type === type).length}
                  </span>
                </span>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}
