"use client";

import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import "maplibre-gl/dist/maplibre-gl.css";
import { Source, Layer, NavigationControl } from "react-map-gl/maplibre";
import {
  getCrimeTypes,
  getDistricts,
  getCrimeLocations,
  getHotspots,
  geoExportCsvUrl,
} from "@/lib/api";
import type { CrimeLocation, GeoFilters, HotspotPrediction } from "@/lib/types";
import {
  LoadingBlocks,
  PageHeader,
  Panel,
  Readout,
  RuledGrid,
  SegmentedControl,
} from "@/components/ui/motion";

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

// Severity ramps from phosphor grey (routine) to hazard red (critical) -
// red is reserved for genuine alert conditions, never used decoratively.
const SEVERITY_COLOR: Record<string, string> = {
  critical: "#e61919",
  high: "#ff6a3d",
  medium: "#eaeaea",
  low: "#6a6a6a",
};

const RISK_COLOR: Record<string, string> = {
  Critical: "#e61919",
  High: "#ff6a3d",
  Medium: "#eaeaea",
  Low: "#6a6a6a",
};

type Mode = "markers" | "heatmap" | "hotspots";

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

  // Filters change rapidly (sliders, checkbox lists), so in-flight requests
  // are guarded - without this a slow earlier response can overwrite the
  // results of a newer filter selection.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = mode === "hotspots" ? await getHotspots(filters) : await getCrimeLocations(filters);
        if (cancelled) return;
        if ("predictions" in res) setHotspots(res.predictions);
        else setLocations(res.rows);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [mode, filters]);

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
        { label: "HOTSPOT CLUSTERS", value: hotspots.length, max: 50 },
        { label: "HIGH / CRITICAL", value: highRisk, max: 50 },
        { label: "CRIMES CLUSTERED", value: clusteredCrimes, max: 700 },
        { label: "DISTRICTS", value: districts.length, max: 50 },
      ];
    }
    return [
      { label: "RECORDS SHOWN", value: locations.length, max: limit },
      { label: "CRITICAL SEVERITY", value: locations.filter((l) => l.severity === "critical").length, max: 100 },
      { label: "ARRESTS MADE", value: locations.filter((l) => l.arrest_made).length, max: 200 },
      { label: "DISTRICTS", value: districts.length, max: 50 },
    ];
  }, [mode, hotspots, locations, districts, limit]);

  const count = mode === "hotspots" ? hotspots.length : locations.length;

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto flex w-full max-w-[1400px] flex-1 flex-col">
        <PageHeader
          unit="D-03"
          title="Geospatial"
          subtitle="CHICAGO INCIDENT MAP // MAPLIBRE GL // NO API KEY REQUIRED"
          right={<span className="telemetry text-phosphor-faint">MODE / {mode.toUpperCase()}</span>}
        />

        <RuledGrid className="mb-4 grid-cols-2 sm:grid-cols-4">
          {statCards.map((m, i) => (
            <Readout key={m.label} label={m.label} value={m.value} max={m.max} index={i} />
          ))}
        </RuledGrid>

        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <Panel label="FILTER CONTROL" right={`LIM ${limit}`}>
            <div className="space-y-3 p-3">
              <SegmentedControl
                options={["markers", "heatmap", "hotspots"] as const}
                value={mode}
                onChange={setMode}
              />

              <div className="grid grid-cols-2 gap-2">
                <label className="block">
                  <span className="telemetry text-phosphor-faint">DATE FROM</span>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="mt-1 w-full border border-rule bg-substrate px-2 py-1.5 text-[11px] text-phosphor focus:border-hazard focus:outline-none"
                  />
                </label>
                <label className="block">
                  <span className="telemetry text-phosphor-faint">DATE TO</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="mt-1 w-full border border-rule bg-substrate px-2 py-1.5 text-[11px] text-phosphor focus:border-hazard focus:outline-none"
                  />
                </label>
              </div>

              <label className="block">
                <span className="telemetry flex justify-between text-phosphor-faint">
                  <span>MAX RECORDS</span>
                  <span className="text-hazard">{limit.toLocaleString()}</span>
                </span>
                <input
                  type="range"
                  min={500}
                  max={5000}
                  step={500}
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="mt-1.5 w-full"
                />
              </label>

              <div>
                <div className="telemetry flex justify-between text-phosphor-faint">
                  <span>CRIME TYPE</span>
                  <span className={selectedTypes.length ? "text-hazard" : ""}>
                    {selectedTypes.length || "ALL"}
                  </span>
                </div>
                <div className="mt-1 max-h-32 overflow-y-auto border border-rule bg-substrate">
                  {crimeTypes.map((t) => (
                    <label
                      key={t}
                      className="telemetry flex cursor-pointer items-center gap-2 px-2 py-1 text-phosphor-dim transition-colors duration-100 hover:bg-hazard hover:text-substrate"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(t)}
                        onChange={() => toggle(selectedTypes, setSelectedTypes, t)}
                        className="h-2.5 w-2.5"
                      />
                      {t}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <div className="telemetry flex justify-between text-phosphor-faint">
                  <span>DISTRICT</span>
                  <span className={selectedDistricts.length ? "text-hazard" : ""}>
                    {selectedDistricts.length || "ALL"}
                  </span>
                </div>
                <div className="mt-1 max-h-32 overflow-y-auto border border-rule bg-substrate">
                  {districts.map((d) => (
                    <label
                      key={d}
                      className="telemetry flex cursor-pointer items-center gap-2 px-2 py-1 text-phosphor-dim transition-colors duration-100 hover:bg-hazard hover:text-substrate"
                    >
                      <input
                        type="checkbox"
                        checked={selectedDistricts.includes(d)}
                        onChange={() => toggle(selectedDistricts, setSelectedDistricts, d)}
                        className="h-2.5 w-2.5"
                      />
                      DIST {d}
                    </label>
                  ))}
                </div>
              </div>

              <a
                href={geoExportCsvUrl(filters)}
                download
                className="telemetry flex items-center justify-between border border-hazard bg-hazard px-3 py-2 text-substrate transition-colors duration-150 hover:bg-transparent hover:text-hazard"
              >
                EXPORT CSV
                <span>{"[ DL ]"}</span>
              </a>
            </div>
          </Panel>

          <Panel
            label="INCIDENT MAP"
            right={loading ? "SYNCING" : `${count} PLOTTED`}
            className="relative"
          >
            <div className="relative h-[640px] w-full overflow-hidden">
              {loading && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-substrate/70">
                  <LoadingBlocks label="FETCHING INCIDENTS" />
                </div>
              )}

              {error && (
                <div className="absolute left-3 right-3 top-3 z-10 border border-hazard bg-substrate p-2.5">
                  <div className="telemetry text-hazard">{"// FAULT"}</div>
                  <div className="mt-1 text-[12px] text-phosphor-dim">{error}</div>
                </div>
              )}

              {!loading && count === 0 && (
                <div className="telemetry absolute inset-0 z-10 flex items-center justify-center text-phosphor-faint">
                  NO RECORDS MATCH CURRENT FILTERS
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
          </Panel>
        </div>
      </div>
    </main>
  );
}
