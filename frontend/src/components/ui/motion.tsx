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
