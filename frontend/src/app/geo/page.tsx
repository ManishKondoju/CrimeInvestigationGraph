"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import "maplibre-gl/dist/maplibre-gl.css";
import { Source, Layer, NavigationControl } from "react-map-gl/maplibre";
import { ArrowLeft, CircleNotch, DownloadSimple, MapTrifold } from "@phosphor-icons/react";
import {
  getCrimeTypes,
  getDistricts,
  getCrimeLocations,
  getHotspots,
  geoExportCsvUrl,
} from "@/lib/api";
import type { CrimeLocation, GeoFilters, HotspotPrediction } from "@/lib/types";

// Geographic Mapping page - step 17 of the rebuild. Parity target:
// geo_mapping.py's CrimeGeographicMapper - filter sidebar (crime types,
// districts, date range, max records), 3 display modes (markers/heatmap/
// hotspots), stat cards, CSV export.
//
// THE MAP-TOKEN FIX: the original used Plotly's go.Densitymapbox/
// Scattermapbox with no Mapbox token configured anywhere in the repo,
// producing an "API KEY REQUIRED" watermark. This page uses MapLibre GL
// (free, open, no token) with CARTO's free "dark matter" GL vector style
// instead - same look, zero API key needed.
//
// NOTE: CARTO's plain raster tile CDN (basemaps.cartocdn.com/dark_matter/
// {z}/{x}/{y}.png) does NOT work here - it serves no CORS headers, which is
// fine for Leaflet's <img> tags but fails in MapLibre, which loads tiles
// into WebGL textures and therefore requires CORS. The /gl/ vector style
// below does send `access-control-allow-origin: *`.

// Only the top-level Map component touches window/WebGL at mount time, so
// only it needs a client-only dynamic import - Source/Layer/NavigationControl
// are plain context-consuming wrappers and must come from the SAME module
// instance as Map (dynamically importing them separately broke the React
// context they use to find their parent map).
const Map = dynamic(() => import("react-map-gl/maplibre").then((m) => m.default), { ssr: false });

// CARTO's dedicated MapLibre/Mapbox-GL vector style - free, no API key,
// and (unlike their plain raster tile CDN) served with
// `access-control-allow-origin: *`, which MapLibre GL needs since it loads
// tiles into WebGL textures rather than plain <img> tags. This is the
// actual fix for the original app's "API KEY REQUIRED" Mapbox watermark.
const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

const RISK_COLOR: Record<string, string> = {
  Critical: "#dc2626",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#22c55e",
};

type Mode = "markers" | "heatmap" | "hotspots";

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

function locationsToGeoJson(rows: CrimeLocation[]) {
  return {
    type: "FeatureCollection" as const,
    features: rows.map((r) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [r.longitude, r.latitude] },
      properties: r,
    })),
  };
}

function hotspotsToGeoJson(rows: HotspotPrediction[]) {
  return {
    type: "FeatureCollection" as const,
    features: rows.map((r) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [r.longitude, r.latitude] },
      properties: r,
    })),
  };
}

