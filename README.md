# CrimeGraphRAG – AI-Powered Crime Investigation System

An intelligent **crime investigation assistant** that combines:

- 🧠 **Large Language Models (LLMs)** for natural-language Q&A  
- 🕸️ **Neo4j knowledge graphs** for rich relationships  
- 🧭 **Graph RAG** (Retrieval-Augmented Generation) to ground answers in real data and reduce hallucinations  
- 📊 **Dashboards, network visualizations, geo-maps, and predictive insights** for investigators

> Built as part of **DAMG 7374 – Knowledge Graphs with GenAI/GraphDB (Northeastern University)**.

---

## 1. What This Project Does

**CrimeGraphRAG** turns a crime dataset into an interactive investigation tool:

- Ask questions like:
  - “Which gangs operate in Chicago?”
  - “Show me everyone connected to Marcus Rivera within 2 hops.”
  - “Which gang members own weapons and are repeat offenders?”
- See **criminal networks** as interactive graphs.
- Explore **crime hotspots, trends, and patterns** on dashboards and maps.
- Use a **conversational AI** that remembers context across turns.
- Experiment with **graph algorithms, clustering, and predictive analysis** on top of the knowledge graph.

Instead of guessing, the LLM:

1. Understands your question.
2. Generates **Cypher queries** for Neo4j.
3. Retrieves exact facts from the graph.
4. Formats a clean, natural-language explanation.

Result: **far fewer hallucinations** and **investigation-grade answers**.

---

## 2. Key Features

### 🧠 Conversational AI Assistant
- Natural-language queries over the crime graph  
- Multi-turn conversation with memory  
- Example flows:
  - “Which gangs operate in Chicago?”  
  - “Tell me more about West Side Crew.”  
  - “What crimes have they committed?”  
  - “Which of their members own weapons?”

### 🕸️ Knowledge Graph + Graph RAG
- 10+ **entity types**: Person, Crime, Organization, Location, Weapon, Vehicle, Evidence, Investigator, Modus Operandi, etc.  
- 20+ **relationship types**: `PARTY_TO`, `MEMBER_OF`, `OWNS`, `HAS_EVIDENCE`, `OCCURRED_AT`, `INVESTIGATED_BY`, `MATCHES_MO`, and more.  
- Graph RAG layer converts questions → Cypher queries → grounded answers.

### 🌐 Interactive Network Visualization
- Explore criminal networks:
  - Drag, zoom, and click nodes
  - Color-coded by entity type
  - Focus on:
    - All networks
    - Gang networks
    - A specific person

### 📊 Crime Analytics Dashboard
- High-level crime statistics  
- Crime type distribution  
- Recent activity  
- Hotspot-style insights and trends  

### 🧭 Role-Based Access Design (RBAC – Design Level)
- Conceptual roles:
  - **Detective** – full investigation view  
  - **Analyst** – pattern / aggregate views  
  - **Supervisor** – performance & caseload  
  - **Prosecutor** – case-specific views  
  - **Public** – anonymized / statistics only  
- RBAC is designed at the **architecture level**, ready for future enforcement in the app.

### 📍 Geo, Timeline, and Predictive Modules (Experimental)
Additional modules (wired or ready to be wired from `app.py`) include:

- Geo mapping & hotspot views  
- Timeline visualizations  
- Graph algorithms & clustering (e.g., hotspot prediction)  
- Early experiments with **face recognition** and **Snowflake pipelines** for scaling to larger datasets

---

## 3. Architecture (High Level)

```text
┌──────────────────────────────────────────────┐
│ USER QUESTION                               │
│ "Which gang members own weapons?"           │
└───────────────────────────────┬─────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────┐
│ GRAPH RAG LAYER (graph_rag.py)              │
│ • Parse intent / entities                   │
│ • Build Cypher queries (multi-step)         │
└───────────────────────────────┬─────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────┐
│ NEO4J KNOWLEDGE GRAPH                        │
│ • Entities + relationships                   │
│ • Executes Cypher, returns structured data   │
└───────────────────────────────┬─────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────┐
│ LLM (via OpenRouter / OpenAI-compatible API) │
│ • Summarizes and explains graph results      │
│ • Maintains conversation context             │
└───────────────────────────────┬─────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────┐
│ STREAMLIT UI (app.py + pages)               │
│ • Dashboard                                 │
│ • AI Assistant                              │
│ • Network / map / analytics views           │
└──────────────────────────────────────────────┘
```

