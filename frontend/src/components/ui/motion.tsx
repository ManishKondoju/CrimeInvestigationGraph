"use client";

import { motion, useMotionValue, useSpring, useTransform } from "motion/react";
import Link from "next/link";
import { useEffect, useState } from "react";

// Shared component kit for the Tactical Telemetry interface.
// Structure comes from 1px rules, grid gaps and ASCII framing - never from
// rounded cards, gradients or soft shadows. Motion is mechanical: short,
// linear-ish, stepped, like a readout refreshing rather than a UI easing.

/** Mechanical curve - decisive, minimal overshoot. */
export const EASE = [0.2, 0.8, 0.2, 1] as const;

/* ------------------------------------------------------------------ */
/* STRUCTURE                                                           */
/* ------------------------------------------------------------------ */

/**
 * The core compartment. A hard-edged bordered zone with an optional
 * label bar - the interface's only container primitive.
 */
export function Panel({
  children,
  label,
  right,
  className = "",
  accent = false,
}: {
  children: React.ReactNode;
  label?: string;
  right?: React.ReactNode;
  className?: string;
  accent?: boolean;
}) {
  return (
    <section
      className={`border bg-substrate-raised ${accent ? "border-hazard" : "border-rule"} ${className}`}
    >
      {label && (
        <header
          className={`flex items-center justify-between border-b px-3 py-1.5 ${
            accent ? "border-hazard bg-hazard text-substrate" : "border-rule text-phosphor-dim"
          }`}
        >
          <span className="telemetry">{label}</span>
          {right && <span className="telemetry">{right}</span>}
        </header>
      )}
      {children}
    </section>
  );
}

/**
 * Grid-gap hairline technique: a 1px-gap grid over a rule-colored
 * background yields mathematically perfect dividers with no borders.
 */
export function RuledGrid({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`grid gap-px border border-rule bg-rule ${className}`}>{children}</div>
  );
}

/** Full-width segregating rule with an optional inline caption. */
export function SectionRule({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-3">
      <span className="h-px flex-1 bg-rule" />
      {label && <span className="telemetry text-phosphor-faint">{label}</span>}
      <span className="h-px flex-1 bg-rule" />
    </div>
  );
}

/** Crosshair registration mark for grid intersections. */
export function Crosshair({ className = "" }: { className?: string }) {
  return (
    <span className={`pointer-events-none select-none text-phosphor-faint ${className}`}>+</span>
  );
}

/* ------------------------------------------------------------------ */
/* READOUTS                                                            */
/* ------------------------------------------------------------------ */

/**
 * Telemetry readout: label, counted-up value, and an 8-cell bar gauge.
 * The gauge is the app's signature data mark - discrete blocks, never a
 * smooth progress bar.
 */
