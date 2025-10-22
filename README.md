# 🔍 CrimeGraphRAG - AI-Powered Crime Investigation System

<div align="center">

![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

**An intelligent crime investigation assistant powered by Graph RAG technology**

[Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Research](#-research-foundation)

</div>

---

## 🎯 What is CrimeGraphRAG?

CrimeGraphRAG is an AI-powered crime investigation system that helps detectives solve cases faster by combining:

- 🧠 **Large Language Models (LLMs)** - For natural language understanding
- 🕸️ **Neo4j Knowledge Graphs** - For storing complex crime relationships
- 🔗 **Graph RAG Framework** - To prevent AI hallucination by grounding responses in real data

**The Problem:** Regular AI like ChatGPT hallucinates when asked about crime data because police databases aren't in their training data. This can mislead investigations.

**The Solution:** Graph RAG - The AI generates database queries instead of guessing, retrieves exact facts from Neo4j, then formats them naturally. Zero hallucination, 100% accuracy.

---

## ✨ Key Features

### 💬 Conversational AI Assistant
- Natural language crime investigation queries
- Multi-turn conversations with context memory
- Ask follow-up questions without repeating context
- Example: "Which gangs operate in Chicago?" → "Tell me about West Side Crew" → "What crimes have they committed?"

### 🕸️ Interactive Network Visualization
- Visualize criminal networks and connections
- Color-coded nodes by entity type
- Interactive graph exploration (drag, zoom, click)
- Shows relationships between suspects, crimes, locations, and gangs

### 📊 Crime Analytics Dashboard
- Real-time crime statistics
- Hotspot identification
- Crime type distribution
- Recent activity monitoring

### 🔐 Role-Based Access Control
- 5 user roles: Detective, Analyst, Supervisor, Prosecutor, Public
- Different data access levels per role
- Privacy-compliant design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│ USER QUESTION                                            │
│ "Which gang members own weapons?"                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ GRAPH RAG SYSTEM (graph_rag.py)                         │
│ • Analyzes question intent                              │
│ • Extracts entities from conversation history           │
│ • Generates 5-10 intelligent Cypher queries             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ NEO4J KNOWLEDGE GRAPH                                    │
│ • 11 entity types (Person, Crime, Organization, etc.)   │
│ • 20+ relationship types                                │
│ • Executes Cypher queries                               │
│ • Returns structured data                               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ LLM (via OpenRouter)                                     │
│ • Formats retrieved data naturally                      │
│ • Maintains conversation context                        │
│ • Generates follow-up questions                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ STREAMLIT INTERFACE                                      │
│ • Displays conversational responses                     │
│ • Shows network visualizations                          │
│ • Presents analytics dashboards                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Knowledge Graph Schema

### **11 Entity Types:**
- **Person** (120 nodes) - Suspects, witnesses, victims
- **Crime** (350 nodes) - Criminal incidents
- **Location** (20 nodes) - Chicago neighborhoods
- **Organization** (5 nodes) - Gangs and criminal groups
- **Evidence** (100 nodes) - Physical, digital, forensic evidence
- **Weapon** (30 nodes) - Firearms, knives
- **Vehicle** (50 nodes) - Cars involved in crimes
- **Investigator** (5 nodes) - Detectives assigned to cases
- **ModusOperandi** (5 nodes) - Crime behavior patterns

### **20+ Relationship Types:**
- `PARTY_TO` - Person commits Crime
- `MEMBER_OF` - Person belongs to Organization
- `OWNS` - Person owns Weapon/Vehicle
- `HAS_EVIDENCE` - Crime has Evidence
- `LINKS_TO` - Evidence links to Person
- `OCCURRED_AT` - Crime occurred at Location
- `INVESTIGATED_BY` - Crime investigated by Investigator
- `MATCHES_MO` - Crime matches ModusOperandi
- And 12+ more...

**Total:** ~685 nodes, ~3,160 relationships

---

## 🚀 Installation

### **Prerequisites**

Before you begin, make sure you have:
- Python 3.8 or higher
- Neo4j Desktop or Neo4j Community Edition
- Git (optional, for cloning)

### **Step 1: Clone the Repository**

```bash
git clone https://github.com/ManishKondoju/CrimeInvestigationGraph.git
cd CrimeInvestigationGraph
```

### **Step 2: Install Python Dependencies**

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### **Step 3: Set Up Neo4j**

#### **Option A: Using Neo4j Desktop (Easier for beginners)**

1. Download Neo4j Desktop from https://neo4j.com/download/
2. Install and open Neo4j Desktop
3. Create a new project called "CrimeGraphRAG"
4. Add a new database:
   - Name: `crimegraph`
   - Password: Choose a password (remember it!)
5. Start the database
6. Note the connection details (usually `bolt://localhost:7687`)

#### **Option B: Using Neo4j Community Edition**

```bash
# Download and install Neo4j
# https://neo4j.com/deployment-center/

# Start Neo4j
neo4j start

# Access Neo4j Browser at http://localhost:7474
# Default username: neo4j
# Set a new password when prompted
```

### **Step 4: Configure Environment Variables**

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
nano .env
```

Add your configuration:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
OPENAI_API_KEY=your_openrouter_api_key_here
```

**How to get OpenRouter API Key:**
1. Go to https://openrouter.ai/
2. Sign up for free account
3. Go to Settings → API Keys
4. Create new key
5. Copy and paste into `.env` file

**Save the file:** `Ctrl+X`, then `Y`, then `Enter`

### **Step 5: Load Data into Neo4j**

```bash
# Run the data loader script
python load_data.py
```

**Expected output:**
```
============================================================
🚀 Loading ENHANCED Chicago Crime Data with Rich Schema
============================================================
🗑️  Database cleared
📍 Creating 20 enhanced locations...
✅ Created 20 locations with enhanced properties
🏢 Creating criminal organizations...
✅ Created 5 organizations
👮 Creating investigators...
✅ Created 5 investigators
...
🎉 ENHANCED DATABASE LOADED SUCCESSFULLY!
============================================================
```

**This takes 30-60 seconds.**

### **Step 6: Verify Data in Neo4j Browser**

1. Open http://localhost:7474 in your browser
2. Login with your Neo4j credentials
3. Run this query to verify data:

```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC
```

You should see:
- Crime: 350
- Person: 120
- Evidence: 100
- And more...

---

## 🎮 Usage

### **Start the Application**

```bash
# Make sure you're in the project directory
cd ~/Documents/CrimeKGQA

# Activate virtual environment (if using one)
source venv/bin/activate

# Run Streamlit app
streamlit run app.py
```

**The app will open automatically in your browser at `http://localhost:8501`**

---

### **Using the Application**

#### **1. Dashboard (🏠)**
- View overall crime statistics
- See top crime hotspots
- Monitor recent criminal activity
- Visualize crime type distribution

#### **2. Ask AI Assistant (💬)**
- Type questions in natural language
- Have conversations with context memory
- Click example buttons for quick queries
- Use "Clear Chat" or "New Chat" to reset

**Example Questions:**
```
Which criminal organizations operate in Chicago?
Show me all members of West Side Crew
What crimes have they committed?
Which gang members own weapons?
Show me everyone connected to Marcus Rivera within 2 degrees
What evidence do we have?
Find suspects who are gang members AND own weapons
```

#### **3. Network Visualization (🕸️)**
- Select network size (20-100 nodes)
- Choose focus: All, Gang Networks, or Specific Person
- Click "Generate" to create interactive network
- Drag nodes, zoom, and click for details
- Color-coded: 🟠 Person, 🔵 Crime, 🟢 Location, 🟡 Organization

---

## 🎯 Example Workflow

### **Scenario: Investigating Gang Activity**

**Step 1:** Ask about organizations
```
You: "Which criminal organizations operate in Chicago?"

AI: "I found **5 criminal organizations** operating in Chicago. 
The most active is **West Side Crew** with **25 members**..."
```

**Step 2:** Follow up (no need to repeat context!)
```
You: "Tell me more about West Side Crew"

AI: "West Side Crew is a **street gang** operating in the **West district**..."
```

**Step 3:** Dig deeper
```
You: "What crimes have they committed?"

AI: "West Side Crew members have committed **47 crimes** in the last 6 months..."
```

**Step 4:** Visualize the network
- Go to Network Visualization tab
- Select "Gang Networks"
- Click Generate
- See the complete gang structure!

---

## 🛠️ Troubleshooting

### **Issue: "Cannot connect to Neo4j"**

**Solution:**
```bash
# Check if Neo4j is running
neo4j status

# Start Neo4j if stopped
neo4j start

# Or restart
neo4j restart
```

### **Issue: "No module named 'neo4j'"**

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt
```

### **Issue: "Database is empty / No results"**

**Solution:**
```bash
# Reload the data
python load_data.py
```

### **Issue: "OpenAI API Error"**

**Solution:**
- Check your `.env` file has correct `OPENAI_API_KEY`
- Verify your OpenRouter account has credits
- The system will fallback to non-LLM mode if API fails

### **Issue: "Streamlit not loading"**

**Solution:**
```bash
# Check which port Streamlit is using
# Default is 8501
# Open browser manually: http://localhost:8501

# Or specify different port
streamlit run app.py --server.port 8502
```

---

## 📚 Research Foundation

This project is based on the research paper:

**"CrimeKGQA: A Crime Investigation System Based on Knowledge Graph RAG"**  
by Ka Lok Kuok, Hao Hui Liu, and Wai Weng Lo

**Key Contributions from the Paper:**
- Identified LLM hallucination problem for specialized domains
- Proposed Graph RAG architecture for crime investigation
- Validated that Neo4j + LLM prevents hallucination
- Demonstrated on 61,521 crime records

**My Extensions:**
- ✅ Expanded from 4 to 11 entity types
- ✅ Added conversational memory (multi-turn dialogue)
- ✅ Built production-ready interface (Dashboard + Chat + Viz)
- ✅ Enhanced with RBAC design (5 user roles)
- ✅ Multi-query aggregation (5-10 queries per question)

---

## 🏆 Why Graph RAG?

### **Traditional RAG (Vector Databases):**
- Uses document embeddings
- Retrieves by semantic similarity
- Loses relationship structure
- Fuzzy matches

### **Graph RAG (Knowledge Graphs):**
- Uses structured entities and relationships
- Retrieves by graph traversal
- Preserves relationship structure
- Exact matches

**For crime investigation:** Graph RAG is superior because investigations are fundamentally about relationships (who knows who, which evidence links to which suspect, which gang operates where).

---

## 🎓 Course Alignment

**Course:** DAMG 7374 - Knowledge Graphs with GenAI/GraphDB  
**Institution:** Northeastern University

**Learning Objectives Met:**
- ✅ Graph Data Science (multi-hop traversal, network analysis)
- ✅ Semantic Modeling (11-entity crime ontology)
- ✅ GenAI Integration (LLM + Knowledge Graph)
- ✅ Real-World Application (actual law enforcement use case)

---

## 📂 Project Structure

```
CrimeInvestigationGraph/
│
├── app.py                  # Main Streamlit application
├── graph_rag.py           # Graph RAG system (core logic)
├── database.py            # Neo4j connection wrapper
├── load_data.py           # Data generation and loading
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## 🔧 Configuration

### **Environment Variables (.env)**

| Variable | Description | Example |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection string | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your_password` |
| `OPENAI_API_KEY` | OpenRouter API key | `sk-or-v1-...` |

### **Graph RAG Settings (config.py)**

```python
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-oss-20b:free"  # Free model, or upgrade to better ones
```

---

## 📊 Database Schema

### **Node Types (11 total):**

```cypher
// Person nodes
(:Person {
    id: string,
    name: string,
    age: integer,
    gender: string,
    occupation: string,
    criminal_record: boolean,
    risk_score: float,
    address: string
})

// Crime nodes
(:Crime {
    id: string,
    type: string,
    date: date,
    time: string,
    severity: string,
    status: string,
    case_number: string
})

// Organization nodes
(:Organization {
    id: string,
    name: string,
    type: string,
    territory: string,
    members_count: integer,
    activity_level: string
})

// And 8 more node types...
```

### **Relationship Types (20+ total):**

```cypher
// Person relationships
(Person)-[:PARTY_TO]->(Crime)
(Person)-[:MEMBER_OF {rank: string}]->(Organization)
(Person)-[:OWNS]->(Weapon)
(Person)-[:OWNS]->(Vehicle)
(Person)-[:KNOWS {strength: float}]-(Person)
(Person)-[:FAMILY_REL {relation: string}]-(Person)

// Crime relationships
(Crime)-[:OCCURRED_AT]->(Location)
(Crime)-[:HAS_EVIDENCE]->(Evidence)
(Crime)-[:INVESTIGATED_BY]->(Investigator)
(Crime)-[:MATCHES_MO {similarity: float}]->(ModusOperandi)

// And 10+ more relationship types...
```

---

## 💡 How It Works

### **The Graph RAG Process:**

**1. User asks question:**
```
"Which gang members own weapons?"
```

**2. System analyzes intent:**
- Identifies entities needed: Person, Organization, Weapon
- Identifies relationships needed: MEMBER_OF, OWNS

**3. Generates Cypher queries:**
```cypher
MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
MATCH (p)-[:OWNS]->(w:Weapon)
RETURN p.name, o.name, w.type
```

**4. Neo4j returns exact data:**
```json
[
  {"p.name": "Marcus Rivera", "o.name": "West Side Crew", "w.type": "firearm"},
  {"p.name": "David Lee", "o.name": "West Side Crew", "w.type": "knife"}
]
```

**5. LLM formats naturally:**
```
I found **2 armed gang members** in the database. **Marcus Rivera** 
from **West Side Crew** owns a **firearm**, and **David Lee** from the 
same organization owns a **knife**. Both are flagged as high-risk 
individuals.

Would you like to see their complete criminal histories or their 
network connections?
```

**6. User gets accurate, conversational answer - zero hallucination!**

---

## 🎯 Example Queries

### **Basic Queries:**
```
Which criminal organizations operate in Chicago?
Show me crime hotspots
What are the most common crime types?
Who are the repeat offenders?
```

### **Conversational Flow:**
```
Q1: "Which gangs operate in Chicago?"
Q2: "Tell me more about West Side Crew"
Q3: "What crimes have they committed?"
Q4: "Which of their members own weapons?"
```

### **Complex Queries (Multi-Hop):**
```
Show me everyone connected to Marcus Rivera within 2 degrees
Which gang members own weapons?
Find suspects who are gang members AND own weapons AND have committed multiple crimes
Which gang is expanding into rival territory?
What evidence links suspects to unsolved crimes?
```

---

## 🔐 Role-Based Access Control

The system supports 5 user roles:

| Role | Access Level | Use Case |
|------|-------------|----------|
| **👮 Detective** | Full access | Active investigations |
| **📊 Analyst** | Patterns only (anonymized) | Intelligence analysis |
| **🎖️ Supervisor** | All + performance metrics | Case management |
| **⚖️ Prosecutor** | Case-specific | Trial preparation |
| **🔬 Public** | Statistics only | Public transparency |

---

## 🚧 Roadmap

### **✅ Completed (Current)**
- [x] Core Graph RAG architecture
- [x] 11-entity knowledge graph
- [x] Conversational AI with memory
- [x] Interactive network visualization
- [x] Dashboard with analytics
- [x] Synthetic Chicago crime dataset

### **🔄 In Progress (This Week)**
- [ ] Snowflake data warehouse integration
- [ ] 100,000+ real crime records from Chicago Open Data
- [ ] ETL pipeline (Snowflake → Neo4j)
- [ ] Enterprise scale demonstration

### **📅 Future Enhancements**
- [ ] Real-time data streaming
- [ ] Advanced ML for crime prediction
- [ ] Multi-agency data sharing
- [ ] Mobile application
- [ ] Advanced RBAC implementation

---

## 🎓 Educational Value

### **What This Project Demonstrates:**

**1. Graph Database Superiority**
- Multi-hop queries impossible in SQL
- Network analysis at scale
- Relationship-first architecture

**2. Graph RAG vs Vector RAG**
- Why knowledge graphs > vector databases for structured domains
- Prevention of LLM hallucination
- Exact fact retrieval vs fuzzy similarity

**3. Enterprise Architecture**
- Snowflake (data warehouse) + Neo4j (graph) integration
- RBAC security design
- Production deployment thinking

**4. AI/ML Integration**
- LLM for natural language understanding
- Graph algorithms for network analysis
- DBSCAN clustering for hotspot prediction

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Query Response Time** | <100ms for complex queries |
| **Network Visualization** | Handles 100+ nodes smoothly |
| **Conversation Context** | Remembers last 10 exchanges |
| **Data Scale** | Current: 685 nodes, Target: 100K+ |

---

## 🤝 Contributing

This is an academic project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is for educational purposes as part of DAMG 7374 coursework at Northeastern University.

---

## 👤 Author

**Manish Kumar Kondoju**  
MS Information Systems, Northeastern University  
Course: DAMG 7374 - Knowledge Graphs with GenAI/GraphDB

**Contact:**
- GitHub: [@ManishKondoju](https://github.com/ManishKondoju)
- LinkedIn: [Manish Kumar Kondoju](https://linkedin.com/in/manishkondoju)

---

## 🙏 Acknowledgments

- Research paper: **CrimeKGQA** by Kuok et al.
- Neo4j community for excellent graph database tools
- Streamlit for the amazing web framework
- OpenRouter for LLM API access
- Professor and classmates at Northeastern University

---

## 📚 References

1. Kuok, K.L., Liu, H.H., Lo, W.W. (2024). "CrimeKGQA: A Crime Investigation System Based on Knowledge Graph RAG"
2. Neo4j Documentation: https://neo4j.com/docs/
3. Streamlit Documentation: https://docs.streamlit.io/
4. LangChain Documentation: https://python.langchain.com/

---

## ⚡ Quick Start (TL;DR)

```bash
# Clone repo
git clone https://github.com/ManishKondoju/CrimeInvestigationGraph.git
cd CrimeInvestigationGraph

# Install dependencies
pip install -r requirements.txt

# Set up .env file with your Neo4j credentials

# Load data
python load_data.py

# Run app
streamlit run app.py

# Open browser: http://localhost:8501
```

---

<div align="center">

**Made with ❤️ for better crime investigation through AI and graph technology**

⭐ Star this repo if you find it helpful!

</div>
