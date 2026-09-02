"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  getKpis,
  getTrends,
  getGangs,
  getBreakdowns,
  getOperations,
  getActivity,
} from "@/lib/api";
import type {
  DashboardActivity,
  DashboardBreakdowns,
  DashboardKpis,
  DashboardOperations,
  DashboardTrends,
  GangIntel,
} from "@/lib/types";
import {
  AnimatedNumber,
  LoadingBlocks,
  PageHeader,
  Panel,
  Readout,
  RuledGrid,
  Shimmer,
} from "@/components/ui/motion";

// Executive dashboard. Parity target: enhanced_dashboard.py, consumed via
// the 6 aggregate endpoints instead of its ~30 inline queries.
//
// Charts are hand-rolled SVG/CSS rather than a charting library: every
// mainstream lib defaults to rounded bars, smooth curves and soft grids,
// which would fight the hard-edged system. Blocks and rules are cheaper
// here than fighting a library's defaults.
//
// NOTE: the original page's time-period / district / severity filters were
// decorative (no query consumed them). Per the agreed plan this port keeps
// exact current behaviour, so those controls are simply not reproduced
// rather than shipped as fake controls.

const SEVERITY_RANK = ["critical", "high", "severe", "medium", "low"];

// Person names are NOT unique in this dataset (duplicates exist across
// different node ids), and these endpoints return names without ids - so
// any list keyed on a person name needs a composite key.

/** Horizontal block bar: label, discrete track, value. The core data mark. */
function BarRow({
  label,
  value,
  max,
  sub,
  alert = false,
  index = 0,
}: {
  label: string;
  value: number;
  max: number;
  sub?: string;
  alert?: boolean;
  index?: number;
}) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  return (
    <div className="flex items-center gap-3 px-3 py-1.5">
      <span className="telemetry w-32 shrink-0 truncate text-phosphor-dim" title={label}>
        {label}
      </span>
      <span className="relative h-3 flex-1 bg-phosphor-faint/15">
        <motion.span
          initial={{ scaleX: 0 }}
          animate={{ scaleX: pct }}
          transition={{ duration: 0.6, delay: index * 0.04, ease: [0.2, 0.8, 0.2, 1] }}
          className={`absolute inset-y-0 left-0 w-full origin-left ${
            alert ? "bg-hazard" : "bg-phosphor"
          }`}
        />
      </span>
      {sub && <span className="telemetry w-14 shrink-0 text-right text-phosphor-faint">{sub}</span>}
      <span className="telemetry w-12 shrink-0 text-right tabular-nums text-phosphor">
        {value.toLocaleString()}
      </span>
    </div>
  );
}

/** Vertical column chart for the monthly trend series. */
function TrendColumns({ data }: { data: DashboardTrends["monthly_trends"] }) {
  const max = Math.max(...data.map((d) => d.total_crimes), 1);
  return (
    <div className="p-3">
      <div className="flex h-40 items-end gap-px">
        {data.map((d, i) => {
          const totalH = (d.total_crimes / max) * 100;
          const severeH = (d.severe_crimes / max) * 100;
          return (
            // h-full is required: the bar heights are percentages, which
            // only resolve against a parent with a definite height. Under
            // `items-end` these wrappers would otherwise be auto-height and
            // every column would collapse to zero.
            <div key={d.year_month} className="group relative flex h-full flex-1 flex-col justify-end">
              <motion.div
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ duration: 0.5, delay: i * 0.04, ease: [0.2, 0.8, 0.2, 1] }}
                style={{ height: `${totalH}%` }}
                className="relative w-full origin-bottom bg-phosphor-faint/40"
              >
                {/* Severe portion overlays the base column in hazard red */}
                <span
                  className="absolute bottom-0 left-0 w-full bg-hazard"
                  style={{ height: `${(severeH / totalH) * 100 || 0}%` }}
                />
              </motion.div>
              <div className="telemetry pointer-events-none absolute -top-6 left-1/2 z-10 hidden -translate-x-1/2 whitespace-nowrap border border-hazard bg-substrate px-1.5 py-0.5 text-phosphor group-hover:block">
                {d.year_month} / {d.total_crimes}
              </div>
            </div>
          );
        })}
      </div>
      <div className="telemetry mt-2 flex justify-between text-phosphor-faint">
        <span>{data[0]?.year_month}</span>
        <span className="text-hazard">■ SEVERE</span>
        <span>{data[data.length - 1]?.year_month}</span>
      </div>
      {/* Scale is linear and deliberately not normalised. The series is
          genuinely lopsided: the real Chicago Open Data import all carries
          near-identical recent dates, while the synthetic records spread
          across 2024. Printing the peak keeps that legible instead of
          making the early months look like zero. */}
      <div className="telemetry mt-1 flex justify-between border-t border-rule pt-1 text-phosphor-faint">
        <span>SCALE / LINEAR</span>
        <span>
          PEAK <span className="text-phosphor">{max.toLocaleString()}</span> / MO
        </span>
      </div>
    </div>
  );
}