export function Readout({
  label,
  value,
  max,
  unit,
  index = 0,
}: {
  label: string;
  value: number | string;
  max?: number;
  unit?: string;
  index?: number;
}) {
  const numeric = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
  const isNumeric = Number.isFinite(numeric);
  const filled = max && isNumeric ? Math.round((Math.min(numeric, max) / max) * 8) : 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.25, delay: index * 0.05 }}
      className="bg-substrate-raised p-3"
    >
      <div className="telemetry text-phosphor-dim">{label}</div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <AnimatedNumber
          value={value}
          className="display text-3xl tabular-nums text-phosphor"
        />
        {unit && <span className="telemetry text-phosphor-faint">{unit}</span>}
      </div>
      {max !== undefined && (
        <div className="mt-2 flex gap-px" aria-hidden>
          {Array.from({ length: 8 }).map((_, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.15, delay: index * 0.05 + i * 0.04 }}
              className={`h-1.5 flex-1 ${i < filled ? "bg-hazard" : "bg-phosphor-faint/30"}`}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

/** Counts up to `value`. Re-runs whenever the value changes. */
export function AnimatedNumber({
  value,
  className = "",
}: {
  value: number | string;
  className?: string;
}) {
  const numeric = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
  const isNumeric = Number.isFinite(numeric);

  const mv = useMotionValue(0);
  const spring = useSpring(mv, { stiffness: 120, damping: 24, mass: 0.5 });
  const text = useTransform(spring, (v) => Math.round(v).toLocaleString());
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (isNumeric) mv.set(numeric);
  }, [numeric, isNumeric, mv]);

  useEffect(() => text.on("change", setDisplay), [text]);

  if (!isNumeric) return <span className={className}>{value}</span>;
  return <span className={className}>{display}</span>;
}

/* ------------------------------------------------------------------ */
/* MOTION                                                              */
/* ------------------------------------------------------------------ */

/** Entry: a short mechanical slide + clip, no blur or float. */
export function Reveal({
  children,
  index = 0,
  className = "",
}: {
  children: React.ReactNode;
  index?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.4, delay: index * 0.04, ease: EASE }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * Types a string out character by character, like a terminal writing to
 * screen. Used for headers so pages "boot" rather than fade in.
 */
export function TypeOut({
  text,
  className = "",
  speed = 28,
  startDelay = 0,
}: {
  text: string;
  className?: string;
  speed?: number;
  startDelay?: number;
}) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    let i = 0;
    let interval: ReturnType<typeof setInterval>;
    // Reset and tick from inside timers rather than synchronously in the
    // effect body, so this never cascades a render on mount.
    const start = setTimeout(() => {
      setShown(0);
      interval = setInterval(() => {
        i += 1;
        setShown(i);
        if (i >= text.length) clearInterval(interval);
      }, speed);
    }, startDelay);
    return () => {
      clearTimeout(start);
      clearInterval(interval);
    };
  }, [text, speed, startDelay]);

  return (
    <span className={className}>
      {text.slice(0, shown)}
      {shown < text.length && <span className="animate-pulse text-hazard">_</span>}
    </span>
  );
}

/** Live-connection indicator - the ONE place terminal green appears. */
export function StatusLight({ label = "LINK ACTIVE" }: { label?: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <motion.span
        className="h-1.5 w-1.5 bg-terminal"
        animate={{ opacity: [1, 0.25, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      />
      <span className="telemetry text-phosphor-dim">{label}</span>
    </span>
  );
}

/** Blocky loading state - marching blocks, not a spinner. */
export function LoadingBlocks({ label = "LOADING" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="flex gap-px">
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-1.5 bg-hazard"
            animate={{ opacity: [0.2, 1, 0.2] }}
            transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.1, ease: "linear" }}
          />
        ))}
      </span>
      <span className="telemetry text-phosphor-dim">{label}</span>
    </div>
  );
}

