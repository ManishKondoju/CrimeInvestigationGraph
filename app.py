# app.py - Crime Investigation System
import streamlit as st
from database import Database
from graph_rag import GraphRAG
from network_viz import NetworkVisualization
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="CrimeGraphRAG",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover { background-color: #2563eb; }
    h1, h2, h3 { color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# Initialize systems
@st.cache_resource
def init_db():
    return Database()

@st.cache_resource
def init_graph_rag():
    return GraphRAG()

db = init_db()
graph_rag = init_graph_rag()
network_viz = NetworkVisualization(db)

# Sidebar
with st.sidebar:
    st.title("🕵️ CrimeGraphRAG")
    st.markdown("---")
    
    page = st.selectbox(
        "Navigation",
        ["🏠 Dashboard", "💬 Chat Investigation", "🕸️ Network Visualization", "🔮 Future Features"]
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.caption("**Database:** Neo4j")
    st.caption("**Model:** Gemini 2.0 Flash")
    
    # Database stats
    try:
        total_nodes = db.query("MATCH (n) RETURN count(n) as total")[0]['total']
        total_rels = db.query("MATCH ()-[r]->() RETURN count(r) as total")[0]['total']
        
        st.markdown("---")
        st.caption(f"📊 **Nodes:** {total_nodes:,}")
        st.caption(f"🔗 **Relationships:** {total_rels:,}")
    except:
        pass

# Main content
if page == "🏠 Dashboard":
    st.title("🏠 Crime Investigation Dashboard")
    st.markdown("Comprehensive overview of crime intelligence and network analysis")
    st.markdown("---")
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        crime_count = db.query("MATCH (c:Crime) RETURN count(c) as count")[0]['count']
        delta_crimes = "+12"
        st.metric("Total Crimes", f"{crime_count:,}", delta_crimes)
    
    with col2:
        org_count = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]['count']
        st.metric("Criminal Organizations", org_count, "Active")
    
    with col3:
        person_count = db.query("MATCH (p:Person) RETURN count(p) as count")[0]['count']
        st.metric("Persons of Interest", person_count)
    
    with col4:
        solved = db.query("MATCH (c:Crime {status: 'solved'}) RETURN count(c) as count")[0]['count']
        solve_rate = (solved / crime_count * 100) if crime_count > 0 else 0
        st.metric("Case Clearance Rate", f"{solve_rate:.1f}%")
    
    st.markdown("---")
    
    # Second row - More detailed metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        evidence_count = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]['count']
        st.metric("Evidence Items", evidence_count)
    
    with col2:
        weapon_count = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]['count']
        st.metric("Weapons Tracked", weapon_count)
    
    with col3:
        vehicle_count = db.query("MATCH (v:Vehicle) RETURN count(v) as count")[0]['count']
        st.metric("Vehicles", vehicle_count)
    
    with col4:
        inv_count = db.query("MATCH (i:Investigator) RETURN count(i) as count")[0]['count']
        st.metric("Active Investigators", inv_count)
    
    st.markdown("---")
    
    # Main dashboard content - 3 columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔥 Top Crime Hotspots")
        hotspots = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            RETURN l.name as location, l.district as district, count(c) as crime_count
            ORDER BY crime_count DESC
            LIMIT 8
        """)
        
        if hotspots:
            for i, spot in enumerate(hotspots, 1):
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{i}. {spot['location'][:30]}**")
                        st.caption(f"District {spot['district']}")
                    with col_b:
                        st.metric("", spot['crime_count'])
    
    with col2:
        st.markdown("### 🏴 Gang Activity")
        gang_activity = db.query("""
            MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
            WITH o, count(DISTINCT c) as crimes, count(DISTINCT p) as members
            RETURN o.name as gang, crimes, members
            ORDER BY crimes DESC
        """)
        
        if gang_activity:
            for gang in gang_activity:
                with st.container():
                    st.markdown(f"**{gang['gang']}**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"👥 {gang['members']} members")
                    with col_b:
                        st.caption(f"🚨 {gang['crimes']} crimes")
                    st.markdown("---")
    
    with col3:
        st.markdown("### 👮 Top Investigators")
        investigators = db.query("""
            MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
            WITH i, count(c) as active_cases
            RETURN i.name as name, i.department as dept, active_cases
            ORDER BY active_cases DESC
            LIMIT 5
        """)
        
        if investigators:
            for inv in investigators:
                with st.container():
                    st.markdown(f"**{inv['name']}**")
                    st.caption(f"{inv['dept']} • {inv['active_cases']} active cases")
                    st.markdown("---")
    
    st.markdown("---")
    
    # Bottom row - Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Crime Distribution by Type")
        crime_types = db.query("""
            MATCH (c:Crime)
            RETURN c.type as crime_type, count(c) as count
            ORDER BY count DESC
            LIMIT 8
        """)
        
        if crime_types:
            fig = px.pie(crime_types, values='count', names='crime_type',
                        color_discrete_sequence=px.colors.sequential.Plasma,
                        hole=0.4)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e2e8f0'), height=350, showlegend=True)
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### 📈 Crime Severity Breakdown")
        severity = db.query("""
            MATCH (c:Crime)
            RETURN c.severity as severity, count(c) as count
            ORDER BY count DESC
        """)
        
        if severity:
            fig = px.bar(severity, x='severity', y='count',
                        color='severity',
                        color_discrete_map={'severe': '#dc2626', 'moderate': '#f59e0b', 'minor': '#10b981'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#e2e8f0'), height=350, showlegend=False)
            st.plotly_chart(fig, width='stretch')
    
    # Recent activity table
    st.markdown("---")
    st.markdown("### 🕐 Recent Criminal Activity")
    
    recent = db.query("""
        MATCH (c:Crime)
        OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
        RETURN c.type as Type, c.date as Date, c.severity as Severity, 
               c.status as Status, l.name as Location
        ORDER BY c.date DESC
        LIMIT 15
    """)
    
    if recent:
        st.dataframe(recent, width='stretch', hide_index=True)

elif page == "💬 Chat Investigation":
    st.title("💬 Crime Investigation Chat")
    st.markdown("Ask questions in natural language")
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'conversation_context' not in st.session_state:
        st.session_state.conversation_context = []
    
    # Example questions
    with st.expander("💡 Example Questions"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("How many crimes?"):
                st.session_state.pending_question = "How many crimes are in the database?"
                st.rerun()
            if st.button("List organizations"):
                st.session_state.pending_question = "List all criminal organizations"
                st.rerun()
            if st.button("Show investigators"):
                st.session_state.pending_question = "Show all investigators"
                st.rerun()
        with col2:
            if st.button("Common crime types"):
                st.session_state.pending_question = "What types of crimes are most common?"
                st.rerun()
            if st.button("Crime hotspots"):
                st.session_state.pending_question = "Which locations have the most crimes?"
                st.rerun()
            if st.button("Database stats"):
                st.session_state.pending_question = "Give me database statistics"
                st.rerun()
    
    # Handle pending question
    if 'pending_question' in st.session_state and st.session_state.pending_question:
        pending_q = st.session_state.pending_question
        st.session_state.pending_question = None
        
        st.session_state.chat_history.append({"role": "user", "content": pending_q})
        result = graph_rag.ask_with_context(pending_q, st.session_state.conversation_context)
        response = result['answer']
        
        st.session_state.conversation_context.append({"role": "user", "content": pending_q})
        st.session_state.conversation_context.append({"role": "assistant", "content": response})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Display chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    user_question = st.chat_input("Ask about crime data...")
    
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        with st.chat_message("user"):
            st.markdown(user_question)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                result = graph_rag.ask_with_context(user_question, st.session_state.conversation_context)
                response = result['answer']
                st.markdown(response)
                
                st.session_state.conversation_context.append({"role": "user", "content": user_question})
                st.session_state.conversation_context.append({"role": "assistant", "content": response})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Controls
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ Clear"):
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.rerun()

elif page == "🕸️ Network Visualization":
    st.title("🕸️ Network Graph")
    st.markdown("---")
    network_viz.render()

elif page == "🔮 Future Features":
    st.title("🔮 Planned Features for Final Project")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🧠 Graph Intelligence")
        st.markdown("""
        - **PageRank Analysis** - Identify key criminals
        - **Community Detection** - Find hidden crime rings
        - **Centrality Measures** - Key network connectors
        - **Shortest Path** - Connection analysis
        """)
        
        st.markdown("### 📸 Photo Recognition")
        st.markdown("""
        - Upload suspect photos
        - Face matching
        - Instant profile retrieval
        - Complete criminal history
        """)
        
        st.markdown("### 🗺️ Geographic Mapping")
        st.markdown("""
        - Interactive Chicago map
        - Crime heatmaps
        - Gang territory mapping
        - Geospatial analysis
        """)
    
    with col2:
        st.markdown("### 📅 Temporal Analysis")
        st.markdown("""
        - Timeline visualization
        - Animated patterns
        - Predictive forecasting
        - Time-of-day analysis
        """)
        
        st.markdown("### 🤖 Smart Matching")
        st.markdown("""
        - Auto-assign suspects
        - Pattern-based matching
        - Confidence scoring
        - Real-time integration
        """)
        
        st.markdown("### 🔮 Predictive Analytics")
        st.markdown("""
        - Hotspot prediction
        - Recidivism scoring
        - Crime series detection
        - What-if analysis
        """)
    
    st.markdown("---")
    st.info("📚 **Building on:** CrimeKGQA research paper with extensions for conversational AI and production deployment")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p>🕵️ CrimeGraphRAG - Neo4j & Gemini 2.0 Flash</p>
    <p style='font-size: 0.8rem;'>DAMG 7374 - Knowledge Graphs | Northeastern University</p>
</div>
""", unsafe_allow_html=True)