---

## 4. Tech Stack

- **Backend & Logic**
  - Python 3.8+
  - Neo4j (Desktop or Community)
  - Official Neo4j Python driver
- **Front-End / UI**
  - Streamlit
  - Network / graph visualization libraries
- **AI / RAG**
  - LLM via **OpenRouter** (OpenAI-style API)
  - Custom Graph RAG logic for generating Cypher
- **Data & Pipelines**
  - Synthetic & hybrid Chicago-style crime datasets
  - (Planned / experimental) Snowflake ETL pipelines

---

## 5. Getting Started

### 5.1 Prerequisites

Make sure you have:

- Python **3.8+**
- Neo4j Desktop **or** Neo4j Community Edition
- `git` (optional, for cloning)

### 5.2 Clone the Repository

```bash
git clone https://github.com/ManishKondoju/CrimeInvestigationGraph.git
cd CrimeInvestigationGraph
```

### 5.3 Create and Activate a Virtual Environment

```bash
# Create venv
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate
```

### 5.4 Install Dependencies

```bash
pip install -r requirements.txt
```

If you’re deploying somewhere that uses `packages.txt`, use that file for system-level dependencies.

---

## 6. Set Up Neo4j

### Option A – Neo4j Desktop (Beginner Friendly)

1. Download Neo4j Desktop from the Neo4j site.  
2. Create a project called **CrimeGraphRAG**.  
3. Create a database:
   - Name: `crimegraph`
   - Password: any strong password (remember it).
4. Start the database.
5. Note the connection URI – usually:

```text
bolt://localhost:7687
```

### Option B – Neo4j Community Edition

```bash
# Start Neo4j
neo4j start

# Visit the browser at:
http://localhost:7474
```

Set username & password when prompted.

---

## 7. Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Inside `.env`, add:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# OpenRouter (OpenAI-compatible) key
OPENAI_API_KEY=your_openrouter_api_key_here
```

To get an OpenRouter key, create an account and generate an API key from their dashboard.

---

## 8. Load Data into Neo4j

You have multiple options depending on what you want to demo:

### 8.1 Hybrid / Enhanced Demo Dataset (Recommended)

```bash
python load_hybrid_data.py
```

This script populates Neo4j with a rich, synthetic Chicago-style crime graph (persons, crimes, gangs, locations, evidence, etc.).

### 8.2 Other Data Loaders

- `load_data.py` – base synthetic dataset loader  
- `load_real_data.py` – hook for real crime records (e.g., Chicago open data)  
- `snowflake_pipeline.py` / `snowflake_unstructured_pipeline.py` – ETL from Snowflake into the graph (experimental / for scaling demos)

### 8.3 Verify in Neo4j

Open the Neo4j browser:

```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC;
```

You should see counts for node types like `Crime`, `Person`, `Evidence`, etc.

---

## 9. Run the App

From the project root:

```bash
# (Optional) activate venv again if needed
source venv/bin/activate   # macOS / Linux
# .\venv\Scripts\Activate   # Windows

streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

Streamlit should also try to open a browser window automatically.

---

## 10. Using the Application

### 10.1 Dashboard
- View overall crime statistics  
- See crime type distribution  
- Monitor recent activity and hotspots  

### 10.2 Ask the AI Assistant
- Type questions in natural language:
  - “Which criminal organizations operate in the city?”
  - “Show me all members of West Side Crew.”
  - “What crimes have they committed?”
- Follow up without restating context.
- Clear or reset the chat when starting a new investigation.

### 10.3 Network Visualization
- Select network size (e.g., 20–100 nodes).  
- Choose focus:
  - All networks
  - Gang networks
  - A specific person
- Generate an interactive graph:
  - Drag nodes
  - Zoom in / out
  - Click nodes for details

### 10.4 Additional / Experimental Views
Depending on how `app.py` is configured, you can also wire in:

- Enhanced analytics dashboards (`enhanced_dashboard.py`)  
- Geo mapping (`enhanced_map.py`, `geo_mapping.py`)  
- Timeline visualizations (`timeline_viz.py`)  
- Schema visualization (`schema_visualizer.py`)  
- Graph algorithms & predictive insights (`graph_algorithms.py`, `predictive.py`)  
- Face recognition experiments (`face_recognition.py`)  

