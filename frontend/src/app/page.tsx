"use client";

import Link from "next/link";
import {
  ChartBar,
  ChatCircleDots,
  Graph,
  MapTrifold,
  ClockCountdown,
  ShareNetwork,
  Article,
  ArrowUpRight,
} from "@phosphor-icons/react";
import { motion } from "motion/react";

// Placeholder landing page for step 11 of the FastAPI + Next.js rebuild -
// proves the "high-end-visual-design" skill (Ethereal Glass vibe, Double-
// Bezel cards, Asymmetrical Bento layout) is actually shaping output before
// building the real data pages in steps 12-19. Each card below stands in
// for one of the 8 pages being ported from the Streamlit app.

// href is set once a page's step in the rebuild plan is actually built -
// unbuilt destinations render as inert cards rather than dead links.
const destinations = [
  { label: "AI Assistant", icon: ChatCircleDots, span: "md:col-span-8 md:row-span-2", href: "/chat" },
  { label: "Dashboard", icon: ChartBar, span: "md:col-span-4", href: undefined },
  { label: "Graph Algorithms", icon: Graph, span: "md:col-span-4", href: undefined },
  { label: "Network Visualization", icon: ShareNetwork, span: "md:col-span-4", href: undefined },
  { label: "Geographic Mapping", icon: MapTrifold, span: "md:col-span-4", href: undefined },
  { label: "Timeline Analysis", icon: ClockCountdown, span: "md:col-span-4", href: undefined },
  { label: "Graph Schema", icon: Article, span: "md:col-span-4", href: undefined },
];

function DoubleBezel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-[2rem] bg-white/5 p-2 ring-1 ring-white/10 ${className}`}>
      <div className="h-full rounded-[calc(2rem-0.5rem)] bg-zinc-950/80 shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] backdrop-blur-2xl">
        {children}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <main className="relative flex min-h-[100dvh] flex-col items-center overflow-hidden px-4 py-24 sm:px-8 md:py-32">
      {/* Ethereal Glass background: deep OLED black + subtle glowing orbs */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/4 top-0 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute right-0 top-1/3 h-[28rem] w-[28rem] translate-x-1/3 rounded-full bg-emerald-500/10 blur-[120px]" />
      </div>

      <div className="mx-auto flex w-full max-w-[1400px] flex-col items-center text-center">
        <motion.span
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="rounded-full bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-zinc-400 ring-1 ring-white/10"
        >
          Knowledge Graph Intelligence
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="mt-6 max-w-3xl text-4xl font-semibold tracking-tighter text-zinc-50 md:text-6xl"
        >
          CrimeGraphRAG
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mt-4 max-w-[46ch] text-base leading-relaxed text-zinc-400"
        >
          A crime investigation platform built on a Neo4j knowledge graph,
          queried by a LangGraph agent, and served through this interface.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <Link
            href="/chat"
            className="group mt-10 flex items-center gap-3 rounded-full bg-zinc-50 py-1.5 pl-6 pr-1.5 text-sm font-medium text-zinc-950 transition-transform duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.98]"
          >
            Enter Platform
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-black/10 transition-transform duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-0.5 group-hover:-translate-y-0.5">
              <ArrowUpRight weight="bold" className="h-4 w-4" />
            </span>
          </Link>
        </motion.div>

        <div className="mt-24 grid w-full grid-cols-1 gap-4 md:grid-cols-12">
          {destinations.map(({ label, icon: Icon, span, href }, i) => {
            const card = (
              <DoubleBezel
                className={`h-full transition-colors duration-500 ${href ? "hover:bg-white/10" : ""}`}
              >
                <div className="flex h-full min-h-40 flex-col justify-between p-6 text-left">
                  <Icon weight="light" className="h-6 w-6 text-zinc-500" />
                  <span className="text-sm font-medium text-zinc-200">{label}</span>
                </div>
              </DoubleBezel>
            );

            return (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                className={span}
              >
                {href ? (
                  <Link href={href} className="block h-full">
                    {card}
                  </Link>
                ) : (
                  card
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