/** Skeleton block that sweeps, matching the hard-edged aesthetic. */
export function Shimmer({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden border border-rule bg-substrate-raised ${className}`}>
      <motion.div
        className="absolute inset-y-0 w-1/3 bg-phosphor/5"
        animate={{ x: ["-120%", "420%"] }}
        transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* CONTROLS                                                            */
/* ------------------------------------------------------------------ */

/** Mode selector rendered as bracketed terminal options. */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  layoutId?: string;
}) {
  return (
    <div className="flex border border-rule">
      {options.map((opt, i) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`telemetry flex-1 px-2 py-2 transition-colors duration-150 ${
            i > 0 ? "border-l border-rule" : ""
          } ${
            value === opt
              ? "bg-hazard text-substrate"
              : "bg-substrate-raised text-phosphor-dim hover:text-phosphor"
          }`}
        >
          {value === opt ? `[${opt}]` : opt}
        </button>
      ))}
    </div>
  );
}

/** Square utilitarian action button. */
export function TerminalButton({
  children,
  onClick,
  type = "button",
  disabled = false,
  accent = false,
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  accent?: boolean;
  className?: string;
}) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.1 }}
      className={`telemetry border px-3 py-2 transition-colors duration-150 disabled:opacity-30 ${
        accent
          ? "border-hazard bg-hazard text-substrate hover:bg-transparent hover:text-hazard"
          : "border-rule bg-substrate-raised text-phosphor-dim hover:border-phosphor hover:text-phosphor"
      } ${className}`}
    >
      {children}
    </motion.button>
  );
}

/** Return-to-index control, rendered as a terminal command. */
export function BackLink({ href = "/" }: { href?: string }) {
  return (
    <Link
      href={href}
      className="telemetry group flex items-center gap-2 border border-rule bg-substrate-raised px-3 py-2 text-phosphor-dim transition-colors duration-150 hover:border-hazard hover:text-hazard"
    >
      <span className="transition-transform duration-150 group-hover:-translate-x-0.5">{"<<"}</span>
      INDEX
    </Link>
  );
}

/** Standard page header: unit ID, typed title, status strip. */
export function PageHeader({
  unit,
  title,
  subtitle,
  right,
}: {
  unit: string;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-6 border-b border-rule pb-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BackLink />
          <span className="telemetry text-phosphor-faint">UNIT / {unit}</span>
        </div>
        <div className="flex items-center gap-4">
          {right}
          <StatusLight />
        </div>
      </div>
      <h1 className="display text-[clamp(1.8rem,5vw,3.2rem)] text-phosphor">
        <TypeOut text={title} />
      </h1>
      {subtitle && <p className="telemetry mt-2 text-phosphor-dim">{subtitle}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* DISPATCH                                                            */
/* ------------------------------------------------------------------ */

/**
 * Rotating emergency beacon, drawn rather than photographed - a stock
 * siren image would break the system's typographic/technical discipline
 * and carry licensing baggage for no benefit.
 */
export function SirenBeacon({ size = 44 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden
      className="shrink-0"
    >
      {/* Sweeping light cone */}
      <g className="beacon-sweep">
        <path d="M24 22 L46 10 L46 34 Z" fill="var(--hazard)" opacity="0.16" />
        <path d="M24 22 L2 10 L2 34 Z" fill="var(--hazard)" opacity="0.16" />
      </g>

      {/* Lamp dome */}
      <path
        d="M14 24 A10 10 0 0 1 34 24 Z"
        fill="var(--hazard)"
        className="beacon-lamp"
      />
      {/* Housing + base, squared off to match the system's geometry */}
      <rect x="12" y="24" width="24" height="4" fill="var(--phosphor-dim)" />
      <rect x="15" y="28" width="18" height="7" fill="var(--phosphor-faint)" />
      <rect x="11" y="35" width="26" height="3" fill="var(--phosphor-dim)" />
    </svg>
  );
}

export interface TickerIncident {
  id: string;
  type: string;
  date: string;
  time: string | null;
  severity: string;
  status: string;
  location: string;
  district: string;
  suspect: string | null;
}

/**
 * Endless dispatch feed of real incidents from the graph.
 *
 * The track renders the list TWICE and scrolls exactly -50%: at the end of
 * the animation the second copy sits precisely where the first started, so
 * the loop has no visible seam and no JS is involved in the scrolling.
 */
export function IncidentTicker({ incidents }: { incidents: TickerIncident[] }) {
  if (incidents.length === 0) return null;

  const severe = (s: string) => ["critical", "high", "severe"].includes(s.toLowerCase());

  const Item = ({ inc }: { inc: TickerIncident }) => (
    <div className="flex shrink-0 items-center gap-3 border-r border-rule px-5 py-2.5">
      <span className={`h-2 w-2 shrink-0 ${severe(inc.severity) ? "bg-hazard" : "bg-phosphor-faint"}`} />
      <span className="telemetry text-phosphor-faint">
        {inc.date}
        {inc.time ? ` ${inc.time.slice(0, 5)}` : ""}
      </span>
      <span className="telemetry text-phosphor">{inc.type}</span>
      <span className="telemetry text-phosphor-dim">DIST {inc.district}</span>
      <span className="telemetry max-w-[22ch] truncate text-phosphor-dim" title={inc.location}>
        {inc.location}
      </span>
      {inc.suspect && (
        <span className="telemetry text-phosphor-faint">
          {"// "}
          {inc.suspect.toUpperCase()}
        </span>
      )}
      <span className={`telemetry ${severe(inc.severity) ? "text-hazard" : "text-phosphor-faint"}`}>
        [{inc.severity.toUpperCase()}]
      </span>
    </div>
  );

  return (
    <div className="relative overflow-hidden border-y border-rule bg-substrate-raised">
      {/* Fixed label rides above the moving feed */}
      <div className="absolute inset-y-0 left-0 z-10 flex items-center gap-2 border-r border-hazard bg-hazard px-3">
        <span className="telemetry text-substrate">● LIVE DISPATCH</span>
      </div>

      <div className="ticker-track pl-[168px]">
        {/* Two copies - see the -50% translate above */}
        {[0, 1].map((copy) => (
          <div key={copy} className="flex" aria-hidden={copy === 1}>
            {incidents.map((inc) => (
              <Item key={`${copy}-${inc.id}`} inc={inc} />
            ))}
          </div>
        ))}
      </div>

      {/* Edge fades so items enter and leave rather than popping */}
      <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-substrate-raised to-transparent" />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* IDLE CONSTELLATION                                                  */
/* ------------------------------------------------------------------ */

// The real schema, not decorative noise: these are the graph's actual node
// labels and the actual relationships between them, so the standby visual
// doubles as a legend for what can be asked about.
//
// Positions are fixed rather than randomised - this renders inside a client
// component that Next still server-renders, and Math.random() would produce
// different coordinates on server and client, causing a hydration mismatch.
const CONSTELLATION_NODES: {
  id: string;
  label: string;
  x: number;
  y: number;
  hub?: boolean;
}[] = [
  { id: "mo", label: "MODUS OPERANDI", x: 232, y: 34 },
  { id: "loc", label: "LOCATION", x: 104, y: 92 },
  { id: "inv", label: "INVESTIGATOR", x: 150, y: 176 },
  { id: "crime", label: "CRIME", x: 322, y: 112, hub: true },
  { id: "evi", label: "EVIDENCE", x: 330, y: 196 },
  { id: "weapon", label: "WEAPON", x: 486, y: 188 },
  { id: "person", label: "PERSON", x: 566, y: 96, hub: true },
  { id: "org", label: "ORGANIZATION", x: 724, y: 46 },
  { id: "veh", label: "VEHICLE", x: 716, y: 172 },
];

const CONSTELLATION_EDGES: [string, string][] = [
  ["crime", "loc"],
  ["crime", "inv"],
  ["crime", "evi"],
  ["crime", "mo"],
  ["crime", "weapon"],
  ["crime", "veh"],
  ["person", "crime"],
  ["person", "org"],
  ["person", "weapon"],
  ["person", "veh"],
  ["evi", "person"],
];

/**
 * Ambient knowledge-graph constellation for the assistant's idle state.
 * Pure SVG + CSS animation - no canvas, no per-frame JS.
 */
export function GraphConstellation() {
  const byId = Object.fromEntries(CONSTELLATION_NODES.map((n) => [n.id, n]));

  return (
    <div className="pointer-events-none relative flex w-full items-center justify-center py-4">
      <svg
        viewBox="0 0 828 230"
        className="w-full max-w-4xl"
        aria-hidden
        role="presentation"
      >
        <defs>
          {/* Soft bloom around each node */}
          <filter id="node-bloom" x="-140%" y="-140%" width="380%" height="380%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {CONSTELLATION_EDGES.map(([a, b], i) => (
          <line
            key={`${a}-${b}`}
            x1={byId[a].x}
            y1={byId[a].y}
            x2={byId[b].x}
            y2={byId[b].y}
            stroke="var(--node-glow)"
            strokeOpacity={0.22}
            strokeWidth={1}
            className="constellation-edge"
            style={{ animationDelay: `${i * 0.35}s` }}
          />
        ))}

        {CONSTELLATION_NODES.map((n, i) => {
          const r = n.hub ? 7 : 4.5;
          return (
            <g
              key={n.id}
              className="constellation-node"
              style={{
                animationDelay: `${i * 0.55}s`,
                animationDuration: `${6.5 + (i % 4)}s`,
              }}
            >
              {/* Halo sits behind the core and breathes independently */}
              <circle
                cx={n.x}
                cy={n.y}
                r={r * 3}
                fill="var(--node-glow)"
                fillOpacity={0.07}
                className="constellation-halo"
                style={{ animationDelay: `${i * 0.4}s` }}
              />
              <circle
                cx={n.x}
                cy={n.y}
                r={r}
                fill="var(--node-glow)"
                filter="url(#node-bloom)"
                opacity={n.hub ? 0.95 : 0.75}
              />
              {/* Hubs get a ring so the two anchor entities read as primary */}
              {n.hub && (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={r + 5}
                  fill="none"
                  stroke="var(--node-glow)"
                  strokeOpacity={0.35}
                  strokeWidth={1}
                />
              )}
              <text
                x={n.x}
                y={n.y + (n.hub ? 26 : 20)}
                textAnchor="middle"
                className="fill-phosphor-dim"
                style={{
                  // 8px at 0.45 opacity on this substrate was effectively
                  // invisible - the labels are what make this read as a
                  // knowledge graph rather than abstract dots.
                  fontSize: 9.5,
                  letterSpacing: "0.12em",
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                  opacity: n.hub ? 0.95 : 0.68,
                }}
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* MODULE PREVIEWS                                                     */
/* ------------------------------------------------------------------ */

/**
 * AI ASSISTANT preview: an analyst seated at a console while the agent
 * writes a transcript back to them.
 *
 * Drawn rather than illustrated with an asset - a stock image would break
 * the system's line-work discipline. Sits behind the card's label layer,
 * so the title stays readable at all times.
 */
export function AssistantPreview() {
  // Response lines: x-offset, width, and the delay that staggers them so
  // the transcript appears to stream rather than land all at once.
  const lines: [number, number, number][] = [
    [150, 92, 1.5],
    [150, 118, 1.9],
    [150, 74, 2.3],
    [150, 104, 2.7],
  ];

  return (
    <svg
      viewBox="0 0 320 150"
      // Anchored to the card's right edge at its natural aspect rather than
      // stretched across it: the card is far wider than the scene, and
      // slicing to fill cropped the composition badly. This also keeps the
      // left of the card clear for the title.
      className="preview-scene pointer-events-none absolute bottom-0 right-0 top-0 h-full w-auto"
      preserveAspectRatio="xMaxYMid meet"
      aria-hidden
      role="presentation"
    >
      {/* Console glow pooled on the desk */}
      <ellipse cx="212" cy="118" rx="86" ry="9" fill="var(--hazard)" opacity="0.06" />

      {/* Desk */}
      <rect x="16" y="116" width="288" height="1.5" fill="var(--phosphor-faint)" opacity="0.55" />

      {/* Seated operator, back to us, facing the console */}
      <g className="preview-operator" opacity="0.62">
        {/* chair back */}
        <rect x="40" y="86" width="3" height="30" fill="var(--phosphor-faint)" />
        <rect x="40" y="84" width="26" height="3" fill="var(--phosphor-faint)" />
        {/* torso */}
        <path
          d="M56 116 L60 82 Q72 74 84 82 L88 116 Z"
          fill="none"
          stroke="var(--phosphor-dim)"
          strokeWidth="1.6"
        />
        {/* head */}
        <circle cx="72" cy="64" r="11" fill="none" stroke="var(--phosphor-dim)" strokeWidth="1.6" />
        {/* arm reaching to the keyboard */}
        <path
          d="M86 92 Q104 96 116 108"
          fill="none"
          stroke="var(--phosphor-dim)"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </g>

      {/* Keyboard */}
      <rect x="112" y="110" width="34" height="4" fill="var(--phosphor-faint)" opacity="0.7" />

      {/* Console screen */}
      <g>
        <rect
          x="140"
          y="26"
          width="158"
          height="78"
          fill="var(--substrate)"
          stroke="var(--rule)"
          strokeWidth="1.2"
        />
        {/* screen header bar */}
        <rect x="140" y="26" width="158" height="9" fill="var(--rule)" opacity="0.6" />
        <circle cx="147" cy="30.5" r="1.6" fill="var(--hazard)" />

        {/* the analyst's query, in hazard */}
        <rect
          className="preview-line"
          x="148"
          y="44"
          width="72"
          height="3"
          rx="0"
          fill="var(--hazard)"
          style={{ animationDelay: "0s" }}
        />

        {/* agent response streaming back */}
        {lines.map(([x, w, delay], i) => (
          <rect
            key={i}
            className="preview-line"
            x={x - 2}
            y={56 + i * 9}
            width={w}
            height={2.5}
            fill="var(--phosphor-dim)"
            opacity="0.85"
            style={{ animationDelay: `${delay}s` }}
          />
        ))}

        {/* caret */}
        <rect className="preview-caret" x="148" y="92" width="5" height="3" fill="var(--hazard)" />
      </g>

      {/* Monitor stand */}
      <rect x="212" y="104" width="4" height="10" fill="var(--phosphor-faint)" opacity="0.7" />
      <rect x="200" y="114" width="28" height="2" fill="var(--phosphor-faint)" opacity="0.7" />
    </svg>
  );
}