export default function GeoPage() {
  const [mode, setMode] = useState<Mode>("markers");
  const [crimeTypes, setCrimeTypes] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedDistricts, setSelectedDistricts] = useState<string[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [limit, setLimit] = useState(2000);

  const [locations, setLocations] = useState<CrimeLocation[]>([]);
  const [hotspots, setHotspots] = useState<HotspotPrediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCrimeTypes().then((r) => setCrimeTypes(r.types)).catch((e) => setError(e.message));
    getDistricts().then((r) => setDistricts(r.districts)).catch((e) => setError(e.message));
  }, []);

  const filters: GeoFilters = useMemo(
    () => ({
      crime_types: selectedTypes.length ? selectedTypes : undefined,
      districts: selectedDistricts.length ? selectedDistricts : undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      limit,
    }),
    [selectedTypes, selectedDistricts, startDate, endDate, limit],
  );

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const request = mode === "hotspots" ? getHotspots(filters) : getCrimeLocations(filters);
    request
      .then((res) => {
        if ("predictions" in res) setHotspots(res.predictions);
        else setLocations(res.rows);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, filters]);

  useEffect(() => {
    load();
  }, [load]);

  const geojson = useMemo(
    () => (mode === "hotspots" ? hotspotsToGeoJson(hotspots) : locationsToGeoJson(locations)),
    [mode, hotspots, locations],
  );

  const toggle = (list: string[], setList: (v: string[]) => void, value: string) => {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  };

  // Hotspots mode returns DBSCAN clusters, not individual crimes, so the
  // stat cards have to describe a different thing entirely - showing
  // "Records Shown: 28" (clusters) next to a stale crime-level severity
  // count would be actively misleading.
  const statCards = useMemo(() => {
    if (mode === "hotspots") {
      const highRisk = hotspots.filter((h) => h.risk_level === "Critical" || h.risk_level === "High").length;
      const clusteredCrimes = hotspots.reduce((sum, h) => sum + h.crime_count, 0);
      return [
        { label: "Hotspot Clusters", value: hotspots.length.toLocaleString() },
        { label: "High / Critical Risk", value: highRisk.toLocaleString() },
        { label: "Crimes Clustered", value: clusteredCrimes.toLocaleString() },
        { label: "Districts", value: String(districts.length) },
      ];
    }
    return [
      { label: "Records Shown", value: locations.length.toLocaleString() },
      { label: "Critical Severity", value: locations.filter((l) => l.severity === "critical").length.toLocaleString() },
      { label: "Arrests Made", value: locations.filter((l) => l.arrest_made).length.toLocaleString() },
      { label: "Districts", value: String(districts.length) },
    ];
  }, [mode, hotspots, locations, districts]);

  const count = mode === "hotspots" ? hotspots.length : locations.length;

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
            <h1 className="text-lg font-semibold tracking-tight text-zinc-50">Geographic Mapping</h1>
            <p className="text-xs text-zinc-500">Chicago crime map - MapLibre GL, no API key required</p>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {statCards.map((m) => (
            <DoubleBezel key={m.label}>
              <div className="p-4">
                <p className="text-[10px] uppercase tracking-[0.15em] text-zinc-500">{m.label}</p>
                <p className="mt-1 text-2xl font-semibold text-zinc-50">{m.value}</p>
              </div>
            </DoubleBezel>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <div className="space-y-4">
            <DoubleBezel>
              <div className="space-y-4 p-4">
                <div className="flex gap-1.5 rounded-full bg-white/5 p-1">
                  {(["markers", "heatmap", "hotspots"] as Mode[]).map((m) => (
                    <button
                      key={m}
                      onClick={() => setMode(m)}
                      className={`flex-1 rounded-full px-3 py-1.5 text-xs font-medium capitalize transition-colors duration-300 ${
                        mode === m ? "bg-zinc-50 text-zinc-950" : "text-zinc-400 hover:text-zinc-200"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">Start Date</p>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full rounded-xl bg-white/5 px-3 py-1.5 text-xs text-zinc-100 ring-1 ring-white/10 focus:outline-none"
                  />
                </div>
                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">End Date</p>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full rounded-xl bg-white/5 px-3 py-1.5 text-xs text-zinc-100 ring-1 ring-white/10 focus:outline-none"
                  />
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">
                    Max Records: {limit.toLocaleString()}
                  </p>
                  <input
                    type="range"
                    min={500}
                    max={5000}
                    step={500}
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="w-full accent-zinc-50"
                  />
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">
                    Crime Types {selectedTypes.length ? `(${selectedTypes.length})` : ""}
                  </p>
                  <div className="max-h-32 space-y-1 overflow-y-auto rounded-xl bg-black/20 p-2">
                    {crimeTypes.map((t) => (
                      <label key={t} className="flex items-center gap-2 text-[11px] text-zinc-400">
                        <input
                          type="checkbox"
                          checked={selectedTypes.includes(t)}
                          onChange={() => toggle(selectedTypes, setSelectedTypes, t)}
                          className="accent-zinc-50"
                        />
                        {t}
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-medium text-zinc-500">
                    Districts {selectedDistricts.length ? `(${selectedDistricts.length})` : ""}
                  </p>
                  <div className="max-h-32 space-y-1 overflow-y-auto rounded-xl bg-black/20 p-2">
                    {districts.map((d) => (
                      <label key={d} className="flex items-center gap-2 text-[11px] text-zinc-400">
                        <input
                          type="checkbox"
                          checked={selectedDistricts.includes(d)}
                          onChange={() => toggle(selectedDistricts, setSelectedDistricts, d)}
                          className="accent-zinc-50"
                        />
                        District {d}
                      </label>
                    ))}
                  </div>
                </div>

                <a
                  href={geoExportCsvUrl(filters)}
                  download
                  className="flex items-center justify-center gap-2 rounded-xl bg-white/5 px-3 py-2 text-xs font-medium text-zinc-300 ring-1 ring-white/10 transition-colors duration-500 hover:bg-white/10 hover:text-zinc-50"
                >
                  <DownloadSimple weight="light" className="h-3.5 w-3.5" />
                  Export CSV
                </a>
              </div>
            </DoubleBezel>
          </div>

          <DoubleBezel className="relative">
            <div className="relative h-[640px] w-full overflow-hidden rounded-[calc(1.5rem-0.375rem)]">
              {loading && (
                <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-zinc-950/60 text-xs text-zinc-400 backdrop-blur-sm">
                  <CircleNotch weight="bold" className="h-4 w-4 animate-spin" />
                  Loading crime data...
                </div>
              )}

              {error && (
                <div className="absolute left-4 right-4 top-4 z-10 rounded-2xl bg-red-500/10 px-4 py-2.5 text-xs text-red-300 ring-1 ring-red-500/20">
                  {error}
                </div>
              )}

              {!loading && count === 0 && (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-zinc-600">
                  <MapTrifold weight="light" className="h-8 w-8" />
                  <p className="text-sm">No records match the current filters</p>
                </div>
              )}

              <Map
                initialViewState={{ longitude: -87.65, latitude: 41.85, zoom: 10 }}
                mapStyle={MAP_STYLE}
                style={{ width: "100%", height: "100%" }}
              >
                <NavigationControl position="top-right" />

                {mode === "markers" && (
                  <Source id="crimes" type="geojson" data={geojson}>
                    <Layer
                      id="crime-points"
                      type="circle"
                      paint={{
                        "circle-radius": 5,
                        "circle-color": [
                          "match",
                          ["get", "severity"],
                          "critical",
                          SEVERITY_COLOR.critical,
                          "high",
                          SEVERITY_COLOR.high,
                          "medium",
                          SEVERITY_COLOR.medium,
                          "low",
                          SEVERITY_COLOR.low,
                          "#94a3b8",
                        ],
                        "circle-opacity": 0.75,
                        "circle-stroke-width": 1,
                        "circle-stroke-color": "#050505",
                      }}
                    />
                  </Source>
                )}

                {mode === "heatmap" && (
                  <Source id="crimes-heat" type="geojson" data={geojson}>
                    <Layer
                      id="crime-heatmap"
                      type="heatmap"
                      paint={{
                        "heatmap-weight": 1,
                        "heatmap-intensity": 1,
                        "heatmap-radius": 20,
                        "heatmap-opacity": 0.8,
                        "heatmap-color": [
                          "interpolate",
                          ["linear"],
                          ["heatmap-density"],
                          0,
                          "rgba(0,0,0,0)",
                          0.2,
                          "#22c55e",
                          0.4,
                          "#eab308",
                          0.6,
                          "#f97316",
                          1,
                          "#dc2626",
                        ],
                      }}
                    />
                  </Source>
                )}

                {mode === "hotspots" && (
                  <Source id="hotspots" type="geojson" data={geojson}>
                    <Layer
                      id="hotspot-points"
                      type="circle"
                      paint={{
                        "circle-radius": ["interpolate", ["linear"], ["get", "crime_count"], 1, 6, 20, 24],
                        "circle-color": [
                          "match",
                          ["get", "risk_level"],
                          "Critical",
                          RISK_COLOR.Critical,
                          "High",
                          RISK_COLOR.High,
                          "Medium",
                          RISK_COLOR.Medium,
                          "Low",
                          RISK_COLOR.Low,
                          "#94a3b8",
                        ],
                        "circle-opacity": 0.55,
                        "circle-stroke-width": 1.5,
                        "circle-stroke-color": "#050505",
                      }}
                    />
                  </Source>
                )}
              </Map>
            </div>
          </DoubleBezel>
        </div>
      </div>
    </main>
  );
}
