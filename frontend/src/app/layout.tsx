import type { Metadata } from "next";
import { JetBrains_Mono, Archivo_Black } from "next/font/google";
import "./globals.css";

// Micro-typography: all telemetry, metadata, tables, IDs, coordinates.
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

// Macro-typography: structural headers only, always uppercase.
const archivoBlack = Archivo_Black({
  variable: "--font-archivo-black",
  weight: "400",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CRIMEGRAPHRAG // TACTICAL INTELLIGENCE TERMINAL",
  description:
    "Crime investigation platform powered by a Neo4j knowledge graph and a LangGraph agent",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${jetbrainsMono.variable} ${archivoBlack.variable} h-full`}
    >
      {/* Scanlines + grain are applied once at the root so the whole
          terminal shares one continuous simulated-hardware surface. */}
      <body className="crt-scanlines crt-noise min-h-full bg-substrate text-phosphor">
        {children}
      </body>
    </html>
  );
}
