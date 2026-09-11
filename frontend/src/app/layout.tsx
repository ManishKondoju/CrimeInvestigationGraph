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

const SITE_URL = "https://crime-investigation-graph.vercel.app";
const DESCRIPTION =
  "Ask a crime knowledge graph questions in plain English. A LangGraph agent writes its own Cypher, validates the result, and retries when it is wrong - and shows you every query behind its answer.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "CrimeGraphRAG // Tactical Intelligence Terminal",
  description: DESCRIPTION,
  // Without these the link shared as a blank card - no title, no image.
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "CrimeGraphRAG",
    title: "CrimeGraphRAG // Tactical Intelligence Terminal",
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: "CrimeGraphRAG // Tactical Intelligence Terminal",
    description: DESCRIPTION,
  },
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