---

## 11. Project Structure

High-level layout:

```text
CrimeInvestigationGraph/
├── app.py                       # Main Streamlit app (navigation + layout)
├── config.py                    # Central config for models, settings, etc.
├── database.py                  # Neo4j connection and helper functions
├── graph_rag.py                 # Core Graph RAG logic (LLM + Cypher + Neo4j)
├── load_data.py                 # Base synthetic dataset loader
├── load_hybrid_data.py          # Enriched hybrid dataset loader (recommended)
├── load_real_data.py            # Hooks for real crime data ingestion
├── enhanced_dashboard.py        # Rich analytics dashboard components
├── enhanced_map.py              # Map / geo-visualization components
├── geo_mapping.py               # Geo helper utilities / mapping logic
├── graph_algorithms.py          # Graph analytics (centrality, communities, etc.)
├── network_viz.py               # Network visualization utilities
├── timeline_viz.py              # Time-based / timeline visualizations
├── predictive.py                # Predictive / hotspot-style analytics
├── schema_visualizer.py         # Visual representation of the graph schema
├── snowflake_pipeline.py        # Structured Snowflake → Neo4j ETL (experimental)
├── snowflake_unstructured_pipeline.py  # Unstructured Snowflake → Neo4j ETL
├── face_recognition.py          # Experimental face → person linking module
├── lib/                         # Shared helpers / utilities
├── requirements.txt             # Python dependencies
├── packages.txt                 # System packages for some environments
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 12. Why Graph RAG Instead of Plain Vector RAG?

**Traditional RAG (Vector DBs)**  
- Works great for unstructured documents.  
- But loses explicit relationships (`WHO knows WHO`, `WHAT links to WHAT`).  
- Good for “find me similar text”; less ideal for multi-hop reasoning.

**Graph RAG (This Project)**  
- Uses **nodes and relationships** that mirror how investigators think.  
- Supports **multi-hop queries** (“friends of friends”, “evidence that links X to Y”).  
- Lets the LLM reason over a graph-shaped context instead of a flat chunk of text.

For crime investigation, where **relationships are everything**, Graph RAG is a much closer match to the domain.

---

## 13. Research & Course Context

This project is inspired by the paper:

> *“CrimeKGQA: A Crime Investigation System Based on Knowledge Graph RAG”*  
> Kuok, Liu, Lo (2024)

Extensions in this implementation include:

- More entity types and relationships  
- A full Streamlit front-end (dashboard + chat + visualizations)  
- Conversation memory and multi-query aggregation  
- A design for RBAC and enterprise-style architecture (with Snowflake in the roadmap)

Course: **DAMG 7374 – Knowledge Graphs with GenAI/GraphDB**  
Program: **MS in Information Systems, Northeastern University**

---

## 14. Roadmap

**Current:**

- Graph RAG integration with Neo4j  
- Streamlit UI (dashboard + chat + network viz)  
- Synthetic / hybrid crime datasets  
- Early graph algorithms & hotspot-style analytics  

**In Progress / Planned:**

- Snowflake integration with 100k+ real crime records  
- More scalable ETL + data quality checks  
- Richer RBAC implementation in the UI layer  
- Advanced ML models for crime pattern prediction  
- Real-time streaming architecture concepts  
- Improved deployment story (cloud hosting, containers, etc.)

---

## 15. Contributing

Although this is an academic project, suggestions are welcome:

1. Fork the repo  
2. Create a feature branch:  
   ```bash
   git checkout -b feature/amazing-idea
   ```
3. Commit your changes:  
   ```bash
   git commit -m "Add amazing idea"
   ```
4. Push the branch and open a Pull Request.

---

## 16. License / Usage

This project is primarily for **educational and portfolio** purposes  
as part of Northeastern University coursework.

(You can add a formal `LICENSE` file if you want to open-source it under MIT / Apache-2.0.)

---

## 17. Author

**Manish Kumar Kondoju**  
MS in Information Systems – Northeastern University  

- GitHub: [@ManishKondoju](https://github.com/ManishKondoju)  
- LinkedIn: *link in profile*

---

> Built with ❤️ to explore how **knowledge graphs + GenAI** can support safer, more transparent crime investigation.
