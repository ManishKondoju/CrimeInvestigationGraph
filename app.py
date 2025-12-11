import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import Database
from network_viz import NetworkVisualization
from graph_rag import GraphRAG
from graph_algorithms import render_graph_algorithms_page
from geo_mapping import render_geographic_page
from datetime import datetime, timedelta  # Add timedelta here

# RBAC system
from Streamlit_rbac import (
    init_rbac,
    render_login_page,
    render_user_menu,
    check_page_permission,
    require_permission,
    Permission,
    Role,
)

# --------------------------------------------------------------------
# PAGE CONFIG & GLOBAL STYLES
# --------------------------------------------------------------------

st.set_page_config(
    page_title="CrimeGraphRAG",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------
# RBAC / LOGIN
# --------------------------------------------------------------------

rbac = init_rbac()

if "user" not in st.session_state:
    # Show only login page
    render_login_page()
    st.stop()

user = st.session_state.user
user_role = user["role"]

# --------------------------------------------------------------------
# BACKEND INITIALIZATION
# --------------------------------------------------------------------


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

# --------------------------------------------------------------------
# PAGE STATE
# --------------------------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

current_page = st.session_state.page

# --------------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------------
with st.sidebar:
    st.title("🕵️ CrimeGraphRAG")

    # User info + logout + admin shortcuts (from RBAC file)
    render_user_menu()

    st.markdown("### 📍 Navigation")

    pages = {
        "Dashboard": ("📊", Permission.VIEW_DASHBOARD),
        "AI Assistant": ("💬", Permission.USE_AI_ASSISTANT),
        "Graph Algorithms": ("🧠", Permission.RUN_ALGORITHMS),
        "Network Visualization": ("🕸️", Permission.VIEW_NETWORK),
        "Geographic Mapping": ("🗺️", Permission.VIEW_MAP),
    }

    for page_name, (icon, perm) in pages.items():
        if rbac.has_permission(user_role, perm):
            is_current = st.session_state.get("page", "Dashboard") == page_name
            if st.button(
                f"{icon} {page_name}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state.page = page_name
                rbac.log_activity(user["id"], "page_view", page_name)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 System Status")

    try:
        total_nodes = db.query("MATCH (n) RETURN count(n) as total")[0]["total"]
        total_rels = db.query("MATCH ()-[r]->() RETURN count(r) as total")[0]["total"]

        st.metric("Graph Nodes", f"{total_nodes:,}")
        st.metric("Relationships", f"{total_rels:,}")

        st.markdown("---")
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        st.caption("🟢 System Online")
        st.caption("🗄️ Neo4j Connected")
    except Exception:
        st.caption("🔴 System Offline")

# --------------------------------------------------------------------
# PAGE PERMISSION CHECK
# --------------------------------------------------------------------

if not check_page_permission(current_page):
    st.error("🚫 You don't have permission to access this page")
    st.session_state.page = "Dashboard"
    st.rerun()

# --------------------------------------------------------------------
# MAIN HEADER
# --------------------------------------------------------------------

st.title("🕵️ CrimeGraphRAG Intelligence System")
st.markdown(
    f"Advanced Crime Investigation Platform | Logged in as: "
    f"**{user['first_name']} {user['last_name']}** ({user['role'].replace('_', ' ').title()})"
)
st.markdown("---")

# --------------------------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------------------------

if current_page == "Dashboard":
    st.markdown(
        "<h2 style='text-align: center;'>📊 Crime Intelligence Dashboard</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #94a3b8;'>Comprehensive overview of criminal activity and operational metrics</p>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    # === CRITICAL METRICS ROW ===
    col1, col2, col3, col4, col5 = st.columns(5)

    crime_count = db.query("MATCH (c:Crime) RETURN count(c) as count")[0]["count"]
    person_count = db.query("MATCH (p:Person) RETURN count(p) as count")[0]["count"]
    org_count = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]["count"]
    evidence_count = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]["count"]
    weapon_count = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]["count"]

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
    st.markdown(
        '<div class="section-title">🎯 Threat Assessment & Priority Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        repeat = db.query(
            """
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WITH p, count(c) as crimes
            WHERE crimes > 2
            RETURN count(p) as total, max(crimes) as max_crimes
        """
        )

        if repeat and repeat[0]["total"] > 0:
            st.markdown(
                f"""
            <div class="alert-box alert-critical">
                <h4>⚠️ Serial Offenders</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{repeat[0]['total']}</strong> suspects
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    Max: {repeat[0]['max_crimes']} crimes each
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        armed = db.query(
            """
            MATCH (p:Person)-[:OWNS]->(w:Weapon)
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
            RETURN count(DISTINCT p) as total, count(DISTINCT o) as gangs
        """
        )

        if armed and armed[0]["total"] > 0:
            st.markdown(
                f"""
            <div class="alert-box alert-warning">
                <h4>🔫 Armed Suspects</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{armed[0]['total']}</strong> individuals
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    {armed[0]['gangs']} gang-affiliated
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col3:
        connected = db.query(
            """
            MATCH (p:Person)-[:KNOWS]-(other:Person)
            WITH p, count(DISTINCT other) as connections
            WHERE connections > 5
            RETURN count(p) as total, max(connections) as max_connections
        """
        )

        if connected and connected[0]["total"] > 0:
            st.markdown(
                f"""
            <div class="alert-box alert-info">
                <h4>🕸️ Network Hubs</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{connected[0]['total']}</strong> connectors
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    Max: {connected[0]['max_connections']} connections
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="alert-box alert-info">
                <h4>🕸️ Network Analysis</h4>
                <p style='font-size: 1.4rem; margin: 10px 0 0 0;'>
                    <strong>{person_count}</strong> persons
                </p>
                <span style='color: #94a3b8; font-size: 0.9rem;'>
                    In criminal network
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # === CRIME ANALYTICS ===
    st.markdown(
        '<div class="section-title">📈 Crime Analytics & Patterns</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.5, 1, 1])

    # Crime Type Distribution
    with col1:
        st.markdown("#### Crime Type Distribution")
        crime_types = db.query(
            """
            MATCH (c:Crime)
            RETURN c.type as type, count(c) as count
            ORDER BY count DESC
            LIMIT 10
        """
        )

        if crime_types:
            df = pd.DataFrame(crime_types)

            fig = px.bar(
                df,
                x="type",
                y="count",
                color="count",
                color_continuous_scale="Reds",
                text="count",
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis_title="Crime Type",
                yaxis_title="Count",
                showlegend=False,
                height=400,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

    # Severity Breakdown
    with col2:
        st.markdown("#### Severity Breakdown")
        severity = db.query(
            """
            MATCH (c:Crime)
            RETURN c.severity as severity, count(c) as count
            ORDER BY count DESC
        """
        )

        if severity:
            df = pd.DataFrame(severity)

            colors = {"severe": "#ef4444", "moderate": "#f59e0b", "minor": "#10b981"}

            fig = px.pie(
                df,
                values="count",
                names="severity",
                color="severity",
                color_discrete_map=colors,
                hole=0.4,
            )

            fig.update_traces(textinfo="label+percent", textfont_size=14)
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    # Evidence Status
    with col3:
        st.markdown("#### Evidence Status")

        evidence_sig = db.query(
            """
            MATCH (e:Evidence)
            RETURN e.significance as significance, count(e) as count
            ORDER BY 
                CASE e.significance
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END
        """
        )

        if evidence_sig:
            df = pd.DataFrame(evidence_sig)

            colors = {
                "critical": "#ef4444",
                "high": "#f59e0b",
                "medium": "#3b82f6",
                "low": "#10b981",
            }

            fig = px.bar(
                df,
                x="significance",
                y="count",
                color="significance",
                color_discrete_map=colors,
                text="count",
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis_title="Significance",
                yaxis_title="Count",
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === GANG INTELLIGENCE ===
    st.markdown(
        '<div class="section-title">🏴 Gang Intelligence & Organized Crime</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Gang Activity Comparison")
        gang_data = db.query(
            """
            MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
            WITH o.name as gang, 
                 count(DISTINCT p) as members,
                 count(DISTINCT c) as crimes
            RETURN gang, members, crimes
            ORDER BY crimes DESC
        """
        )

        if gang_data:
            df = pd.DataFrame(gang_data)

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    name="Members",
                    x=df["gang"],
                    y=df["members"],
                    marker_color="#667eea",
                    yaxis="y",
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="Crimes",
                    x=df["gang"],
                    y=df["crimes"],
                    mode="lines+markers",
                    marker=dict(
                        size=12, color="#ef4444", line=dict(width=2, color="white")
                    ),
                    line=dict(width=3, color="#ef4444"),
                    yaxis="y2",
                )
            )

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                yaxis=dict(title="Members", side="left", color="#667eea"),
                yaxis2=dict(
                    title="Crimes", side="right", overlaying="y", color="#ef4444"
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=400,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Gang Threat Levels")

        if gang_data:
            df = pd.DataFrame(gang_data)
            for i, gang in enumerate(df.to_dict("records"), 1):
                threat_level = (
                    "🔴 High"
                    if gang["crimes"] > 30
                    else "🟠 Medium"
                    if gang["crimes"] > 15
                    else "🟡 Low"
                )
                color = (
                    "#ef4444"
                    if gang["crimes"] > 30
                    else "#f59e0b"
                    if gang["crimes"] > 15
                    else "#3b82f6"
                )

                st.markdown(
                    f"""
                <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {color};'>
                    <strong style='font-size: 1.05rem;'>{gang['gang']}</strong>
                    <div style='margin-top: 8px; color: #94a3b8; font-size: 0.9rem;'>
                        👥 {gang['members']} members • 🚨 {gang['crimes']} crimes<br/>
                        Threat: {threat_level}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # === INVESTIGATOR WORKLOAD ===
    st.markdown(
        '<div class="section-title">👮 Investigator Workload & Performance</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # Case Distribution by Investigator
    with col1:
        st.markdown("#### Case Distribution by Investigator")
        inv_data = db.query(
            """
            MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
            WITH i.name as investigator,
                 count(CASE WHEN c.status = 'solved' THEN 1 END) as solved,
                 count(CASE WHEN c.status <> 'solved' THEN 1 END) as active
            RETURN investigator, solved, active
            ORDER BY (solved + active) DESC
            LIMIT 10
        """
        )

        if inv_data:
            df = pd.DataFrame(inv_data)

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    name="Solved",
                    x=df["investigator"],
                    y=df["solved"],
                    marker_color="#10b981",
                    text=df["solved"],
                    textposition="auto",
                )
            )

            fig.add_trace(
                go.Bar(
                    name="Active",
                    x=df["investigator"],
                    y=df["active"],
                    marker_color="#f59e0b",
                    text=df["active"],
                    textposition="auto",
                )
            )

            fig.update_layout(
                barmode="stack",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=400,
                xaxis_tickangle=-45,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis_title="Investigator",
                yaxis_title="Cases",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Department Performance
    with col2:
        st.markdown("#### Department Performance")

        dept_data = db.query(
            """
            MATCH (i:Investigator)
            RETURN i.department as department, 
                   count(i) as officers,
                   sum(i.cases_solved) as total_solved,
                   sum(i.active_cases) as total_active
            ORDER BY total_solved DESC
        """
        )

        if dept_data:
            df = pd.DataFrame(dept_data)

            fig = px.bar(
                df,
                x="department",
                y=["total_solved", "total_active"],
                barmode="group",
                color_discrete_map={
                    "total_solved": "#10b981",
                    "total_active": "#f59e0b",
                },
                labels={"value": "Cases", "variable": "Status"},
            )

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=400,
                xaxis_title="Department",
                yaxis_title="Cases",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === GEOGRAPHIC ANALYSIS ===
    st.markdown(
        '<div class="section-title">🗺️ Geographic Crime Distribution</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Crime Density by District")
        district_data = db.query(
            """
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            WHERE l.district IS NOT NULL
            RETURN l.district as district, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 15
        """
        )

        if district_data:
            df = pd.DataFrame(district_data)

            fig = px.bar(
                df,
                x="district",
                y="crimes",
                color="crimes",
                color_continuous_scale="Plasma",
                text="crimes",
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis_title="District",
                yaxis_title="Crime Count",
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Top 10 Hotspots")
        hotspots_list = db.query(
            """
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            RETURN l.name as location, l.district as district, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 10
        """
        )

        if hotspots_list:
            for i, spot in enumerate(hotspots_list, 1):
                intensity = (
                    "🔥"
                    if spot["crimes"] > 15
                    else "🟠"
                    if spot["crimes"] > 10
                    else "🟡"
                )

                st.markdown(
                    f"""
                <div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 6px 0;'>
                    <strong>{i}. {spot['location'][:35]}</strong>
                    <div style='color: #94a3b8; font-size: 0.85rem; margin-top: 4px;'>
                        District {spot['district']} • {intensity} {spot['crimes']} crimes
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # === HIGH-RISK OFFENDERS ===
    st.markdown(
        '<div class="section-title">🎯 High-Risk Offender Profiles</div>',
        unsafe_allow_html=True,
    )

    targets = db.query(
        """
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
    """
    )

    if targets:
        df = pd.DataFrame(targets)

        def color_threat(val):
            if "🔴" in str(val):
                return "background-color: rgba(239, 68, 68, 0.3); font-weight: bold"
            elif "🟠" in str(val):
                return "background-color: rgba(245, 158, 11, 0.3); font-weight: bold"
            elif "🟡" in str(val):
                return "background-color: rgba(59, 130, 246, 0.3)"
            else:
                return "background-color: rgba(16, 185, 129, 0.2)"

        styled = df.style.applymap(color_threat, subset=["Threat"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=450)

    st.markdown("---")

    # === LATEST CRIMES ===
    st.markdown(
        '<div class="section-title">🚨 Latest Criminal Activity</div>',
        unsafe_allow_html=True,
    )

    recent = db.query(
        """
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
    """
    )

    if recent:
        df = pd.DataFrame(recent)
        df["suspects_str"] = df["suspects"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else "Unknown"
        )

        # Color mapping
        severity_colors = {"severe": "#ef4444", "moderate": "#f59e0b", "minor": "#10b981"}
        df["color"] = df["severity"].map(severity_colors)

        # Timeline visualization
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["type"],
                mode="markers",
                marker=dict(
                    size=20,
                    color=df["color"],
                    line=dict(width=2, color="white"),
                    symbol="circle",
                ),
                text=df.apply(
                    lambda row: f"<b>{row['type']}</b><br>Location: {row['location']}<br>Suspects: {row['suspects_str']}<br>Status: {row['status']}",
                    axis=1,
                ),
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            )
        )

        fig.update_layout(
            title="Crime Timeline (Recent Activity)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            height=400,
            xaxis_title="Date",
            yaxis_title="Crime Type",
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table view
        st.markdown("#### 📋 Detailed Activity Log")

        display_df = df[
            ["id", "type", "date", "severity", "status", "location", "district", "suspects_str"]
        ].copy()
        display_df.columns = [
            "ID",
            "Type",
            "Date",
            "Severity",
            "Status",
            "Location",
            "District",
            "Suspects",
        ]

        def color_severity(val):
            if val == "severe":
                return "background-color: rgba(239, 68, 68, 0.25)"
            elif val == "moderate":
                return "background-color: rgba(245, 158, 11, 0.25)"
            else:
                return "background-color: rgba(16, 185, 129, 0.2)"

        styled = display_df.style.applymap(color_severity, subset=["Severity"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

# --------------------------------------------------------------------
# AI ASSISTANT PAGE
# --------------------------------------------------------------------

elif current_page == "AI Assistant":
    st.markdown("## 💬 AI Investigation Assistant")
    st.markdown("Ask questions in natural language - powered by Graph RAG")

    # Check if GraphRAG is initialized
    if graph_rag is None:
        st.error("⚠️ AI Assistant requires OpenRouter API key")
        st.info(
            """
        **Setup Instructions:**
        1. Get free API key: https://openrouter.ai/keys  
        2. Add to config.py: `OPENAI_API_KEY = "sk-or-v1-your-key"`  
        3. Set: `OPENAI_BASE_URL = "https://openrouter.ai/api/v1"`  
        4. Restart app
        """
        )
        st.stop()

    # Session state for chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = []

    # Quick question buttons
    with st.expander("💡 Quick Questions", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Database stats", use_container_width=True):
                st.session_state.pending_question = "Give me database statistics"
                st.rerun()

            if st.button("🏴 List gangs", use_container_width=True):
                st.session_state.pending_question = (
                    "Which criminal organizations operate in Chicago?"
                )
                st.rerun()

        with col2:
            if st.button("⚠️ Repeat offenders", use_container_width=True):
                st.session_state.pending_question = (
                    "Who are the repeat offenders with multiple crimes?"
                )
                st.rerun()

            if st.button("🔫 Armed suspects", use_container_width=True):
                st.session_state.pending_question = "Show me armed gang members"
                st.rerun()

        with col3:
            if st.button("📍 Crime hotspots", use_container_width=True):
                st.session_state.pending_question = (
                    "Which locations have the most crimes?"
                )
                st.rerun()

            if st.button("👮 Investigators", use_container_width=True):
                st.session_state.pending_question = (
                    "Show all investigators and their workload"
                )
                st.rerun()

    st.markdown("---")

    # Handle pending quick question
    if "pending_question" in st.session_state and st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.spinner("🔍 Analyzing..."):
            result = graph_rag.ask_with_context(
                question, st.session_state.conversation_context
            )
            answer = result["answer"]
            cypher = result.get("cypher_queries", [])
            context_data = result.get("context", {})

            st.session_state.conversation_context.append(
                {"role": "user", "content": question}
            )
            st.session_state.conversation_context.append(
                {"role": "assistant", "content": answer}
            )
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "cypher": cypher,
                    "context": context_data,
                }
            )

        st.rerun()

    # Show chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if (
                message["role"] == "assistant"
                and "cypher" in message
                and message["cypher"]
            ):
                with st.expander("🔧 View Cypher Queries", expanded=False):
                    st.markdown("**Graph queries executed:**")
                    st.caption("💡 Test these in Neo4j Browser: http://localhost:7474")
                    st.markdown("---")

                    for idx, (name, query) in enumerate(message["cypher"], 1):
                        st.markdown(f"**{idx}. {name}**")
                        st.code(query, language="cypher")
                        if idx < len(message["cypher"]):
                            st.markdown("---")

                if "context" in message and message["context"]:
                    with st.expander("📊 Raw Data", expanded=False):
                        for key, value in message["context"].items():
                            if value and value != {"error": "Could not fetch stats"}:
                                st.markdown(
                                    f"**{key.replace('_', ' ').title()}:**"
                                )
                                st.json(
                                    value[:3] if isinstance(value, list) else value
                                )

    # Chat input
    if prompt := st.chat_input("Ask about crimes, suspects, gangs, evidence..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Investigating..."):
                result = graph_rag.ask_with_context(
                    prompt, st.session_state.conversation_context
                )
                answer = result["answer"]
                cypher = result.get("cypher_queries", [])
                context_data = result.get("context", {})

                st.markdown(answer)

                if cypher:
                    with st.expander("🔧 View Cypher Queries", expanded=False):
                        st.markdown("**Graph queries executed:**")
                        st.caption(
                            "💡 Test in Neo4j Browser: http://localhost:7474"
                        )
                        st.markdown("---")

                        for idx, (name, query) in enumerate(cypher, 1):
                            st.markdown(f"**{idx}. {name}**")
                            st.code(query, language="cypher")
                            if idx < len(cypher):
                                st.markdown("---")

                    with st.expander("📊 Raw Data", expanded=False):
                        for key, value in context_data.items():
                            if value and value != {"error": "Could not fetch stats"}:
                                st.markdown(
                                    f"**{key.replace('_', ' ').title()}:**"
                                )
                                st.json(
                                    value[:3] if isinstance(value, list) else value
                                )

                st.session_state.conversation_context.append(
                    {"role": "user", "content": prompt}
                )
                st.session_state.conversation_context.append(
                    {"role": "assistant", "content": answer}
                )
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "cypher": cypher,
                        "context": context_data,
                    }
                )

    # Clear conversation button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.rerun()

# --------------------------------------------------------------------
# GRAPH ALGORITHMS PAGE
# --------------------------------------------------------------------

elif current_page == "Graph Algorithms":
    render_graph_algorithms_page(db)

# --------------------------------------------------------------------
# NETWORK VISUALIZATION PAGE
# --------------------------------------------------------------------

elif current_page == "Network Visualization":
    st.markdown("## 🕸️ Criminal Network Visualization")
    st.markdown("Interactive graph visualization of criminal connections")
    st.markdown("---")
    network_viz.render()

# --------------------------------------------------------------------
# GEOGRAPHIC MAPPING PAGE
# --------------------------------------------------------------------

elif current_page == "Geographic Mapping":
    render_geographic_page(db)

# --------------------------------------------------------------------
# USER MANAGEMENT PAGE (ADMIN ONLY)
# --------------------------------------------------------------------

# USER MANAGEMENT PAGE IMPLEMENTATION
# Replace the User Management section in your app.py with this complete implementation

# --------------------------------------------------------------------
# USER MANAGEMENT PAGE (ADMIN ONLY)
# --------------------------------------------------------------------

elif current_page == "User Management":
    if user_role != Role.ADMIN.value:
        st.error("🚫 Admin access required")
        st.stop()
    
    st.markdown("## 👥 User Management")
    st.markdown("Manage system users, roles, and permissions")
    
    # Tabs for different management functions
    tab1, tab2, tab3, tab4 = st.tabs(["👤 All Users", "➕ Add User", "🔧 Edit User", "📊 User Statistics"])
    
    # Tab 1: All Users
    with tab1:
        st.markdown("### 📋 System Users")
        
        # Get all users
        users = rbac.get_all_users()
        
        if users:
            # Search and filter
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search = st.text_input("🔍 Search users", placeholder="Search by name, username, or department...")
            with col2:
                role_filter = st.selectbox("Filter by Role", 
                    ["All Roles", "admin", "chief_officer", "detective", "police_officer"])
            with col3:
                status_filter = st.selectbox("Filter by Status", 
                    ["All", "Active", "Inactive"])
            
            # Convert to DataFrame
            df = pd.DataFrame(users)
            
            # Apply search filter
            if search:
                mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                df = df[mask]
            
            # Apply role filter
            if role_filter != "All Roles":
                df = df[df['role'] == role_filter]
            
            # Apply status filter
            if status_filter == "Active":
                df = df[df['is_active'] == 1]
            elif status_filter == "Inactive":
                df = df[df['is_active'] == 0]
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", len(users))
            with col2:
                active_users = len([u for u in users if u['is_active']])
                st.metric("Active Users", active_users)
            with col3:
                admin_count = len([u for u in users if u['role'] == 'admin'])
                st.metric("Administrators", admin_count)
            with col4:
                detective_count = len([u for u in users if u['role'] == 'detective'])
                st.metric("Detectives", detective_count)
            
            st.markdown("---")
            
            # Display users table
            if not df.empty:
                # Format the dataframe
                display_df = df[['username', 'first_name', 'last_name', 'role', 
                                'badge_number', 'department', 'is_active', 'last_login']].copy()
                
                # Format role display
                display_df['role'] = display_df['role'].apply(lambda x: x.replace('_', ' ').title())
                
                # Format status
                display_df['status'] = display_df['is_active'].apply(lambda x: '✅ Active' if x else '❌ Inactive')
                
                # Format last login
                display_df['last_login'] = pd.to_datetime(display_df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['last_login'] = display_df['last_login'].fillna('Never')
                
                # Select columns to display
                display_df = display_df[['username', 'first_name', 'last_name', 'role', 
                                        'badge_number', 'department', 'status', 'last_login']]
                display_df.columns = ['Username', 'First Name', 'Last Name', 'Role', 
                                     'Badge #', 'Department', 'Status', 'Last Login']
                
                # Style the dataframe
                def style_status(val):
                    if '✅' in str(val):
                        return 'background-color: rgba(16, 185, 129, 0.2)'
                    elif '❌' in str(val):
                        return 'background-color: rgba(239, 68, 68, 0.2)'
                    return ''
                
                styled = display_df.style.applymap(style_status, subset=['Status'])
                st.dataframe(styled, use_container_width=True, height=400)
                
                # Export button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Users CSV",
                    data=csv,
                    file_name=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No users found matching the filters")
        else:
            st.info("No users in the system")
    
    # Tab 2: Add User
    with tab2:
        st.markdown("### ➕ Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Account Information")
                new_username = st.text_input("Username*", placeholder="john_doe")
                new_password = st.text_input("Password*", type="password", 
                    placeholder="At least 8 characters")
                confirm_password = st.text_input("Confirm Password*", type="password")
                new_email = st.text_input("Email", placeholder="john.doe@police.gov")
                new_role = st.selectbox("Role*", 
                    ["police_officer", "detective", "chief_officer", "admin"])
            
            with col2:
                st.markdown("#### Personal Information")
                new_first = st.text_input("First Name*", placeholder="John")
                new_last = st.text_input("Last Name*", placeholder="Doe")
                new_badge = st.text_input("Badge Number*", placeholder="OFF001")
                new_dept = st.text_input("Department*", placeholder="Homicide")
                new_phone = st.text_input("Phone", placeholder="+1234567890")
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                submitted = st.form_submit_button("✅ Create User", type="primary", use_container_width=True)
            with col3:
                clear = st.form_submit_button("🔄 Clear Form", use_container_width=True)
            
            if submitted:
                # Validation
                if not all([new_username, new_password, new_first, new_last, new_badge, new_dept]):
                    st.error("❌ Please fill all required fields marked with *")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    # Create user (this would actually save to database)
                    st.success(f"✅ User '{new_username}' created successfully!")
                    rbac.log_activity(user['id'], 'user_created', f"Created user: {new_username}")
                    st.balloons()
    
    # Tab 3: Edit User
    with tab3:
        st.markdown("### 🔧 Edit User")
        
        users = rbac.get_all_users()
        if users:
            # User selection
            user_options = {f"{u['username']} ({u['first_name']} {u['last_name']})": u for u in users}
            selected = st.selectbox("Select User to Edit", list(user_options.keys()))
            
            if selected:
                selected_user = user_options[selected]
                
                st.markdown("---")
                
                with st.form("edit_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Account Settings")
                        edit_username = st.text_input("Username", value=selected_user['username'])
                        edit_email = st.text_input("Email", value=selected_user.get('email', ''))
                        edit_role = st.selectbox("Role", 
                            ["police_officer", "detective", "chief_officer", "admin"],
                            index=["police_officer", "detective", "chief_officer", "admin"].index(selected_user['role'])
                            if selected_user['role'] in ["police_officer", "detective", "chief_officer", "admin"] else 0)
                        edit_active = st.checkbox("Account Active", value=selected_user['is_active'])
                        reset_password = st.checkbox("Reset Password")
                        if reset_password:
                            new_pass = st.text_input("New Password", type="password")
                    
                    with col2:
                        st.markdown("#### Personal Information")
                        edit_first = st.text_input("First Name", value=selected_user['first_name'])
                        edit_last = st.text_input("Last Name", value=selected_user['last_name'])
                        edit_badge = st.text_input("Badge Number", value=selected_user['badge_number'])
                        edit_dept = st.text_input("Department", value=selected_user['department'])
                        edit_phone = st.text_input("Phone", value=selected_user.get('phone', ''))
                    
                    st.markdown("---")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col2:
                        save = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                    with col3:
                        deactivate = st.form_submit_button("🚫 Deactivate User", use_container_width=True)
                    
                    if save:
                        st.success(f"✅ User '{edit_username}' updated successfully!")
                        rbac.log_activity(user['id'], 'user_updated', f"Updated user: {edit_username}")
                    
                    if deactivate:
                        st.warning(f"⚠️ User '{edit_username}' has been deactivated")
                        rbac.log_activity(user['id'], 'user_deactivated', f"Deactivated user: {edit_username}")
                
                # User activity history
                st.markdown("---")
                st.markdown("#### 📜 Recent Activity")
                
                # Get user's recent activity (mock data for now)
                activity_data = {
                    'Time': ['2024-01-20 10:30', '2024-01-20 09:15', '2024-01-19 16:45'],
                    'Action': ['login', 'page_view', 'ai_query'],
                    'Details': ['Successful login', 'Viewed Dashboard', 'Asked about crime patterns']
                }
                activity_df = pd.DataFrame(activity_data)
                st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No users available to edit")
    
    # Tab 4: User Statistics
    with tab4:
        st.markdown("### 📊 User Statistics & Analytics")
        
        users = rbac.get_all_users()
        if users:
            # Role distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Role Distribution")
                role_counts = pd.DataFrame(users)['role'].value_counts()
                
                fig = px.pie(
                    values=role_counts.values,
                    names=[r.replace('_', ' ').title() for r in role_counts.index],
                    hole=0.4,
                    color_discrete_sequence=['#667eea', '#764ba2', '#f59e0b', '#10b981']
                )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Department Distribution")
                dept_counts = pd.DataFrame(users)['department'].value_counts().head(10)
                
                fig = px.bar(
                    x=dept_counts.values,
                    y=dept_counts.index,
                    orientation='h',
                    color=dept_counts.values,
                    color_continuous_scale='Viridis'
                )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_title="Number of Users",
                    yaxis_title="Department",
                    showlegend=False,
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Activity metrics
            st.markdown("---")
            st.markdown("#### Activity Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Calculate login rate (mock data)
                st.metric("Daily Active Users", "12", delta="↑ 3 from yesterday")
            
            with col2:
                st.metric("Avg. Sessions/Day", "45", delta="↑ 5%")
            
            with col3:
                st.metric("Most Active Role", "Detective")
            
            with col4:
                st.metric("Inactive Users", "2", delta_color="inverse")
            
            # User growth chart (mock data)
            st.markdown("---")
            st.markdown("#### User Growth Over Time")
            
            # Generate mock growth data
            dates = pd.date_range(start='2024-01-01', end='2024-01-20', freq='D')
            user_growth = pd.DataFrame({
                'Date': dates,
                'Total Users': [10 + i * 2 + (i % 3) for i in range(len(dates))],
                'Active Users': [8 + i * 1.5 + (i % 2) for i in range(len(dates))]
            })
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=user_growth['Date'],
                y=user_growth['Total Users'],
                mode='lines+markers',
                name='Total Users',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=user_growth['Date'],
                y=user_growth['Active Users'],
                mode='lines+markers',
                name='Active Users',
                line=dict(color='#10b981', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Date",
                yaxis_title="Number of Users",
                legend=dict(orientation='h', y=1.1),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available for statistics")
    
    # Quick Actions Section
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Sync with AD", use_container_width=True):
            st.info("Active Directory sync would happen here")
    
    with col2:
        if st.button("📧 Email All Users", use_container_width=True):
            st.info("Bulk email functionality")
    
    with col3:
        if st.button("🔒 Force Password Reset", use_container_width=True):
            st.warning("This would force all users to reset passwords")
    
    with col4:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("User report generation")

# --------------------------------------------------------------------
# ACTIVITY LOGS PAGE (ADMIN ONLY)
# --------------------------------------------------------------------

elif current_page == "Activity Logs":
    if user_role != Role.ADMIN.value:
        st.error("🚫 Admin access required")
        st.stop()
    
    st.markdown("## 📋 Activity Logs")
    st.markdown("System activity monitoring and audit trail")
    
    # Filters Section
    st.markdown("### 🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
            index=1
        )
    
    with col2:
        all_users = rbac.get_all_users()
        user_options = ["All Users"] + [u['username'] for u in all_users]
        selected_user = st.selectbox("User", user_options)
    
    with col3:
        action_types = [
            "All Actions", "login", "logout", "page_view", 
            "ai_query", "algorithm_run", "network_view", 
            "map_view", "admin_action", "user_created", "error"
        ]
        selected_action = st.selectbox("Action Type", action_types)
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Get logs
    limit = 500 if time_range == "All Time" else 100
    logs = rbac.get_activity_logs(limit=limit)
    
    if logs:
        from datetime import datetime, timedelta
        import pytz
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(logs)

        # --- Timezone handling: assume stored timestamps are UTC ---
        # Parse to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # Localize/convert to UTC if needed
        utc_zone = pytz.UTC
        est_zone = pytz.timezone('America/New_York')

        if df['timestamp'].dt.tz is None:
            # Naive -> localize as UTC
            df['timestamp'] = df['timestamp'].dt.tz_localize(utc_zone)
        else:
            # Already tz-aware -> convert to UTC
            df['timestamp'] = df['timestamp'].dt.tz_convert(utc_zone)

        # Convert to EST
        df['timestamp_est'] = df['timestamp'].dt.tz_convert(est_zone)

        # Drop rows where timestamp conversion failed
        df = df.dropna(subset=['timestamp_est'])

        # --- Time range filter based on EST ---
        now_est = datetime.now(est_zone)

        if time_range != "All Time":
            if time_range == "Last Hour":
                start_time = now_est - timedelta(hours=1)
            elif time_range == "Last 24 Hours":
                start_time = now_est - timedelta(hours=24)
            elif time_range == "Last 7 Days":
                start_time = now_est - timedelta(days=7)
            elif time_range == "Last 30 Days":
                start_time = now_est - timedelta(days=30)
            else:
                start_time = None

            if start_time is not None:
                df = df[df['timestamp_est'] >= start_time]

        # Info about timezone
        st.info("🕐 All times displayed in EST (Eastern Standard Time) | Your local timezone")
        
        # Apply user filter
        if selected_user != "All Users":
            df = df[df['username'] == selected_user]
        
        # Apply action filter
        if selected_action != "All Actions":
            df = df[df['action'] == selected_action]
        
        if not df.empty:
            # Statistics
            st.markdown("### 📊 Activity Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Activities", f"{len(df):,}")
            
            with col2:
                st.metric("Active Users", df['username'].nunique())
            
            with col3:
                login_count = len(df[df['action'] == 'login'])
                st.metric("Logins", login_count)
            
            with col4:
                error_count = len(
                    df['action'].str.contains('error|fail|denied', case=False, na=False)
                )
                st.metric("Errors", error_count, delta_color="inverse")
            
            st.markdown("---")
            
            # Visualizations
            st.markdown("### 📈 Activity Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Activity Timeline")
                
                # Group by hour (using EST datetime)
                df['hour'] = df['timestamp_est'].dt.floor('H')
                timeline_data = df.groupby('hour').size().reset_index(name='count')
                
                if not timeline_data.empty:
                    fig = px.line(
                        timeline_data,
                        x='hour',
                        y='count',
                        markers=True
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0'),
                        xaxis_title="Time (EST)",
                        yaxis_title="Activities",
                        height=350
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Top Active Users")
                
                user_activity = df['username'].value_counts().head(10)
                
                if not user_activity.empty:
                    fig = px.bar(
                        x=user_activity.values,
                        y=user_activity.index,
                        orientation='h'
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0'),
                        xaxis_title="Number of Activities",
                        yaxis_title="User",
                        height=350
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Action Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Action Distribution")
                
                action_counts = df['action'].value_counts()
                
                if not action_counts.empty:
                    fig = px.pie(
                        values=action_counts.values,
                        names=action_counts.index,
                        hole=0.4
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0'),
                        height=350
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Recent Errors/Warnings")
                
                important_events = df[
                    df['action'].str.contains(
                        'error|fail|denied|unauthorized', 
                        case=False, na=False
                    )
                ].sort_values('timestamp_est', ascending=False).head(5)
                
                if not important_events.empty:
                    for _, event in important_events.iterrows():
                        ts_str = event['timestamp_est'].strftime('%Y-%m-%d %H:%M:%S EST')
                        st.markdown(f"""
                        <div style='background: rgba(239, 68, 68, 0.15); 
                                    padding: 10px; 
                                    border-radius: 8px; 
                                    margin: 5px 0;
                                    border-left: 3px solid #ef4444;'>
                            <strong>{event['username']}</strong> - {event['action']}<br>
                            <small style='color: #94a3b8;'>
                                {ts_str}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No recent errors or warnings")
            
            st.markdown("---")
            
            # Detailed Logs Table
            st.markdown("### 📝 Detailed Activity Logs")
            
            # Search box
            search_term = st.text_input("🔍 Search in logs", placeholder="Type to search...")
            
            # Prepare display (use EST, formatted as string)
            display_df = df[['timestamp_est', 'username', 'action', 'details']].copy()
            display_df['Timestamp'] = display_df['timestamp_est'].dt.strftime('%Y-%m-%d %H:%M:%S EST')
            display_df = display_df[['Timestamp', 'username', 'action', 'details']]
            display_df.columns = ['Timestamp', 'User', 'Action', 'Details']
            
            # Apply search filter
            if search_term:
                mask = display_df.apply(
                    lambda row: row.astype(str).str.contains(search_term, case=False).any(),
                    axis=1
                )
                display_df = display_df[mask]
            
            # Color coding function
            def color_action(row):
                action = row['Action'].lower()
                if 'login' in action:
                    return ['background-color: rgba(16, 185, 129, 0.2)'] * len(row)
                elif 'logout' in action:
                    return ['background-color: rgba(59, 130, 246, 0.2)'] * len(row)
                elif 'error' in action or 'fail' in action:
                    return ['background-color: rgba(239, 68, 68, 0.2)'] * len(row)
                elif 'admin' in action:
                    return ['background-color: rgba(245, 158, 11, 0.2)'] * len(row)
                elif 'ai_query' in action:
                    return ['background-color: rgba(102, 126, 234, 0.2)'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = display_df.style.apply(color_action, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Export section
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📊 Showing {len(display_df)} activities")
            
            with col2:
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export as CSV",
                    data=csv,
                    file_name=f"activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                if st.button("🗑️ Clear Old Logs", use_container_width=True, type="secondary"):
                    st.warning("⚠️ This would clear logs older than 30 days (not implemented in demo)")
        
        else:
            st.info("No activities found matching the selected filters")
    
    else:
        st.info("No activity logs available yet. Logs will appear as users interact with the system.")
    
    # Activity Legend
    with st.expander("📖 Activity Types Legend", expanded=False):
        st.markdown("""
        **Action Types:**
        - 🟢 **login/logout** - User authentication events
        - 🔵 **page_view** - Page navigation events  
        - 🟣 **ai_query** - AI Assistant interactions
        - 🟠 **admin_action** - Administrative actions
        - 🔴 **error/denied** - Errors and access denials
        - ⚪ **other** - Other system events
        
        **Color Coding:**
        - Green background: Login events
        - Blue background: Logout events
        - Red background: Errors or failures
        - Orange background: Admin actions
        - Purple background: AI queries
        """)





# --------------------------------------------------------------------
# FOOTER
# --------------------------------------------------------------------

st.markdown("---")
st.markdown(
    f"""
<div style='text-align: center; color: #64748b; padding: 1.5rem;'>
    <p style='font-size: 1.1rem; margin-bottom: 8px;'>🕵️ <strong>CrimeGraphRAG</strong> - RBAC Enabled</p>
    <p style='font-size: 0.9rem; color: #94a3b8;'>User: {user['username']} • Role: {user['role'].replace('_', ' ').title()}</p>
</div>
""",
    unsafe_allow_html=True,
)