/** Case pipeline as a single segmented bar. */
function Pipeline({ pipeline }: { pipeline: DashboardTrends["pipeline"] }) {
  const segments = [
    { key: "OPEN", value: pipeline.open, cls: "bg-hazard" },
    { key: "INVESTIGATING", value: pipeline.investigating, cls: "bg-phosphor" },
    { key: "SOLVED", value: pipeline.solved, cls: "bg-phosphor-dim" },
    { key: "COLD", value: pipeline.cold, cls: "bg-phosphor-faint" },
  ];
  const total = pipeline.total || 1;
  return (
    <div className="p-3">
      <div className="flex h-6 w-full gap-px">
        {segments.map((s, i) => (
          <motion.div
            key={s.key}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.5, delay: 0.1 + i * 0.08, ease: [0.2, 0.8, 0.2, 1] }}
            style={{ width: `${(s.value / total) * 100}%` }}
            className={`origin-left ${s.cls}`}
            title={`${s.key}: ${s.value}`}
          />
        ))}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
        {segments.map((s) => (
          <div key={s.key} className="telemetry flex items-center gap-1.5 text-phosphor-faint">
            <span className={`h-2 w-2 ${s.cls}`} />
            {s.key}
            <span className="ml-auto tabular-nums text-phosphor">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [trends, setTrends] = useState<DashboardTrends | null>(null);
  const [gangs, setGangs] = useState<GangIntel[] | null>(null);
  const [breakdowns, setBreakdowns] = useState<DashboardBreakdowns | null>(null);
  const [operations, setOperations] = useState<DashboardOperations | null>(null);
  const [activity, setActivity] = useState<DashboardActivity | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Fired in parallel - the six endpoints are independent.
        const [k, t, g, b, o, a] = await Promise.all([
          getKpis(),
          getTrends(),
          getGangs(),
          getBreakdowns(),
          getOperations(),
          getActivity(),
        ]);
        if (cancelled) return;
        setKpis(k);
        setTrends(t);
        setGangs(g.gangs);
        setBreakdowns(b);
        setOperations(o);
        setActivity(a);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const maxCrimeType = Math.max(...(breakdowns?.crime_types.map((c) => c.count) ?? [1]));
  const maxDistrict = Math.max(...(breakdowns?.districts.map((d) => d.crimes) ?? [1]));
  const maxHotspot = Math.max(...(operations?.hotspots.map((h) => h.crimes) ?? [1]));
  const maxSeverity = Math.max(...(breakdowns?.severity.map((s) => s.count) ?? [1]));

  return (
    <main className="blueprint-grid min-h-[100dvh] px-4 py-8 sm:px-8">
      <div className="mx-auto w-full max-w-[1400px]">
        <PageHeader
          unit="D-05"
          title="Dashboard"
          subtitle="EXECUTIVE OVERVIEW // CASE LOAD, THREAT POSTURE, DATA INTEGRITY"
          right={
            activity?.peak_hour ? (
              <span className="telemetry text-phosphor-faint">
                PEAK HOUR / <span className="text-hazard">{activity.peak_hour}:00</span>
              </span>
            ) : undefined
          }
        />

        {error && (
          <div className="mb-3 border border-hazard bg-substrate-raised p-3">
            <div className="telemetry text-hazard">{"// FAULT"}</div>
            <div className="mt-1 text-[13px] text-phosphor-dim">{error}</div>
          </div>
        )}

        {/* --- PRIMARY READOUTS ------------------------------------- */}
        {!kpis ? (
          <div className="grid grid-cols-2 gap-px border border-rule bg-rule sm:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Shimmer key={i} className="h-[104px] border-0" />
            ))}
          </div>
        ) : (
          <RuledGrid className="grid-cols-2 sm:grid-cols-4">
            <Readout label="TOTAL CRIMES" value={kpis.total_crimes} max={kpis.total_crimes} index={0} />
            <Readout label="OPEN CASES" value={kpis.open_cases} max={kpis.total_crimes} index={1} />
            <Readout label="CRITICAL" value={kpis.critical_crimes} max={kpis.total_crimes} index={2} />
            <Readout
              label="SOLVE RATE"
              value={Math.round(kpis.solve_rate)}
              max={100}
              unit="%"
              index={3}
            />
          </RuledGrid>
        )}

        {kpis && (
          <RuledGrid className="mt-px grid-cols-2 sm:grid-cols-5">
            <Readout label="SUSPECTS" value={kpis.total_persons} index={0} />
            <Readout label="ORGANIZATIONS" value={kpis.total_organizations} index={1} />
            <Readout label="EVIDENCE" value={kpis.total_evidence} index={2} />
            <Readout label="WEAPONS" value={kpis.total_weapons} index={3} />
            <Readout label="DISTRICTS" value={kpis.districts.length} index={4} />
          </RuledGrid>
        )}

        {/* --- TREND + PIPELINE ------------------------------------- */}
        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_420px]">
          <Panel label="MONTHLY INCIDENT TREND" right={trends ? `${trends.monthly_trends.length} MO` : undefined}>
            {trends ? <TrendColumns data={trends.monthly_trends} /> : <div className="p-4"><LoadingBlocks /></div>}
          </Panel>

          <Panel label="CASE PIPELINE" right={trends ? `${trends.pipeline.total} TOTAL` : undefined}>
            {trends ? <Pipeline pipeline={trends.pipeline} /> : <div className="p-4"><LoadingBlocks /></div>}
          </Panel>
        </div>

        {/* --- GANG THREAT MATRIX ----------------------------------- */}
        <Panel label="GANG THREAT MATRIX" right={gangs ? `${gangs.length} ORGS` : undefined} className="mt-4">
          {gangs ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="telemetry border-b border-rule text-phosphor-faint">
                    <th className="px-3 py-2 font-normal">ORGANIZATION</th>
                    <th className="px-3 py-2 font-normal">TERRITORY</th>
                    <th className="px-3 py-2 text-right font-normal">MEMBERS</th>
                    <th className="px-3 py-2 text-right font-normal">CRIMES</th>
                    <th className="px-3 py-2 text-right font-normal">WEAPONS</th>
                    <th className="px-3 py-2 text-right font-normal">SEVERE</th>
                    <th className="px-3 py-2 font-normal">THREAT</th>
                  </tr>
                </thead>
                <tbody className="text-[12px]">
                  {gangs.map((g, i) => (
                    <motion.tr
                      key={g.gang}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.25, delay: i * 0.05 }}
                      className="border-b border-rule/60 text-phosphor-dim"
                    >
                      <td className="px-3 py-2 text-phosphor">{g.gang.toUpperCase()}</td>
                      <td className="px-3 py-2">{g.territory ?? "-"}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{g.members}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{g.crimes}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{g.weapons}</td>
                      <td className="px-3 py-2 text-right tabular-nums text-hazard">{g.severe_crimes}</td>
                      <td className="px-3 py-2">
                        {/* Threat level 1-5 as discrete blocks, matching the
                            backend's CASE-derived score exactly. */}
                        <span className="flex gap-px" title={`LEVEL ${g.threat_level} / 5`}>
                          {[1, 2, 3, 4, 5].map((n) => (
                            <span
                              key={n}
                              className={`h-3 w-2.5 ${
                                n <= g.threat_level ? "bg-hazard" : "bg-phosphor-faint/25"
                              }`}
                            />
                          ))}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4">
              <LoadingBlocks />
            </div>
          )}
        </Panel>

        {/* --- BREAKDOWNS ------------------------------------------- */}
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <Panel label="CRIME TYPE">
            {breakdowns ? (
              <div className="py-1.5">
                {breakdowns.crime_types.map((c, i) => (
                  <BarRow key={c.type} label={c.type} value={c.count} max={maxCrimeType} index={i} />
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>

          <Panel label="SEVERITY DISTRIBUTION">
            {breakdowns ? (
              <div className="py-1.5">
                {[...breakdowns.severity]
                  .sort((a, b) => SEVERITY_RANK.indexOf(a.severity) - SEVERITY_RANK.indexOf(b.severity))
                  .map((s, i) => (
                    <BarRow
                      key={s.severity}
                      label={s.severity}
                      value={s.count}
                      max={maxSeverity}
                      alert={["critical", "high", "severe"].includes(s.severity)}
                      index={i}
                    />
                  ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>

          <Panel label="DISTRICT LOAD">
            {breakdowns ? (
              <div className="py-1.5">
                {breakdowns.districts.map((d, i) => (
                  <BarRow key={d.district} label={`DIST ${d.district}`} value={d.crimes} max={maxDistrict} index={i} />
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>
        </div>

        {/* --- ASSET STATUS ----------------------------------------- */}
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Panel label="WEAPON RECOVERY STATUS">
            {breakdowns ? (
              <div className="divide-y divide-rule/60">
                {breakdowns.weapon_status.map((w) => (
                  <div key={w.type} className="flex items-center gap-3 px-3 py-2">
                    <span className="telemetry w-24 text-phosphor">{w.type}</span>
                    <span className="flex h-3 flex-1 gap-px">
                      <span
                        className="bg-phosphor"
                        style={{ width: `${(w.recovered / w.total) * 100}%` }}
                        title={`RECOVERED ${w.recovered}`}
                      />
                      <span
                        className="bg-hazard"
                        style={{ width: `${(w.at_large / w.total) * 100}%` }}
                        title={`AT LARGE ${w.at_large}`}
                      />
                    </span>
                    <span className="telemetry text-phosphor-dim">
                      {w.recovered}/{w.total} REC
                    </span>
                    {w.at_large > 0 && (
                      <span className="telemetry text-hazard">{w.at_large} AT LARGE</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>

          <Panel label="EVIDENCE VERIFICATION">
            {breakdowns ? (
              <div className="divide-y divide-rule/60">
                {breakdowns.evidence_significance.map((e) => (
                  <div key={e.significance} className="flex items-center gap-3 px-3 py-2">
                    <span className="telemetry w-24 text-phosphor">{e.significance}</span>
                    <span className="relative h-3 flex-1 bg-phosphor-faint/15">
                      <span
                        className="absolute inset-y-0 left-0 bg-phosphor"
                        style={{ width: `${(e.verified / e.total) * 100}%` }}
                      />
                    </span>
                    <span className="telemetry text-phosphor-dim">
                      {e.verified}/{e.total} VERIFIED
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>
        </div>

        {/* --- OPERATIONS ------------------------------------------- */}
        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
          <Panel label="INVESTIGATOR CASELOAD">
            {operations ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="telemetry border-b border-rule text-phosphor-faint">
                      <th className="px-3 py-2 font-normal">INVESTIGATOR</th>
                      <th className="px-3 py-2 font-normal">DEPT</th>
                      <th className="px-3 py-2 text-right font-normal">ACTIVE</th>
                      <th className="px-3 py-2 text-right font-normal">SOLVED</th>
                      <th className="px-3 py-2 text-right font-normal">RATE</th>
                    </tr>
                  </thead>
                  <tbody className="text-[12px]">
                    {operations.investigators.map((inv, ii) => (
                      <tr key={`${inv.investigator}-${ii}`} className="border-b border-rule/60 text-phosphor-dim">
                        <td className="px-3 py-1.5 text-phosphor">{inv.investigator}</td>
                        <td className="px-3 py-1.5">{inv.department ?? "-"}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums">{inv.active}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums">{inv.solved}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums text-phosphor">
                          {Math.round(inv.solve_rate)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>

          <Panel label="TOP HOTSPOTS" right={operations ? "BY VOLUME" : undefined}>
            {operations ? (
              <div className="py-1.5">
                {operations.hotspots.map((h, i) => (
                  <BarRow
                    key={`${h.location}-${i}`}
                    label={h.location}
                    value={h.crimes}
                    max={maxHotspot}
                    sub={`D${h.district ?? "-"}`}
                    alert={h.severe > 0}
                    index={i}
                  />
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>
        </div>

        {/* --- PRIORITY TARGETS + FEED ------------------------------ */}
        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
          <Panel label="PRIORITY TARGETS" right={activity ? `${activity.priority_targets.length}` : undefined}>
            {activity ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="telemetry border-b border-rule text-phosphor-faint">
                      <th className="px-3 py-2 font-normal">SUBJECT</th>
                      <th className="px-3 py-2 font-normal">AFFILIATION</th>
                      <th className="px-3 py-2 text-right font-normal">CRIMES</th>
                      <th className="px-3 py-2 text-right font-normal">ARMS</th>
                      <th className="px-3 py-2 font-normal">PRIORITY</th>
                    </tr>
                  </thead>
                  <tbody className="text-[12px]">
                    {activity.priority_targets.map((t, ti) => {
                      // Backend emits an emoji-prefixed label ("🔴 CRITICAL");
                      // strip it - emoji has no place in a monospace terminal.
                      const level = t.priority.replace(/[^\w\s]/g, "").trim();
                      const critical = level.startsWith("CRITICAL");
                      return (
                        <tr key={`${t.name}-${ti}`} className="border-b border-rule/60 text-phosphor-dim">
                          <td className="px-3 py-1.5 text-phosphor">
                            {t.name.toUpperCase()}{" "}
                            <span className="text-phosphor-faint">/{t.age}</span>
                          </td>
                          <td className="px-3 py-1.5">{t.gang}</td>
                          <td className="px-3 py-1.5 text-right tabular-nums">{t.crimes}</td>
                          <td className="px-3 py-1.5 text-right tabular-nums">{t.weapons}</td>
                          <td className="px-3 py-1.5">
                            <span
                              className={`telemetry px-1.5 py-0.5 ${
                                critical ? "bg-hazard text-substrate" : "text-phosphor-dim"
                              }`}
                            >
                              {level}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>

          <Panel label="RECENT INCIDENTS" right={activity ? "LIVE FEED" : undefined}>
            {activity ? (
              <div className="divide-y divide-rule/60">
                {activity.recent_incidents.map((inc, i) => (
                  <motion.div
                    key={inc.id}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25, delay: i * 0.04 }}
                    className="px-3 py-2"
                  >
                    <div className="telemetry flex items-center justify-between text-phosphor-faint">
                      <span>
                        {inc.date} {inc.time?.slice(0, 5) ?? ""} / DIST {inc.district}
                      </span>
                      <span
                        className={
                          ["critical", "high", "severe"].includes(inc.severity)
                            ? "text-hazard"
                            : "text-phosphor-faint"
                        }
                      >
                        {inc.severity}
                      </span>
                    </div>
                    <div className="mt-0.5 text-[12px] text-phosphor">{inc.type}</div>
                    <div className="telemetry mt-0.5 text-phosphor-dim">
                      {inc.location}
                      {inc.suspect ? ` // ${inc.suspect}` : ""}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="p-4"><LoadingBlocks /></div>
            )}
          </Panel>
        </div>

        {/* --- DATA INTEGRITY --------------------------------------- */}
        {activity && (
          <Panel label="DATA INTEGRITY FLAGS" accent className="mt-4">
            <RuledGrid className="grid-cols-2 sm:grid-cols-4 border-0">
              {[
                { label: "ORPHANED CRIMES", value: activity.data_quality.orphaned_crimes },
                { label: "NO EVIDENCE", value: activity.data_quality.no_evidence_crimes },
                { label: "UNSOLVED SEVERE", value: activity.data_quality.unsolved_severe },
                { label: "UNAFFILIATED", value: activity.data_quality.independent_suspects },
              ].map((f) => (
                <div key={f.label} className="bg-substrate-raised p-3">
                  <div className="telemetry text-phosphor-dim">{f.label}</div>
                  <AnimatedNumber
                    value={f.value}
                    className={`display mt-1 block text-2xl tabular-nums ${
                      f.value > 0 ? "text-hazard" : "text-phosphor"
                    }`}
                  />
                </div>
              ))}
            </RuledGrid>
          </Panel>
        )}

        <div className="telemetry mt-6 flex justify-between border-t border-rule pt-3 text-phosphor-faint">
          <span>{">>>"} END OF REPORT</span>
          <span>CRIMEGRAPHRAG® / REV 2.6</span>
        </div>
      </div>
    </main>
  );
}
