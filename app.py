# app.py - Crime Investigation System
import streamlit as st
from database import Database
from network_viz import NetworkVisualization
from graph_rag import GraphRAG
from graph_algorithms import render_graph_algorithms_page
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="CrimeGraphRAG",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"  # Keep sidebar open
)

# Professional CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { 
        background: linear-gradient(135deg, #0f1419 0%, #1a1f3a 50%, #0a0e27 100%);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton>button:hover { 
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    h1, h2, h3 { color: #ffffff; }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .alert-box {
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 4px solid;
    }
    
    .alert-critical {
        background: rgba(239, 68, 68, 0.15);
        border-color: #ef4444;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.15);
        border-color: #f59e0b;
    }
    
    .alert-info {
        background: rgba(59, 130, 246, 0.15);
        border-color: #3b82f6;
    }
    
    .section-title {
        color: #667eea;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 14, 39, 0.95) 0%, rgba(26, 31, 58, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e2e8f0;
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
    st.title("🕵️ CrimeGraphRAG")
    st.markdown("---")
    
    st.markdown("### 📍 Navigation")
    
    # Navigation buttons
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
    
    st.markdown("---")
    
    st.markdown("### 📊 System Status")
    
    try:
        total_nodes = db.query("MATCH (n) RETURN count(n) as total")[0]['total']
        total_rels = db.query("MATCH ()-[r]->() RETURN count(r) as total")[0]['total']
        
        st.metric("Graph Nodes", f"{total_nodes:,}")
        st.metric("Relationships", f"{total_rels:,}")
        
        st.markdown("---")
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        st.caption("🟢 System Online")
        st.caption("🗄️ Neo4j Connected")
    except:
        st.caption("🔴 System Offline")

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'

# Get current page
current_page = st.session_state.page

# ========================================
# MAIN HEADER
# ========================================
st.title("🕵️ CrimeGraphRAG Intelligence System")
st.markdown("Advanced Crime Investigation Platform powered by Knowledge Graphs & AI")
st.markdown("---")

# ========================================
# PAGE: DASHBOARD
# ========================================
if current_page == 'Dashboard':
    st.markdown("<h2 style='text-align: center;'>📊 Crime Intelligence Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Comprehensive overview of criminal activity and operational metrics</p>", unsafe_allow_html=True)
    st.markdown("")
    
    # === CRITICAL METRICS ROW ===
    col1, col2, col3, col4, col5 = st.columns(5)
    
    crime_count = db.query("MATCH (c:Crime) RETURN count(c) as count")[0]['count']
    person_count = db.query("MATCH (p:Person) RETURN count(p) as count")[0]['count']
    org_count = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]['count']
    evidence_count = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]['count']
    weapon_count = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]['count']
    
    with col1:
        st.metric("🚨 Total Crimes", f"{crime_count:,}", delta="Real Chicago Data")
    
    with col2:
        st.metric("👤 Suspects", person_count, delta=f"{person_count} tracked")
    
    with col3:
        st.metric("🏴 Gangs", org_count, delta="Active")
    
    with col4:
        st.metric("📦 Evidence", evidence_count, delta="Catalogued")
    
    with col5:
        st.metric("🔫 Weapons", weapon_count, delta="Registered")
    
    st.markdown("---")
    
    # === THREAT ASSESSMENT ===
    st.markdown('<div class="section-title">🎯 Threat Assessment & Priority Intelligence</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        repeat = db.query("""
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WITH p, count(c) as crimes
            WHERE crimes > 2
            RETURN count(p) as total, max(crimes) as max_crimes
        """)
        
        if repeat and repeat[0]['total'] > 0:
            st.markdown(f"""
            <div class="alert-box alert-critical">
                <h4>⚠️ Serial Offenders</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{repeat[0]['total']}</strong> suspects
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    Max: {repeat[0]['max_crimes']} crimes each
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        armed = db.query("""
            MATCH (p:Person)-[:OWNS]->(w:Weapon)
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
            RETURN count(DISTINCT p) as total, count(DISTINCT o) as gangs
        """)
        
        if armed and armed[0]['total'] > 0:
            st.markdown(f"""
            <div class="alert-box alert-warning">
                <h4>🔫 Armed Suspects</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{armed[0]['total']}</strong> individuals
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    {armed[0]['gangs']} gang-affiliated
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Network connectivity - who has most connections
        connected = db.query("""
            MATCH (p:Person)-[:KNOWS]-(other:Person)
            WITH p, count(DISTINCT other) as connections
            WHERE connections > 5
            RETURN count(p) as total, max(connections) as max_connections
        """)
        
        if connected and connected[0]['total'] > 0:
            st.markdown(f"""
            <div class="alert-box alert-info">
                <h4>🕸️ Network Hubs</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{connected[0]['total']}</strong> connectors
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    Max: {connected[0]['max_connections']} connections
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-box alert-info">
                <h4>🕸️ Network Analysis</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{person_count}</strong> persons
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    In criminal network
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === CRIME ANALYTICS ===
    st.markdown('<div class="section-title">📈 Crime Analytics & Patterns</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 1, 1])
    
    with col1:
        st.markdown("#### Crime Type Distribution")
        crime_types = db.query("""
            MATCH (c:Crime)
            RETURN c.type as type, count(c) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        if crime_types:
            df = pd.DataFrame(crime_types)
            
            fig = px.bar(
                df, 
                x='type', 
                y='count',
                color='count',
                color_continuous_scale='Reds',
                text='count'
            )
            
            fig.update_traces(textposition='outside')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Crime Type",
                yaxis_title="Count",
                showlegend=False,
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Severity Breakdown")
        severity = db.query("""
            MATCH (c:Crime)
            RETURN c.severity as severity, count(c) as count
            ORDER BY count DESC
        """)
        
        if severity:
            df = pd.DataFrame(severity)
            
            colors = {'severe': '#ef4444', 'moderate': '#f59e0b', 'minor': '#10b981'}
            
            fig = px.pie(
                df,
                values='count',
                names='severity',
                color='severity',
                color_discrete_map=colors,
                hole=0.4
            )
            
            fig.update_traces(textinfo='label+percent', textfont_size=14)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown("#### Evidence Status")
        
        evidence_sig = db.query("""
            MATCH (e:Evidence)
            RETURN e.significance as significance, count(e) as count
            ORDER BY 
                CASE e.significance
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END
        """)
        
        if evidence_sig:
            df = pd.DataFrame(evidence_sig)
            
            colors = {'critical': '#ef4444', 'high': '#f59e0b', 'medium': '#3b82f6', 'low': '#10b981'}
            
            fig = px.bar(
                df,
                x='significance',
                y='count',
                color='significance',
                color_discrete_map=colors,
                text='count'
            )
            
            fig.update_traces(textposition='outside')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Significance",
                yaxis_title="Count",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === GANG INTELLIGENCE ===
    st.markdown('<div class="section-title">🏴 Gang Intelligence & Organized Crime</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Gang Activity Comparison")
        gang_data = db.query("""
            MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
            WITH o.name as gang, 
                 count(DISTINCT p) as members,
                 count(DISTINCT c) as crimes
            RETURN gang, members, crimes
            ORDER BY crimes DESC
        """)
        
        if gang_data:
            df = pd.DataFrame(gang_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Members',
                x=df['gang'],
                y=df['members'],
                marker_color='#667eea',
                yaxis='y'
            ))
            
            fig.add_trace(go.Scatter(
                name='Crimes',
                x=df['gang'],
                y=df['crimes'],
                mode='lines+markers',
                marker=dict(size=12, color='#ef4444', line=dict(width=2, color='white')),
                line=dict(width=3, color='#ef4444'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                yaxis=dict(title='Members', side='left', color='#667eea'),
                yaxis2=dict(title='Crimes', side='right', overlaying='y', color='#ef4444'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Gang Threat Levels")
        
        if gang_data:
            for i, gang in enumerate(df.to_dict('records'), 1):
                threat_level = '🔴 High' if gang['crimes'] > 30 else '🟠 Medium' if gang['crimes'] > 15 else '🟡 Low'
                color = '#ef4444' if gang['crimes'] > 30 else '#f59e0b' if gang['crimes'] > 15 else '#3b82f6'
                
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {color};'>
                    <strong style='font-size: 1.05rem;'>{gang['gang']}</strong>
                    <div style='margin-top: 8px; color: #94a3b8; font-size: 0.9rem;'>
                        👥 {gang['members']} members • 🚨 {gang['crimes']} crimes<br/>
                        Threat: {threat_level}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === INVESTIGATOR WORKLOAD ===
    st.markdown('<div class="section-title">👮 Investigator Workload & Performance</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Case Distribution by Investigator")
        inv_data = db.query("""
            MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
            WITH i.name as investigator,
                 count(CASE WHEN c.status = 'solved' THEN 1 END) as solved,
                 count(CASE WHEN c.status <> 'solved' THEN 1 END) as active
            RETURN investigator, solved, active
            ORDER BY (solved + active) DESC
            LIMIT 10
        """)
        
        if inv_data:
            df = pd.DataFrame(inv_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Solved',
                x=df['investigator'],
                y=df['solved'],
                marker_color='#10b981',
                text=df['solved'],
                textposition='auto'
            ))
            
            fig.add_trace(go.Bar(
                name='Active',
                x=df['investigator'],
                y=df['active'],
                marker_color='#f59e0b',
                text=df['active'],
                textposition='auto'
            ))
            
            fig.update_layout(
                barmode='stack',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                height=400,
                xaxis_tickangle=-45,
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                xaxis_title="Investigator",
                yaxis_title="Cases"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Department Performance")
        
        dept_data = db.query("""
            MATCH (i:Investigator)
            RETURN i.department as department, 
                   count(i) as officers,
                   sum(i.cases_solved) as total_solved,
                   sum(i.active_cases) as total_active
            ORDER BY total_solved DESC
        """)
        
        if dept_data:
            df = pd.DataFrame(dept_data)
            
            fig = px.bar(
                df,
                x='department',
                y=['total_solved', 'total_active'],
                barmode='group',
                color_discrete_map={'total_solved': '#10b981', 'total_active': '#f59e0b'},
                labels={'value': 'Cases', 'variable': 'Status'}
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                height=400,
                xaxis_title="Department",
                yaxis_title="Cases"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === GEOGRAPHIC ANALYSIS ===
    st.markdown('<div class="section-title">🗺️ Geographic Crime Distribution</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Crime Density by District")
        district_data = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            WHERE l.district IS NOT NULL
            RETURN l.district as district, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 15
        """)
        
        if district_data:
            df = pd.DataFrame(district_data)
            
            fig = px.bar(
                df,
                x='district',
                y='crimes',
                color='crimes',
                color_continuous_scale='Plasma',
                text='crimes'
            )
            
            fig.update_traces(textposition='outside')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="District",
                yaxis_title="Crime Count",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Top 10 Hotspots")
        hotspots_list = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            RETURN l.name as location, l.district as district, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 10
        """)
        
        if hotspots_list:
            for i, spot in enumerate(hotspots_list, 1):
                intensity = '🔥' if spot['crimes'] > 15 else '🟠' if spot['crimes'] > 10 else '🟡'
                
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 6px 0;'>
                    <strong>{i}. {spot['location'][:35]}</strong>
                    <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 4px;'>
                        District {spot['district']} • {intensity} {spot['crimes']} crimes
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === HIGH-RISK OFFENDERS ===
    st.markdown('<div class="section-title">🎯 High-Risk Offender Profiles</div>', unsafe_allow_html=True)
    
    targets = db.query("""
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, count(c) as crimes
        WHERE crimes > 1
        OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
        RETURN p.name as Name,
               p.age as Age,
               crimes as Crimes,
               count(DISTINCT w) as Weapons,
               COALESCE(o.name, 'Independent') as Gang,
               CASE 
                   WHEN crimes > 4 AND count(w) > 0 THEN '🔴 Critical'
                   WHEN crimes > 3 THEN '🟠 High'
                   WHEN crimes > 1 THEN '🟡 Medium'
                   ELSE '🟢 Low'
               END as Threat
        ORDER BY crimes DESC, Weapons DESC
        LIMIT 20
    """)
    
    if targets:
        df = pd.DataFrame(targets)
        
        def color_threat(val):
            if '🔴' in str(val):
                return 'background-color: rgba(239, 68, 68, 0.3); font-weight: bold'
            elif '🟠' in str(val):
                return 'background-color: rgba(245, 158, 11, 0.3); font-weight: bold'
            elif '🟡' in str(val):
                return 'background-color: rgba(59, 130, 246, 0.3)'
            else:
                return 'background-color: rgba(16, 185, 129, 0.2)'
        
        styled = df.style.applymap(color_threat, subset=['Threat'])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=450)
    
    st.markdown("---")
    
    # === LATEST CRIMES ===
    st.markdown('<div class="section-title">🚨 Latest Criminal Activity</div>', unsafe_allow_html=True)
    
    recent = db.query("""
        MATCH (c:Crime)
        OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
        OPTIONAL MATCH (p:Person)-[:PARTY_TO]->(c)
        RETURN c.id as id,
               c.type as type,
               c.date as date,
               c.severity as severity,
               c.status as status,
               COALESCE(l.name, 'Unknown') as location,
               COALESCE(l.district, 'N/A') as district,
               COALESCE(collect(DISTINCT p.name)[0..2], ['Unknown']) as suspects
        ORDER BY c.date DESC
        LIMIT 15
    """)
    
    if recent:
        df = pd.DataFrame(recent)
        df['suspects_str'] = df['suspects'].apply(lambda x: ', '.join(x) if isinstance(x, list) else 'Unknown')
        
        # Create timeline visualization
        fig = go.Figure()
        
        # Color mapping
        severity_colors = {'severe': '#ef4444', 'moderate': '#f59e0b', 'minor': '#10b981'}
        df['color'] = df['severity'].map(severity_colors)
        
        # Create scatter plot for timeline
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['type'],
            mode='markers',
            marker=dict(
                size=20,
                color=df['color'],
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            text=df.apply(lambda row: f"<b>{row['type']}</b><br>Location: {row['location']}<br>Suspects: {row['suspects_str']}<br>Status: {row['status']}", axis=1),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        
        fig.update_layout(
            title='Crime Timeline (Recent Activity)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            height=400,
            xaxis_title="Date",
            yaxis_title="Crime Type",
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Table view
        st.markdown("#### 📋 Detailed Activity Log")
        
        display_df = df[['id', 'type', 'date', 'severity', 'status', 'location', 'district', 'suspects_str']].copy()
        display_df.columns = ['ID', 'Type', 'Date', 'Severity', 'Status', 'Location', 'District', 'Suspects']
        
        def color_severity(val):
            if val == 'severe':
                return 'background-color: rgba(239, 68, 68, 0.25)'
            elif val == 'moderate':
                return 'background-color: rgba(245, 158, 11, 0.25)'
            else:
                return 'background-color: rgba(16, 185, 129, 0.2)'
        
        styled = display_df.style.applymap(color_severity, subset=['Severity'])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

# ========================================
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
# DEFAULT PAGE
# ========================================
else:
    st.session_state.page = 'Dashboard'
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1.5rem;'>
    <p style='font-size: 1.1rem; margin-bottom: 8px;'>🕵️ <strong>CrimeGraphRAG</strong> - Advanced Crime Investigation Platform</p>
    <p style='font-size: 0.9rem; color: #94a3b8;'>Neo4j Knowledge Graphs • OpenRouter AI • Real Chicago Crime Data</p>
    <p style='font-size: 0.8rem; margin-top: 12px;'>DAMG 7374 - Knowledge Graphs with GenAI | Northeastern University</p>
</div>
""", unsafe_allow_html=True)