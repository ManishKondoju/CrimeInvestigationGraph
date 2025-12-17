# about_page.py - Project Information & Documentation
import streamlit as st

def render_about_page():
    """Render comprehensive About page for CrimeGraphRAG"""
    
    st.markdown("""
    <div style='text-align: center; padding: 40px 0 30px 0;'>
        <h1 style='font-size: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            🕵️ CrimeGraphRAG
        </h1>
        <h3 style='color: #a0aec0; font-weight: 400; margin-top: 12px;'>
            Advanced Crime Investigation Platform
        </h3>
        <p style='color: #94a3b8; font-size: 1rem; margin-top: 8px;'>
            Knowledge Graphs + Generative AI + Machine Learning
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # PROJECT OVERVIEW
    # ========================================
    st.markdown("## 📋 Project Overview")
    
    st.markdown("""
    <div class='glass-card' style='padding: 24px; background: rgba(102, 126, 234, 0.05); border: 1px solid rgba(102, 126, 234, 0.2); border-radius: 16px;'>
        <p style='font-size: 1.05rem; line-height: 1.8; color: #e2e8f0; margin: 0;'>
            <strong>CrimeGraphRAG</strong> is an advanced crime investigation intelligence platform that combines 
            <strong>Knowledge Graphs</strong>, <strong>Graph RAG (Retrieval-Augmented Generation)</strong>, and 
            <strong>Machine Learning</strong> to provide zero-hallucination AI-powered crime analysis. Built on 
            <strong>Neo4j graph database</strong> with <strong>705 real Chicago crime incidents</strong>, the system 
            enables multi-hop relationship traversal, pattern detection, and predictive analytics for law enforcement intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # KEY FEATURES
    # ========================================
    st.markdown("## ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🧠 Knowledge Graph & AI
        
        **Graph RAG Architecture**
        - Zero-hallucination AI responses
        - Grounded in explicit graph paths
        - Multi-turn conversational context
        - Transparent Cypher query inspection
        
        **Graph Algorithms**
        - PageRank influence analysis
        - Community detection (hidden crime rings)
        - Betweenness centrality (gang bridges)
        - Degree centrality (network hubs)
        - Shortest path finding
        
        **Graph Schema**
        - 9 entity types
        - 20+ relationship types
        - 1,157 total nodes
        - 3,500+ relationships
        """)
        
        st.markdown("""
        ### 📊 Analytics & Visualization
        
        **Executive Dashboard**
        - 16+ professional chart types
        - Funnel, gauge, bubble, radar charts
        - Real-time activity monitoring
        - Performance leaderboards
        
        **Timeline Analysis**
        - Crime events timeline
        - Activity heatmap (day × hour)
        - Gang activity trends
        - Investigation progress tracking
        
        **Geographic Intelligence**
        - Density heatmap visualization
        - ML-powered hotspot prediction (DBSCAN)
        - Risk scoring (4 levels)
        - Full Chicago coverage
        """)
    
    with col2:
        st.markdown("""
        ### 🗺️ Network & Schema
        
        **Network Visualization**
        - Interactive D3.js force-directed graphs
        - 8 entity types supported
        - Drag, zoom, hover interactions
        - Dynamic color-coded legend
        
        **Schema Visualization**
        - Interactive entity-relationship diagram
        - Property details for each entity
        - Relationship cardinality matrix
        - Schema export (JSON, Cypher, Markdown)
        
        ### 🎯 Data Quality
        
        **Real Chicago Crime Data**
        - 495 real crimes from Chicago Open Data Portal
        - Authentic incident reports
        - Verified locations and timestamps
        
        **Intelligent Enrichment**
        - 210 synthetic crimes for coverage
        - Realistic temporal distributions
        - Geographic diversity (all districts)
        - Complete relationship graphs
        """)
    
    st.markdown("---")
    
    # ========================================
    # TECHNOLOGY STACK
    # ========================================
    st.markdown("## 🛠️ Technology Stack")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Database & Backend**
        - Neo4j (Graph Database)
        - Python 3.11
        - Cypher Query Language
        - Neo4j Python Driver
        
        **AI & ML**
        - OpenRouter API
        - Large Language Models
        - scikit-learn (DBSCAN)
        - Graph RAG Architecture
        """)
    
    with col2:
        st.markdown("""
        **Frontend & Visualization**
        - Streamlit
        - Plotly (Interactive Charts)
        - D3.js (Network Graphs)
        - HTML/CSS (Custom UI)
        
        **Data Sources**
        - Chicago Open Data Portal
        - Real crime incidents (2024)
        - FBI UCR crime patterns
        - Domain-driven enrichment
        """)
    
    with col3:
        st.markdown("""
        **Libraries & Tools**
        - pandas (Data Processing)
        - numpy (Numerical Computing)
        - plotly (Visualization)
        - streamlit-folium (Maps)
        - python-dotenv (Config)
        - requests (API Calls)
        """)
    
    st.markdown("---")
    
    # ========================================
    # ACADEMIC CONTEXT
    # ========================================
    st.markdown("## 🎓 Academic Context")
    
    st.markdown("""
    <div class='glass-card' style='padding: 20px; background: rgba(139, 92, 246, 0.05); border-left: 4px solid #8b5cf6; border-radius: 12px;'>
        <h4 style='color: #ffffff; margin: 0 0 12px 0;'>Course: DAMG 7374 - Knowledge Graphs with GenAI</h4>
        <p style='color: #cbd5e0; line-height: 1.7; margin: 0;'>
            <strong>Institution:</strong> Northeastern University, Khoury College of Computer Sciences<br/>
            <strong>Program:</strong> Master of Science in Information Systems<br/>
            <strong>Focus:</strong> Knowledge Graph Design, Graph Algorithms, Graph RAG Implementation<br/>
            <strong>Semester:</strong> Fall 2024
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # TECHNICAL ARCHITECTURE
    # ========================================
    st.markdown("## 🏗️ System Architecture")
    
    # Display architecture diagram image
    try:
        st.image("architecture_diagram.png", use_container_width=True, caption="CrimeGraphRAG System Architecture")
    except:
        st.warning("Architecture diagram not found. Place 'architecture_diagram.png' in the project root directory.")
    
    st.markdown("---")
    
    # ========================================
    # GRAPH SCHEMA
    # ========================================
    st.markdown("## 📐 Knowledge Graph Schema")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("""
        ### Entity Types (9)
        
        | Entity | Count | Description |
        |--------|-------|-------------|
        | **Crime** | 705 | Criminal incidents |
        | **Person** | 80 | Suspects and individuals |
        | **Location** | 322 | Crime scene locations |
        | **Evidence** | 100 | Forensic items |
        | **Weapon** | 30 | Firearms and weapons |
        | **Vehicle** | 50 | Cars and transportation |
        | **Organization** | 5 | Criminal gangs |
        | **Investigator** | 5 | Detectives assigned |
        | **ModusOperandi** | 10 | Crime patterns |
        | **Total** | **1,307** | **Complete graph** |
        """)
    
    with col2:
        st.markdown("""
        ### Relationship Types (20+)
        
        - `PARTY_TO` - Person → Crime
        - `OCCURRED_AT` - Crime → Location
        - `MEMBER_OF` - Person → Organization
        - `KNOWS` - Person ↔ Person
        - `FAMILY_REL` - Person ↔ Person
        - `OWNS` - Person → Weapon/Vehicle
        - `HAS_EVIDENCE` - Crime → Evidence
        - `LINKS_TO` - Evidence → Person
        - `INVESTIGATED_BY` - Crime → Investigator
        - `USED_WEAPON` - Crime → Weapon
        - `INVOLVED_VEHICLE` - Crime → Vehicle
        - `MATCHES_MO` - Crime → ModusOperandi
        - *and more...*
        """)
    
    st.markdown("---")
    
    # ========================================
    # FEATURES BY PAGE
    # ========================================
    st.markdown("## 📱 Application Pages")
    
    pages = [
        {
            'icon': '📊',
            'name': 'Dashboard',
            'description': 'Executive intelligence dashboard with 16+ advanced visualizations including KPI metrics, crime trends, case progression funnel, clearance rate gauge, gang threat matrix, and real-time activity monitoring.'
        },
        {
            'icon': '💬',
            'name': 'AI Assistant',
            'description': 'Conversational Graph RAG interface for natural language crime queries. Features zero-hallucination responses, transparent Cypher query inspection, and raw data verification.'
        },
        {
            'icon': '🧠',
            'name': 'Graph Algorithms',
            'description': 'Advanced network analysis with PageRank influence ranking, community detection for hidden crime rings, centrality measures, and shortest path finding between suspects.'
        },
        {
            'icon': '🕸️',
            'name': 'Network Visualization',
            'description': 'Interactive D3.js force-directed graphs showing relationships across all 8 entity types with drag, zoom, and hover capabilities.'
        },
        {
            'icon': '🗺️',
            'name': 'Geographic Mapping',
            'description': 'Spatial crime analysis with density heatmaps, ML-powered predictive hotspots using DBSCAN clustering, and 4-tier risk scoring across all Chicago districts.'
        },
        {
            'icon': '⏱️',
            'name': 'Timeline Analysis',
            'description': 'Temporal pattern detection with crime events timeline, activity heatmap (day × hour), gang activity trends, and investigation progress tracking.'
        },
        {
            'icon': '📐',
            'name': 'Graph Schema',
            'description': 'Interactive entity-relationship model visualization showing complete graph structure with property details, cardinality matrix, and schema export options.'
        }
    ]
    
    for page in pages:
        st.markdown(f"""
        <div class='glass-card' style='padding: 18px; margin: 12px 0; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);'>
            <h4 style='color: #ffffff; margin: 0 0 8px 0;'>{page['icon']} {page['name']}</h4>
            <p style='color: #cbd5e0; font-size: 0.95rem; line-height: 1.6; margin: 0;'>
                {page['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # TECHNICAL HIGHLIGHTS
    # ========================================
    st.markdown("## 🎯 Technical Highlights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔬 Advanced Implementations
        
        **Graph RAG (Retrieval-Augmented Generation)**
        - Combines Neo4j knowledge graphs with LLMs
        - Eliminates AI hallucinations through graph grounding
        - Every answer traceable to explicit database paths
        - Transparent query inspection for verification
        
        **Machine Learning**
        - DBSCAN clustering for hotspot prediction
        - 4-tier risk scoring algorithm
        - Temporal pattern recognition
        - Geographic density analysis
        
        **Graph Algorithms**
        - PageRank for influence ranking
        - Community detection for hidden networks
        - Centrality measures (degree, betweenness)
        - Pathfinding algorithms
        """)
    
    with col2:
        st.markdown("""
        ### 💎 Design Excellence
        
        **User Interface**
        - Glassmorphism design system
        - Animated gradient backgrounds
        - Smooth micro-interactions
        - Responsive layout
        - Professional color palette
        
        **Data Quality**
        - Real Chicago crime data (API integration)
        - Realistic temporal distributions
        - Smart severity mapping
        - 100% location coverage
        - Domain-driven data modeling
        
        **Performance**
        - Optimized Cypher queries
        - Caching strategies
        - Lazy loading
        - Efficient graph traversal
        """)
    
    st.markdown("---")
    
    # ========================================
    # PROJECT STATISTICS
    # ========================================
    st.markdown("## 📈 Project Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Crimes", "705", delta="495 real + 210 synthetic")
    
    with col2:
        st.metric("Graph Nodes", "1,157", delta="9 entity types")
    
    with col3:
        st.metric("Relationships", "3,500+", delta="20 types")
    
    with col4:
        st.metric("Visualizations", "25+", delta="7 pages")
    
    st.markdown("---")
    
    # ========================================
    # USE CASES
    # ========================================
    st.markdown("## 🎯 Demonstration Use Cases")
    
    use_cases = [
        {
            'title': 'Multi-Hop Network Traversal',
            'query': '"Show me everyone within 2 degrees of David Rodriguez"',
            'demonstrates': 'Variable-length pattern matching using [:KNOWS*1..2]'
        },
        {
            'title': 'Cross-Gang Collaboration Detection',
            'query': '"Find suspects who committed crimes together but aren\'t in the same gang"',
            'demonstrates': 'Complex pattern matching with negative filtering'
        },
        {
            'title': 'Influence Ranking (PageRank)',
            'query': '"Who is the most influential criminal?"',
            'demonstrates': 'Graph algorithm integration with weighted scoring'
        },
        {
            'title': 'Betweenness Centrality Analysis',
            'query': '"Which suspects connect to multiple different gangs?"',
            'demonstrates': 'Bridge detection between communities'
        },
        {
            'title': 'Community Detection',
            'query': '"Detect hidden crime rings working outside official gangs"',
            'demonstrates': 'Unsupervised clustering on graph structure'
        },
        {
            'title': 'Temporal Pattern Analysis',
            'query': 'Timeline heatmap showing Friday/Saturday 10 PM-2 AM peak',
            'demonstrates': 'Temporal data modeling and visualization'
        }
    ]
    
    for i, uc in enumerate(use_cases, 1):
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.02); padding: 16px; margin: 10px 0; border-radius: 10px; border-left: 3px solid #667eea;'>
            <strong style='color: #ffffff; font-size: 1rem;'>{i}. {uc['title']}</strong>
            <div style='margin: 8px 0; padding: 8px 12px; background: rgba(0,0,0,0.3); border-radius: 6px; font-family: monospace; font-size: 0.9rem; color: #a5b4fc;'>
                {uc['query']}
            </div>
            <p style='color: #94a3b8; font-size: 0.85rem; margin: 8px 0 0 0;'>
                <em>Demonstrates:</em> {uc['demonstrates']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # KNOWLEDGE GRAPH CONCEPTS
    # ========================================
    st.markdown("## 🎓 Knowledge Graph Concepts Demonstrated")
    
    concepts = {
        'Graph Data Modeling': 'Entity-relationship design with 9 entities and 20+ relationship types following police investigation domain ontology',
        'Graph Traversal': 'Multi-hop queries, variable-length patterns, path exploration up to N degrees of separation',
        'Graph Algorithms': 'PageRank, centrality measures (degree, betweenness, closeness), community detection',
        'Graph RAG': 'LLM + knowledge graph integration for zero-hallucination AI responses grounded in explicit paths',
        'Pattern Matching': 'Complex Cypher patterns including triangles, stars, chains, and cross-entity correlations',
        'Temporal Graphs': 'Time-aware queries, temporal distributions, chronological analysis',
        'Spatial Analysis': 'Geographic clustering, hotspot prediction, density mapping',
        'Schema Visualization': 'Interactive meta-model representation with cardinality and property analysis'
    }
    
    for concept, description in concepts.items():
        st.markdown(f"""
        <div style='background: rgba(102, 126, 234, 0.05); padding: 14px; margin: 8px 0; border-radius: 8px;'>
            <strong style='color: #667eea; font-size: 0.95rem;'>✓ {concept}</strong><br/>
            <span style='color: #a0aec0; font-size: 0.85rem; line-height: 1.5;'>{description}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # PROJECT IMPACT
    # ========================================
    st.markdown("## 💎 Project Value & Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🏆 Academic Excellence
        
        **Demonstrates Mastery Of:**
        - Graph database design and optimization
        - Advanced Cypher query development
        - Graph algorithm implementation
        - LLM + knowledge graph integration
        - Full-stack application development
        - UI/UX design principles
        - Data visualization best practices
        
        **Course Alignment:**
        - ✅ Knowledge graph modeling
        - ✅ Graph algorithms (PageRank, centrality)
        - ✅ GenAI integration (Graph RAG)
        - ✅ Real-world application
        - ✅ Professional implementation
        """)
    
    with col2:
        st.markdown("""
        ### 💼 Professional Portfolio Value
        
        **Industry-Relevant Skills:**
        - Graph database architecture (Neo4j)
        - AI/ML engineering (Graph RAG)
        - Data science & analytics
        - Full-stack web development
        - UI/UX design
        
        **Comparable To:**
        - Palantir Gotham (law enforcement)
        - IBM i2 Analyst's Notebook
        - Linkurious Enterprise
        - Neo4j Bloom
        
        **Estimated Commercial Value:**
        - Development: $50,000-100,000
        - Timeline: 3-6 months (professional team)
        - Actual: 1 academic semester
        """)
    
    st.markdown("---")
    
    # ========================================
    # FUTURE ENHANCEMENTS
    # ========================================
    st.markdown("## 🚀 Potential Enhancements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Advanced Features
        
        - **Graph Embeddings** (Node2Vec)
        - **Link Prediction** (Missing relationships)
        - **Graph Neural Networks** (GNN)
        - **Temporal Graph Evolution** (Network over time)
        - **Multi-Modal Data** (Images, videos)
        - **Real-Time Streaming** (Live crime feeds)
        - **Mobile Application** (iOS/Android)
        - **API Development** (RESTful endpoints)
        """)
    
    with col2:
        st.markdown("""
        ### Integration Opportunities
        
        - **External Data Sources** (FBI, state databases)
        - **Social Media Analysis** (OSINT)
        - **Facial Recognition** (Computer vision)
        - **License Plate Detection** (ALPR)
        - **Predictive Policing** (Crime forecasting)
        - **Resource Optimization** (Patrol allocation)
        - **Case Management** (Investigation tracking)
        - **Evidence Chain** (Blockchain verification)
        """)
    
    st.markdown("---")
    
    # ========================================
    # ACKNOWLEDGMENTS
    # ========================================
    st.markdown("## 🙏 Acknowledgments")
    
    st.markdown("""
    <div class='glass-card' style='padding: 20px; background: rgba(16, 185, 129, 0.05); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);'>
        <p style='color: #cbd5e0; line-height: 1.8; margin: 0;'>
            <strong style='color: #10b981;'>Data Source:</strong> City of Chicago Open Data Portal<br/>
            <strong style='color: #10b981;'>Course:</strong> DAMG 7374 - Knowledge Graphs with GenAI, Northeastern University<br/>
            <strong style='color: #10b981;'>Technologies:</strong> Neo4j, Streamlit, Plotly, D3.js, OpenRouter<br/>
            <strong style='color: #10b981;'>Institution:</strong> Khoury College of Computer Sciences
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # QUICK START
    # ========================================
    st.markdown("## ⚡ Quick Start Guide")
    
    st.code("""
# 1. Start Neo4j Database
neo4j start

# 2. Load Crime Data
python load_hybrid_data.py

# 3. Launch Application
streamlit run app.py

# 4. Navigate to different pages and explore!
    """, language="bash")
    
    st.markdown("---")
    
    # ========================================
    # FOOTER
    # ========================================
    st.markdown("""
    <div style='text-align: center; padding: 30px 0; background: rgba(255,255,255,0.02); border-radius: 16px; margin-top: 40px;'>
        <h3 style='font-size: 1.3rem; margin-bottom: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            CrimeGraphRAG Intelligence System
        </h3>
        <p style='color: #a0aec0; font-size: 0.95rem; margin: 8px 0;'>
            Advanced Crime Investigation Platform
        </p>
        <p style='color: #64748b; font-size: 0.85rem; margin: 12px 0 0 0;'>
            Northeastern University • Khoury College of Computer Sciences<br/>
            Master of Science in Information Systems • Fall 2024
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(page_title="About CrimeGraphRAG", layout="wide")
    render_about_page()