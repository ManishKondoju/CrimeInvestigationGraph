# app.py - Crime Investigation System with ENHANCED MODERN UI
import streamlit as st
from database import Database
from network_viz import NetworkVisualization
from graph_rag import GraphRAG
from graph_algorithms import render_graph_algorithms_page
from geo_mapping import render_geographic_page
from timeline_viz import render_timeline_interface
from enhanced_dashboard import render_enhanced_dashboard
from schema_visualizer import render_schema_page
from about_page import render_about_page  # NEW: About page
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="CrimeGraphRAG",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ENHANCED MODERN CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Background with Animated Gradient */
    .main {
        background: linear-gradient(-45deg, #0a0e27, #1a1f3a, #2d1b4e, #1e2a47);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
        box-shadow: 0 12px 48px 0 rgba(31, 38, 135, 0.5);
    }
    
    /* Modern Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton>button:hover:before {
        left: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px 0 rgba(102, 126, 234, 0.6);
    }
    
    .stButton>button:active {
        transform: translateY(-1px);
    }
    
    /* Enhanced Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* Modern Alert Boxes */
    .alert-box {
        padding: 24px;
        border-radius: 16px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .alert-box:before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 4px;
        transition: width 0.3s ease;
    }
    
    .alert-box:hover:before {
        width: 8px;
    }
    
    .alert-critical {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
    }
    
    .alert-critical:before {
        background: #ef4444;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
    }
    
    .alert-warning:before {
        background: #f59e0b;
    }
    
    .alert-info {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .alert-info:before {
        background: #3b82f6;
    }
    
    /* Section Titles with Glow */
    .section-title {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 40px 0 24px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid transparent;
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.5) 0%, transparent 100%);
        background-position: 0 100%;
        background-repeat: no-repeat;
        background-size: 100% 2px;
        position: relative;
    }
    
    .section-title:after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
    }
    
    /* Modern Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 14, 39, 0.98) 0%, rgba(26, 31, 58, 0.98) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e2e8f0;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        text-align: left;
        justify-content: flex-start;
        padding: 0.85rem 1.2rem;
        font-size: 0.95rem;
        margin: 4px 0;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateX(4px);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    /* Data Tables */
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #a0aec0;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 600;
        color: #e2e8f0;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(102, 126, 234, 0.1);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    /* Input Fields */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stMultiSelect>div>div>div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus,
    .stMultiSelect>div>div>div:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        background: rgba(255, 255, 255, 0.08);
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px;
        margin: 8px 0;
    }
    
    /* Success/Info/Warning/Error Messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border-left-width: 4px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.5);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border-color: rgba(239, 68, 68, 0.5);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card:hover:before {
        transform: scaleX(1);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
        border: 2px solid rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2, #667eea);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Hover Effect for Stats */
    .stat-item {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stat-item:hover {
        transform: scale(1.05);
    }
    
    /* Plotly Charts Background */
    .js-plotly-plot {
        border-radius: 16px;
        overflow: hidden;
    }
    
    /* Footer Enhancement */
    footer {
        background: rgba(255, 255, 255, 0.02);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Code Blocks */
    code {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 6px;
        padding: 2px 6px;
        color: #a5b4fc;
        font-size: 0.9em;
    }
    
    pre {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize systems
@st.cache_resource
def init_db():
    return Database()

@st.cache_resource
def init_graph_rag():
    try:
        return GraphRAG()
    except Exception as e:
        st.error(f"Error initializing GraphRAG: {str(e)}")
        return None

db = init_db()
graph_rag = init_graph_rag()
network_viz = NetworkVisualization(db)

# ========================================
# SIDEBAR NAVIGATION
# ========================================
with st.sidebar:
    # Logo/Title with gradient
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='font-size: 2rem; margin: 0;'>🕵️ CrimeGraphRAG</h1>
            <p style='color: #a0aec0; font-size: 0.9rem; margin-top: 8px;'>AI-Powered Investigation Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📍 Navigation")
    
    # Navigation buttons with icons
    if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.get('page', 'Dashboard') == 'Dashboard' else "secondary"):
        st.session_state.page = 'Dashboard'
        st.rerun()
    
    if st.button("💬 AI Assistant", use_container_width=True, type="primary" if st.session_state.get('page') == 'AI Assistant' else "secondary"):
        st.session_state.page = 'AI Assistant'
        st.rerun()
    
    if st.button("🧠 Graph Algorithms", use_container_width=True, type="primary" if st.session_state.get('page') == 'Graph Algorithms' else "secondary"):
        st.session_state.page = 'Graph Algorithms'
        st.rerun()
    
    if st.button("🕸️ Network Visualization", use_container_width=True, type="primary" if st.session_state.get('page') == 'Network Visualization' else "secondary"):
        st.session_state.page = 'Network Visualization'
        st.rerun()
    
    if st.button("🗺️ Geographic Mapping", use_container_width=True, type="primary" if st.session_state.get('page') == 'Geographic Mapping' else "secondary"):
        st.session_state.page = 'Geographic Mapping'
        st.rerun()
    
    if st.button("⏱️ Timeline Analysis", use_container_width=True, type="primary" if st.session_state.get('page') == 'Timeline Analysis' else "secondary"):
        st.session_state.page = 'Timeline Analysis'
        st.rerun()
    
    if st.button("📐 Graph Schema", use_container_width=True, type="primary" if st.session_state.get('page') == 'Graph Schema' else "secondary"):
        st.session_state.page = 'Graph Schema'
        st.rerun()
    
    st.markdown("---")
    
    if st.button("ℹ️ About", use_container_width=True, type="primary" if st.session_state.get('page') == 'About' else "secondary"):
        st.session_state.page = 'About'
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📊 System Status")
    
    try:
        total_nodes = db.query("MATCH (n) RETURN count(n) as total")[0]['total']
        total_rels = db.query("MATCH ()-[r]->() RETURN count(r) as total")[0]['total']
        
        # Modern metric cards
        st.markdown(f"""
            <div class='metric-card'>
                <div style='color: #a0aec0; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>GRAPH NODES</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #667eea;'>{total_nodes:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class='metric-card' style='margin-top: 12px;'>
                <div style='color: #a0aec0; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>RELATIONSHIPS</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #764ba2;'>{total_rels:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Status badges
        st.markdown(f"""
            <div style='margin: 16px 0;'>
                <div class='status-badge status-online'>🟢 System Online</div>
            </div>
            <div style='margin: 8px 0; color: #a0aec0; font-size: 0.85rem;'>
                🕐 {datetime.now().strftime('%H:%M:%S')}<br/>
                🗄️ Neo4j Connected
            </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown("<div class='status-badge status-offline'>🔴 System Offline</div>", unsafe_allow_html=True)

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'

# Get current page
current_page = st.session_state.page

# ========================================
# MAIN HEADER with Enhanced Styling
# ========================================
st.markdown("""
    <div style='text-align: center; padding: 40px 0 20px 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 8px;'>🕵️ CrimeGraphRAG Intelligence System</h1>
        <p style='color: #a0aec0; font-size: 1.1rem;'>Advanced Crime Investigation Platform powered by Knowledge Graphs & AI</p>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# ========================================
# PAGE: DASHBOARD
# ========================================

# ========================================
# PAGE: DASHBOARD
# ========================================
if current_page == 'Dashboard':
    render_enhanced_dashboard(db)

# PAGE: AI ASSISTANT (CHAT)
# ========================================
elif current_page == 'AI Assistant':
    st.markdown("## 💬 AI Investigation Assistant")
    st.markdown("Ask questions in natural language - powered by Graph RAG")
    
    # Check if GraphRAG is initialized
    if graph_rag is None:
        st.error("⚠️ AI Assistant requires OpenRouter API key")
        st.info("""
        **Setup Instructions:**
        1. Get free API key: https://openrouter.ai/keys
        2. Add to config.py: `OPENAI_API_KEY = "sk-or-v1-your-key"`
        3. Set: `OPENAI_BASE_URL = "https://openrouter.ai/api/v1"`
        4. Restart app
        """)
        st.stop()
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'conversation_context' not in st.session_state:
        st.session_state.conversation_context = []
    
    # Quick Questions
    with st.expander("💡 Quick Questions", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Database stats", use_container_width=True):
                st.session_state.pending_question = "Give me database statistics"
                st.rerun()
            
            if st.button("🏴 List gangs", use_container_width=True):
                st.session_state.pending_question = "Which criminal organizations operate in Chicago?"
                st.rerun()
        
        with col2:
            if st.button("⚠️ Repeat offenders", use_container_width=True):
                st.session_state.pending_question = "Who are the repeat offenders with multiple crimes?"
                st.rerun()
            
            if st.button("🔫 Armed suspects", use_container_width=True):
                st.session_state.pending_question = "Show me armed gang members"
                st.rerun()
        
        with col3:
            if st.button("📍 Crime hotspots", use_container_width=True):
                st.session_state.pending_question = "Which locations have the most crimes?"
                st.rerun()
            
            if st.button("👮 Investigators", use_container_width=True):
                st.session_state.pending_question = "Show all investigators and their workload"
                st.rerun()
    
    st.markdown("---")
    
    # Handle pending question
    if 'pending_question' in st.session_state and st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        
        st.session_state.chat_history.append({"role": "user", "content": question})
        
        with st.spinner("🔍 Analyzing..."):
            result = graph_rag.ask_with_context(question, st.session_state.conversation_context)
            answer = result['answer']
            cypher = result.get('cypher_queries', [])
            context_data = result.get('context', {})
            
            st.session_state.conversation_context.append({"role": "user", "content": question})
            st.session_state.conversation_context.append({"role": "assistant", "content": answer})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "cypher": cypher,
                "context": context_data
            })
        
        st.rerun()
    
    # Display chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Cypher queries dropdown
            if message["role"] == "assistant" and "cypher" in message and message["cypher"]:
                with st.expander("🔧 View Cypher Queries", expanded=False):
                    st.markdown("**Graph queries executed:**")
                    st.caption("💡 Test these in Neo4j Browser: http://localhost:7474")
                    st.markdown("---")
                    
                    for idx, (name, query) in enumerate(message["cypher"], 1):
                        st.markdown(f"**{idx}. {name}**")
                        st.code(query, language="cypher")
                        if idx < len(message["cypher"]):
                            st.markdown("---")
                    
                    # Raw data
                    if "context" in message and message["context"]:
                        with st.expander("📊 Raw Data", expanded=False):
                            for key, value in message["context"].items():
                                if value and value != {'error': 'Could not fetch stats'}:
                                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                                    st.json(value[:3] if isinstance(value, list) else value)
    
    # Chat input
    if prompt := st.chat_input("Ask about crimes, suspects, gangs, evidence..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Investigating..."):
                result = graph_rag.ask_with_context(prompt, st.session_state.conversation_context)
                answer = result['answer']
                cypher = result.get('cypher_queries', [])
                context_data = result.get('context', {})
                
                st.markdown(answer)
                
                if cypher:
                    with st.expander("🔧 View Cypher Queries", expanded=False):
                        st.markdown("**Graph queries executed:**")
                        st.caption("💡 Test in Neo4j Browser: http://localhost:7474")
                        st.markdown("---")
                        
                        for idx, (name, query) in enumerate(cypher, 1):
                            st.markdown(f"**{idx}. {name}**")
                            st.code(query, language="cypher")
                            if idx < len(cypher):
                                st.markdown("---")
                        
                        with st.expander("📊 Raw Data", expanded=False):
                            for key, value in context_data.items():
                                if value and value != {'error': 'Could not fetch stats'}:
                                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                                    st.json(value[:3] if isinstance(value, list) else value)
                
                st.session_state.conversation_context.append({"role": "user", "content": prompt})
                st.session_state.conversation_context.append({"role": "assistant", "content": answer})
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "cypher": cypher,
                    "context": context_data
                })
    
    # Controls
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.rerun()

# ========================================
# PAGE: GRAPH ALGORITHMS
# ========================================
elif current_page == 'Graph Algorithms':
    render_graph_algorithms_page(db)

# ========================================
# PAGE: NETWORK VISUALIZATION
# ========================================
elif current_page == 'Network Visualization':
    st.markdown("## 🕸️ Criminal Network Visualization")
    st.markdown("Interactive graph visualization of criminal connections")
    st.markdown("---")
    network_viz.render()

# ========================================
# PAGE: GEOGRAPHIC MAPPING
# ========================================
elif current_page == 'Geographic Mapping':
    render_geographic_page(db)

# ========================================
# PAGE: TIMELINE ANALYSIS
# ========================================
elif current_page == 'Timeline Analysis':
    render_timeline_interface(db)

# ========================================
# PAGE: GRAPH SCHEMA
# ========================================
elif current_page == 'Graph Schema':
    render_schema_page(db)

# ========================================
# PAGE: ABOUT
# ========================================
elif current_page == 'About':
    render_about_page()

# ========================================
# DEFAULT PAGE
# ========================================
else:
    st.session_state.page = 'Dashboard'
    st.rerun()

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: rgba(255, 255, 255, 0.02); border-radius: 16px; margin-top: 40px;'>
    <h3 style='font-size: 1.3rem; margin-bottom: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        🕵️ CrimeGraphRAG Intelligence System
    </h3>
    <p style='color: #a0aec0; font-size: 0.95rem; margin: 8px 0;'>
        Neo4j Knowledge Graphs • OpenRouter AI • Real Chicago Crime Data
    </p>
    <p style='color: #718096; font-size: 0.85rem; margin-top: 12px;'>
        DAMG 7374 - Knowledge Graphs with GenAI | Northeastern University
    </p>
</div>
""", unsafe_allow_html=True)