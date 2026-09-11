import { ImageResponse } from "next/og";

// Generated at build time rather than shipped as a static asset, so the
// card always matches the interface. Previously the site had no og/twitter
// tags at all, so sharing the link produced a blank card.

export const alt = "CrimeGraphRAG — crime investigation over a Neo4j knowledge graph";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#0a0a0a",
          color: "#eaeaea",
          fontFamily: "monospace",
          padding: 64,
          border: "10px solid #e61919",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 20, letterSpacing: 4, color: "#8a8a8a" }}>
          <span>CRIMEGRAPHRAG® / TACTICAL INTELLIGENCE TERMINAL</span>
          <span style={{ color: "#4af626" }}>● LINK ACTIVE</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", fontSize: 132, fontWeight: 900, letterSpacing: -6, lineHeight: 1 }}>
            <span>CRIME</span>
            <span style={{ color: "#e61919" }}>GRAPH</span>
          </div>
          <div style={{ fontSize: 132, fontWeight: 900, letterSpacing: -6, lineHeight: 1 }}>RAG</div>
          <div style={{ height: 6, background: "#e61919", marginTop: 28, width: 620 }} />
          <div style={{ fontSize: 26, color: "#8a8a8a", marginTop: 28, maxWidth: 900, lineHeight: 1.45 }}>
            Ask a crime knowledge graph questions in plain English. An agent
            writes its own Cypher, validates the result, and retries when it
            is wrong.
          </div>
        </div>

        {/* Satori collapses the whitespace between adjacent spans, so the
            gap between figure and label is set explicitly. */}
        <div style={{ display: "flex", gap: 56, fontSize: 22, letterSpacing: 2, color: "#8a8a8a" }}>
          {[
            ["1,868", "NODES"],
            ["2,738", "RELATIONSHIPS"],
            ["670", "CRIMES"],
            ["NEO4J", "· LANGGRAPH"],
          ].map(([figure, label]) => (
            <span key={label} style={{ display: "flex" }}>
              <span style={{ color: "#eaeaea", marginRight: 10 }}>{figure}</span>
              {label}
            </span>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
