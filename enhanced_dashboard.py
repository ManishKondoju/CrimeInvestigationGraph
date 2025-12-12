# enhanced_dashboard_v2.py - Ultra-Modern Executive Dashboard
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def render_enhanced_dashboard(db):
    """Render ultra-modern executive dashboard with advanced features"""
    
    # Enhanced CSS for ultra-modern look
    st.markdown("""
    <style>
    /* Animated gradient cards */
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .kpi-card {
        background: linear-gradient(-45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1), rgba(102, 126, 234, 0.1));
        background-size: 200% 200%;
        animation: gradient-shift 8s ease infinite;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #667eea, #764ba2, #667eea);
        border-radius: 16px;
        opacity: 0;
        transition: opacity 0.3s;
        z-index: -1;
    }
    
    .kpi-card:hover::before {
        opacity: 0.3;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.3);
    }
    
    .section-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        margin: 20px 0;
    }
    
    .stat-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
    }
    
    .badge-critical {
        background: rgba(220, 38, 38, 0.2);
        color: #fca5a5;
        border: 1px solid rgba(220, 38, 38, 0.4);
    }
    
    .badge-warning {
        background: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .badge-success {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    .badge-info {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    
    .insight-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
        border-left: 4px solid #667eea;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }
    
    .pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ========================================
    # EXECUTIVE SUMMARY BANNER
    # ========================================
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>📊 Executive Intelligence Dashboard</h2>", unsafe_allow_html=True)
    
    # Quick insights banner
    total_crimes = db.query("MATCH (c:Crime) RETURN count(c) as n")[0]['n']
    open_cases = db.query("MATCH (c:Crime) WHERE c.status IN ['open', 'under investigation'] RETURN count(c) as n")[0]['n']
    critical_crimes = db.query("MATCH (c:Crime) WHERE c.severity IN ['critical', 'high', 'severe'] RETURN count(c) as n")[0]['n']
    
    solve_rate_query = db.query("""
        MATCH (c:Crime)
        WITH count(c) as total,
             count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved
        RETURN (solved * 100.0 / total) as rate
    """)
    solve_rate = solve_rate_query[0]['rate'] if solve_rate_query else 0
    
    # Status indicator
    if solve_rate >= 60:
        status_color = "#10b981"
        status_text = "PERFORMING WELL"
        status_icon = "🟢"
    elif solve_rate >= 40:
        status_color = "#f59e0b"
        status_text = "NEEDS ATTENTION"
        status_icon = "🟡"
    else:
        status_color = "#ef4444"
        status_text = "CRITICAL STATUS"
        status_icon = "🔴"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); 
                padding: 20px; border-radius: 16px; margin-bottom: 30px; border: 1px solid rgba(102, 126, 234, 0.3);'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h3 style='margin: 0; color: #ffffff;'>System Status: <span style='color: {status_color};'>{status_icon} {status_text}</span></h3>
                <p style='margin: 8px 0 0 0; color: #a0aec0; font-size: 0.95rem;'>
                    {total_crimes} total incidents • {open_cases} active cases • {critical_crimes} high severity • {solve_rate:.1f}% clearance rate
                </p>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 0.85rem; color: #94a3b8;'>Last Updated</div>
                <div style='font-size: 1.1rem; color: #ffffff; font-weight: 600;'>{datetime.now().strftime('%H:%M:%S')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================
    # INTERACTIVE GLOBAL FILTERS
    # ========================================
    with st.expander("🔍 Dashboard Filters & Settings", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            time_filter = st.selectbox(
                "📅 Time Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Year to Date", "All Time"],
                index=4,
                key="dash_time_filter"
            )
        
        with col2:
            districts_query = db.query("MATCH (l:Location) WHERE l.district IS NOT NULL RETURN DISTINCT l.district as district ORDER BY district")
            all_districts = [str(d['district']) for d in districts_query] if districts_query else []
            
            district_filter = st.multiselect(
                "🏛️ Districts",
                options=all_districts,
                default=[],
                key="dash_district_filter"
            )
        
        with col3:
            severity_filter = st.multiselect(
                "⚠️ Severity Levels",
                ["low", "medium", "high", "critical", "severe"],
                default=[],
                key="dash_severity_filter"
            )
        
        with col4:
            refresh_data = st.button("🔄 Refresh Data", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # KPI METRICS WITH SPARKLINES
    # ========================================
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Get comprehensive stats
    person_count = db.query("MATCH (p:Person) RETURN count(p) as count")[0]['count']
    org_count = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]['count']
    evidence_count = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]['count']
    weapon_count = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]['count']
    
    # High-risk suspects
    high_risk_query = db.query("""
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, count(c) as crimes
        WHERE crimes >= 3
        RETURN count(p) as count
    """)
    high_risk = high_risk_query[0]['count'] if high_risk_query else 0
    
    # Active gangs
    active_gangs_query = db.query("""
        MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
        WHERE c.date >= '2024-06-01'
        RETURN count(DISTINCT o) as count
    """)
    active_gangs = active_gangs_query[0]['count'] if active_gangs_query else 0
    
    # Critical evidence
    critical_evidence_query = db.query("""
        MATCH (e:Evidence)
        WHERE e.significance IN ['critical', 'high']
        RETURN count(e) as count
    """)
    critical_evidence = critical_evidence_query[0]['count'] if critical_evidence_query else 0
    
    # Recovered weapons
    recovered_weapons_query = db.query("""
        MATCH (w:Weapon)
        WHERE w.recovered = true
        RETURN count(w) as count
    """)
    recovered = recovered_weapons_query[0]['count'] if recovered_weapons_query else 0
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>TOTAL INCIDENTS</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: #667eea; margin: 8px 0;'>{total_crimes:,}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.85rem; color: #10b981;'>↑ {solve_rate:.1f}% solved</span>
                <span class='stat-badge badge-info'>Real Data</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>SUSPECTS</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: #f59e0b; margin: 8px 0;'>{person_count}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.85rem; color: #ef4444;'>⚠️ {high_risk} high-risk</span>
                <span class='stat-badge badge-warning'>{high_risk}/{person_count}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>ORGANIZATIONS</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: #ef4444; margin: 8px 0;'>{org_count}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.85rem; color: #f59e0b;'>🏴 {active_gangs} active</span>
                <span class='stat-badge badge-critical pulse'>THREAT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>EVIDENCE</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: #8b5cf6; margin: 8px 0;'>{evidence_count}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.85rem; color: #ef4444;'>🔥 {critical_evidence} critical</span>
                <span class='stat-badge badge-info'>{critical_evidence}/{evidence_count}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        recovery_rate = (recovered / weapon_count * 100) if weapon_count > 0 else 0
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;'>WEAPONS</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: #dc2626; margin: 8px 0;'>{weapon_count}</div>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.85rem; color: #10b981;'>✓ {recovered} recovered</span>
                <span class='stat-badge badge-success'>{recovery_rate:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # KEY INSIGHTS & ALERTS
    # ========================================
    st.markdown("### 🎯 Key Insights & Alerts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Serial offenders
        repeat = db.query("""
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WITH p, count(c) as crimes
            WHERE crimes >= 3
            RETURN count(p) as total, max(crimes) as max_crimes
        """)
        
        if repeat and repeat[0]['total'] > 0:
            st.markdown(f"""
            <div class='insight-card'>
                <h4 style='margin: 0 0 10px 0; color: #ffffff;'>⚠️ Serial Offenders Alert</h4>
                <div style='font-size: 2.2rem; font-weight: 700; color: #ef4444; margin: 10px 0;'>
                    {repeat[0]['total']}
                </div>
                <p style='margin: 0; color: #cbd5e0; font-size: 0.9rem;'>
                    Repeat offenders detected • Max: {repeat[0]['max_crimes']} crimes
                </p>
                <div style='margin-top: 12px;'>
                    <span class='stat-badge badge-critical pulse'>ACTION REQUIRED</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Armed gang members
        armed = db.query("""
            MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
            MATCH (p)-[:OWNS]->(w:Weapon)
            RETURN count(DISTINCT p) as total, 
                   count(DISTINCT o) as gangs,
                   count(DISTINCT w) as weapons
        """)
        
        if armed and armed[0]['total'] > 0:
            st.markdown(f"""
            <div class='insight-card' style='border-left-color: #f59e0b;'>
                <h4 style='margin: 0 0 10px 0; color: #ffffff;'>🔫 Armed Gang Members</h4>
                <div style='font-size: 2.2rem; font-weight: 700; color: #f59e0b; margin: 10px 0;'>
                    {armed[0]['total']}
                </div>
                <p style='margin: 0; color: #cbd5e0; font-size: 0.9rem;'>
                    {armed[0]['gangs']} gangs • {armed[0]['weapons']} weapons registered
                </p>
                <div style='margin-top: 12px;'>
                    <span class='stat-badge badge-warning'>HIGH PRIORITY</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Network analysis
        connected = db.query("""
            MATCH (p:Person)-[:KNOWS]-(other:Person)
            WITH p, count(DISTINCT other) as connections
            WHERE connections >= 6
            RETURN count(p) as total, max(connections) as max_connections
        """)
        
        if connected and connected[0]['total'] > 0:
            st.markdown(f"""
            <div class='insight-card' style='border-left-color: #3b82f6;'>
                <h4 style='margin: 0 0 10px 0; color: #ffffff;'>🕸️ Network Hub Analysis</h4>
                <div style='font-size: 2.2rem; font-weight: 700; color: #3b82f6; margin: 10px 0;'>
                    {connected[0]['total']}
                </div>
                <p style='margin: 0; color: #cbd5e0; font-size: 0.9rem;'>
                    Key connectors identified • Max: {connected[0]['max_connections']} connections
                </p>
                <div style='margin-top: 12px;'>
                    <span class='stat-badge badge-info'>MONITOR</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # CRIME TRENDS WITH COMPARISON
    # ========================================
    st.markdown("### 📈 Crime Trends & Temporal Analysis")
    
    trends_query = db.query("""
        MATCH (c:Crime)
        WHERE c.date IS NOT NULL AND c.date >= '2024-01-01'
        WITH substring(c.date, 0, 7) as year_month,
             count(c) as total_crimes,
             count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe_crimes,
             count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved_crimes
        RETURN year_month, total_crimes, severe_crimes, solved_crimes
        ORDER BY year_month
    """)
    
    if trends_query and len(trends_query) > 1:
        df_trends = pd.DataFrame(trends_query)
        
        # Calculate month-over-month change
        current_month = df_trends.iloc[-1]
        prev_month = df_trends.iloc[-2] if len(df_trends) > 1 else current_month
        
        crime_change = ((current_month['total_crimes'] - prev_month['total_crimes']) / prev_month['total_crimes'] * 100) if prev_month['total_crimes'] > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Multi-line trend chart with fill
            fig = go.Figure()
            
            # Total crimes with area fill
            fig.add_trace(go.Scatter(
                x=df_trends['year_month'],
                y=df_trends['total_crimes'],
                name='Total Crimes',
                mode='lines+markers',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10, symbol='circle'),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)',
                hovertemplate='<b>Total Crimes</b><br>Month: %{x}<br>Count: %{y}<extra></extra>'
            ))
            
            # Severe crimes line
            fig.add_trace(go.Scatter(
                x=df_trends['year_month'],
                y=df_trends['severe_crimes'],
                name='Severe Crimes',
                mode='lines+markers',
                line=dict(color='#ef4444', width=3, dash='dot'),
                marker=dict(size=10, symbol='diamond'),
                hovertemplate='<b>Severe Crimes</b><br>Month: %{x}<br>Count: %{y}<extra></extra>'
            ))
            
            # Solved crimes line
            fig.add_trace(go.Scatter(
                x=df_trends['year_month'],
                y=df_trends['solved_crimes'],
                name='Solved Cases',
                mode='lines+markers',
                line=dict(color='#10b981', width=2),
                marker=dict(size=8, symbol='star'),
                hovertemplate='<b>Solved Cases</b><br>Month: %{x}<br>Count: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(26, 31, 58, 0.8)',
                    bordercolor='rgba(102, 126, 234, 0.3)',
                    borderwidth=1
                ),
                xaxis=dict(title="Month", gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(title="Crime Count", gridcolor='rgba(255,255,255,0.1)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Trend Summary")
            
            # Month-over-month change
            change_color = '#ef4444' if crime_change > 0 else '#10b981'
            change_icon = '↑' if crime_change > 0 else '↓'
            
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 16px; border-radius: 10px; margin: 10px 0;'>
                <div style='color: #94a3b8; font-size: 0.8rem;'>MONTH CHANGE</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {change_color}; margin: 8px 0;'>
                    {change_icon} {abs(crime_change):.1f}%
                </div>
                <div style='color: #cbd5e0; font-size: 0.85rem;'>vs previous month</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Peak month
            peak_month = df_trends.loc[df_trends['total_crimes'].idxmax()]
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 16px; border-radius: 10px; margin: 10px 0;'>
                <div style='color: #94a3b8; font-size: 0.8rem;'>PEAK MONTH</div>
                <div style='font-size: 1.2rem; font-weight: 700; color: #ffffff; margin: 8px 0;'>
                    {peak_month['year_month']}
                </div>
                <div style='color: #cbd5e0; font-size: 0.85rem;'>{int(peak_month['total_crimes'])} crimes</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # CASE PIPELINE & PERFORMANCE
    # ========================================
    st.markdown("### ⚖️ Investigation Pipeline & Performance")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        # Enhanced funnel with actual data flow
        status_data = db.query("""
            MATCH (c:Crime)
            WITH count(c) as total,
                 count(CASE WHEN c.status = 'open' THEN 1 END) as open,
                 count(CASE WHEN c.status = 'under investigation' THEN 1 END) as investigating,
                 count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved,
                 count(CASE WHEN c.status = 'cold case' THEN 1 END) as cold
            RETURN total, open, investigating, solved, cold
        """)
        
        if status_data:
            data = status_data[0]
            
            fig = go.Figure()
            
            # Funnel chart
            fig.add_trace(go.Funnel(
                y=['📋 Reported', '🔍 Under Investigation', '✅ Solved', '❄️ Cold Case'],
                x=[data['total'], data['investigating'], data['solved'], data['cold']],
                textposition="inside",
                textinfo="value+percent initial",
                marker=dict(
                    color=['#3b82f6', '#f59e0b', '#10b981', '#6b7280'],
                    line=dict(width=2, color='rgba(255,255,255,0.3)')
                ),
                connector=dict(
                    line=dict(color='rgba(102, 126, 234, 0.3)', width=3, dash='dot')
                ),
                textfont=dict(size=14, color='white', family='Inter')
            ))
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0', size=13),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 Performance Metrics")
        
        # Clearance rate gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=solve_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Clearance Rate", 'font': {'size': 16, 'color': '#e2e8f0'}},
            delta={'reference': 50, 'increasing': {'color': "#10b981"}, 'decreasing': {'color': "#ef4444"}},
            number={'suffix': "%", 'font': {'size': 36, 'color': '#ffffff'}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': '#667eea'},
                'bar': {'color': "#667eea", 'thickness': 0.75},
                'bgcolor': 'rgba(255,255,255,0.1)',
                'borderwidth': 2,
                'bordercolor': 'rgba(102, 126, 234, 0.3)',
                'steps': [
                    {'range': [0, 33], 'color': 'rgba(239, 68, 68, 0.3)'},
                    {'range': [33, 66], 'color': 'rgba(245, 158, 11, 0.3)'},
                    {'range': [66, 100], 'color': 'rgba(16, 185, 129, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 3},
                    'thickness': 0.8,
                    'value': 50
                }
            }
        ))
        
        fig_gauge.update_layout(
            height=280,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Mini metrics
        active_pct = ((data['open'] + data['investigating']) / data['total'] * 100) if data['total'] > 0 else 0
        cold_pct = (data['cold'] / data['total'] * 100) if data['total'] > 0 else 0
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("🔄 Active", f"{active_pct:.0f}%", delta=f"{data['open'] + data['investigating']} cases")
        with col_b:
            st.metric("❄️ Cold", f"{cold_pct:.0f}%", delta=f"{data['cold']} cases", delta_color="inverse")
    
    st.markdown("---")
    
    # ========================================
    # GANG INTELLIGENCE MATRIX
    # ========================================
    st.markdown("### 🏴 Gang Intelligence & Threat Matrix")
    
    gang_data = db.query("""
        MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)
        OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
        OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
        WITH o,
             count(DISTINCT p) as members,
             count(DISTINCT c) as crimes,
             count(DISTINCT w) as weapons,
             count(DISTINCT CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN c END) as severe_crimes
        RETURN o.name as gang,
               o.territory as territory,
               o.type as type,
               members,
               crimes,
               weapons,
               severe_crimes,
               CASE 
                   WHEN crimes >= 45 AND weapons >= 8 THEN 5
                   WHEN crimes >= 35 AND weapons >= 5 THEN 4
                   WHEN crimes >= 25 THEN 3
                   WHEN crimes >= 15 THEN 2
                   ELSE 1
               END as threat_level
        ORDER BY threat_level DESC, crimes DESC
    """)
    
    if gang_data:
        df_gangs = pd.DataFrame(gang_data)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 4D Bubble chart (members, crimes, weapons, threat)
            fig = px.scatter(
                df_gangs,
                x='members',
                y='crimes',
                size='weapons',
                color='threat_level',
                hover_name='gang',
                hover_data={
                    'territory': True,
                    'severe_crimes': True,
                    'threat_level': True,
                    'members': True,
                    'crimes': True,
                    'weapons': True
                },
                color_continuous_scale=[[0, '#10b981'], [0.4, '#3b82f6'], [0.7, '#f59e0b'], [1, '#ef4444']],
                size_max=70,
                labels={
                    'members': 'Gang Members',
                    'crimes': 'Total Crimes',
                    'weapons': 'Weapons Arsenal',
                    'threat_level': 'Threat Level (1-5)'
                },
                title='Gang Threat Assessment (Size = Weapons, Color = Threat)'
            )
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                title_font_size=14,
                title_x=0
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🎯 Threat Rankings")
            
            for idx, gang in df_gangs.head(5).iterrows():
                threat = gang['threat_level']
                
                if threat >= 4:
                    color = '#dc2626'
                    badge = '🔴 CRITICAL'
                    border_width = '4px'
                elif threat == 3:
                    color = '#f59e0b'
                    badge = '🟠 HIGH'
                    border_width = '3px'
                elif threat == 2:
                    color = '#3b82f6'
                    badge = '🟡 MEDIUM'
                    border_width = '2px'
                else:
                    color = '#10b981'
                    badge = '🟢 LOW'
                    border_width = '2px'
                
                st.markdown(f"""
                <div class='section-card' style='padding: 14px; margin: 10px 0; border-left: {border_width} solid {color};'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div style='flex: 1;'>
                            <h4 style='margin: 0; color: #ffffff; font-size: 1rem;'>{gang['gang']}</h4>
                            <p style='margin: 6px 0 0 0; color: #a0aec0; font-size: 0.85rem; line-height: 1.5;'>
                                📍 {gang['territory']} • {gang['type']}<br/>
                                👥 {gang['members']} members • 🚨 {gang['crimes']} crimes<br/>
                                🔫 {gang['weapons']} weapons • ⚠️ {gang['severe_crimes']} severe
                            </p>
                        </div>
                        <div style='text-align: right;'>
                            <span class='stat-badge badge-critical' style='background: rgba(220, 38, 38, 0.25); color: {color}; border-color: {color};'>
                                {badge}
                            </span>
                            <div style='font-size: 1.5rem; font-weight: 700; color: {color}; margin-top: 6px;'>
                                {threat}/5
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # ANALYTICS GRID (3 COLUMNS)
    # ========================================
    st.markdown("### 📊 Crime Analytics Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Top Crime Types")
        
        crime_types = db.query("""
            MATCH (c:Crime)
            RETURN c.type as type, count(c) as count
            ORDER BY count DESC
            LIMIT 8
        """)
        
        if crime_types:
            df = pd.DataFrame(crime_types)
            
            fig = go.Figure(go.Bar(
                x=df['count'],
                y=df['type'],
                orientation='h',
                marker=dict(
                    color=df['count'],
                    colorscale='Reds',
                    showscale=False,
                    line=dict(color='rgba(255,255,255,0.2)', width=1)
                ),
                text=df['count'],
                textposition='outside',
                textfont=dict(size=12, color='#e2e8f0'),
                hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
            ))
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Count",
                yaxis_title="",
                margin=dict(l=0, r=40, t=20, b=20),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Severity Distribution")
        
        severity = db.query("""
            MATCH (c:Crime)
            RETURN c.severity as severity, count(c) as count
            ORDER BY 
                CASE c.severity
                    WHEN 'critical' THEN 1
                    WHEN 'severe' THEN 2
                    WHEN 'high' THEN 2
                    WHEN 'moderate' THEN 3
                    WHEN 'medium' THEN 3
                    ELSE 4
                END
        """)
        
        if severity:
            df = pd.DataFrame(severity)
            
            colors_map = {
                'critical': '#8e44ad',
                'severe': '#e74c3c',
                'high': '#e74c3c',
                'moderate': '#f39c12',
                'medium': '#f39c12',
                'minor': '#2ecc71',
                'low': '#2ecc71'
            }
            
            fig = go.Figure(data=[go.Pie(
                labels=df['severity'],
                values=df['count'],
                hole=0.5,
                marker=dict(
                    colors=[colors_map.get(s, '#3b82f6') for s in df['severity']],
                    line=dict(color='rgba(255,255,255,0.3)', width=2)
                ),
                textinfo='label+percent',
                textfont=dict(size=12, color='white'),
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
            )])
            
            # Add center text
            fig.add_annotation(
                text=f"<b>{total_crimes}</b><br>Total",
                x=0.5, y=0.5,
                font=dict(size=18, color='#ffffff'),
                showarrow=False
            )
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    bgcolor='rgba(26, 31, 58, 0.8)',
                    bordercolor='rgba(102, 126, 234, 0.2)',
                    borderwidth=1
                ),
                margin=dict(l=20, r=80, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown("#### District Breakdown")
        
        district_data = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            WHERE l.district IS NOT NULL
            RETURN l.district as district, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 8
        """)
        
        if district_data:
            df_districts = pd.DataFrame(district_data)
            
            fig = px.bar(
                df_districts,
                x='district',
                y='crimes',
                color='crimes',
                color_continuous_scale='Plasma',
                text='crimes',
                labels={'district': 'District', 'crimes': 'Crime Count'}
            )
            
            fig.update_traces(
                textposition='outside',
                textfont=dict(size=12, color='#e2e8f0'),
                marker_line_color='rgba(255,255,255,0.2)',
                marker_line_width=1
            )
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                showlegend=False,
                xaxis_title="District",
                yaxis_title="Crimes",
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # TACTICAL INTELLIGENCE
    # ========================================
    st.markdown("### 🎯 Tactical Intelligence & Operations")
    
    tab1, tab2, tab3 = st.tabs(["🔫 Weapons & Assets", "👮 Investigator Performance", "🗺️ Geographic Hotspots"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Weapon Status")
            
            weapon_status = db.query("""
                MATCH (w:Weapon)
                WITH w.type as type,
                     count(w) as total,
                     count(CASE WHEN w.recovered = true THEN 1 END) as recovered
                RETURN type, total, recovered, (total - recovered) as at_large
                ORDER BY total DESC
            """)
            
            if weapon_status:
                df_weapons = pd.DataFrame(weapon_status)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='✅ Recovered',
                    x=df_weapons['type'],
                    y=df_weapons['recovered'],
                    marker=dict(color='#10b981', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_weapons['recovered'],
                    textposition='inside',
                    textfont=dict(color='white')
                ))
                
                fig.add_trace(go.Bar(
                    name='⚠️ At Large',
                    x=df_weapons['type'],
                    y=df_weapons['at_large'],
                    marker=dict(color='#ef4444', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_weapons['at_large'],
                    textposition='inside',
                    textfont=dict(color='white')
                ))
                
                fig.update_layout(
                    barmode='stack',
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_title="Weapon Type",
                    yaxis_title="Count",
                    legend=dict(orientation='h', yanchor='bottom', y=1.02),
                    margin=dict(l=20, r=20, t=20, b=40)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Evidence Significance")
            
            evidence_data = db.query("""
                MATCH (e:Evidence)
                WITH e.significance as significance,
                     count(e) as total,
                     count(CASE WHEN e.verified = true THEN 1 END) as verified
                RETURN significance, total, verified
                ORDER BY 
                    CASE significance
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END
            """)
            
            if evidence_data:
                df_evidence = pd.DataFrame(evidence_data)
                
                # Radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=df_evidence['total'],
                    theta=df_evidence['significance'],
                    fill='toself',
                    name='Total Evidence',
                    fillcolor='rgba(102, 126, 234, 0.3)',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=8)
                ))
                
                fig.add_trace(go.Scatterpolar(
                    r=df_evidence['verified'],
                    theta=df_evidence['significance'],
                    fill='toself',
                    name='Verified',
                    fillcolor='rgba(16, 185, 129, 0.3)',
                    line=dict(color='#10b981', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            gridcolor='rgba(255,255,255,0.15)',
                            tickfont=dict(color='#e2e8f0', size=10)
                        ),
                        angularaxis=dict(
                            gridcolor='rgba(255,255,255,0.15)',
                            tickfont=dict(color='#e2e8f0', size=11)
                        ),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    showlegend=True,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=-0.2,
                        xanchor='center',
                        x=0.5
                    ),
                    margin=dict(l=60, r=60, t=20, b=60)
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### Investigator Performance Matrix")
        
        inv_data = db.query("""
            MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
            WITH i,
                 count(c) as total_cases,
                 count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved,
                 count(CASE WHEN c.status IN ['open', 'under investigation'] THEN 1 END) as active
            RETURN i.name as investigator,
                   i.department as department,
                   total_cases,
                   solved,
                   active,
                   CASE WHEN total_cases > 0 THEN (solved * 100.0 / total_cases) ELSE 0 END as solve_rate
            ORDER BY solve_rate DESC, solved DESC
        """)
        
        if inv_data:
            df_inv = pd.DataFrame(inv_data)
            
            # Grouped bar + line overlay
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    name='✅ Solved',
                    x=df_inv['investigator'],
                    y=df_inv['solved'],
                    marker=dict(color='#10b981', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_inv['solved'],
                    textposition='inside',
                    textfont=dict(color='white', size=11)
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Bar(
                    name='🔄 Active',
                    x=df_inv['investigator'],
                    y=df_inv['active'],
                    marker=dict(color='#f59e0b', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_inv['active'],
                    textposition='inside',
                    textfont=dict(color='white', size=11)
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    name='📈 Solve Rate %',
                    x=df_inv['investigator'],
                    y=df_inv['solve_rate'],
                    mode='lines+markers',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=12, symbol='diamond', line=dict(color='white', width=2)),
                    yaxis='y2'
                ),
                secondary_y=True
            )
            
            fig.update_xaxes(title_text="Investigator", tickangle=-45)
            fig.update_yaxes(title_text="Cases", secondary_y=False)
            fig.update_yaxes(title_text="Solve Rate (%)", secondary_y=True, range=[0, 100])
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                barmode='group',
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance leaderboard
            st.markdown("##### 🏆 Top Performers")
            
            top_3 = df_inv.head(3)
            for idx, inv in top_3.iterrows():
                medal = '🥇' if idx == 0 else '🥈' if idx == 1 else '🥉'
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin: 8px 0;'>
                    {medal} <strong>{inv['investigator']}</strong> ({inv['department']})<br/>
                    <span style='color: #a0aec0; font-size: 0.85rem;'>
                        {inv['solved']}/{inv['total_cases']} solved • {inv['solve_rate']:.0f}% rate
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        col_a, col_b = st.columns([1.5, 1])
        
        with col_a:
            st.markdown("#### Crime Density by District")
            
            district_heatmap = db.query("""
                MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
                WHERE l.district IS NOT NULL
                WITH l.district as district, 
                     count(c) as total,
                     count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe
                RETURN district, total, severe, (total - severe) as other
                ORDER BY total DESC
                LIMIT 12
            """)
            
            if district_heatmap:
                df_districts = pd.DataFrame(district_heatmap)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='⚠️ Severe',
                    y=df_districts['district'],
                    x=df_districts['severe'],
                    orientation='h',
                    marker=dict(color='#ef4444', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_districts['severe'],
                    textposition='inside',
                    textfont=dict(color='white', size=10)
                ))
                
                fig.add_trace(go.Bar(
                    name='📊 Other',
                    y=df_districts['district'],
                    x=df_districts['other'],
                    orientation='h',
                    marker=dict(color='#3b82f6', line=dict(color='rgba(255,255,255,0.2)', width=1)),
                    text=df_districts['other'],
                    textposition='inside',
                    textfont=dict(color='white', size=10)
                ))
                
                fig.update_layout(
                    barmode='stack',
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_title="Crime Count",
                    yaxis_title="District",
                    legend=dict(orientation='h', yanchor='bottom', y=1.02),
                    margin=dict(l=60, r=20, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            st.markdown("#### Top 10 Hotspots")
            
            hotspots = db.query("""
                MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
                RETURN l.name as location, 
                       l.district as district, 
                       count(c) as crimes,
                       count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe
                ORDER BY crimes DESC
                LIMIT 10
            """)
            
            if hotspots:
                for i, spot in enumerate(hotspots, 1):
                    severity_pct = (spot['severe'] / spot['crimes'] * 100) if spot['crimes'] > 0 else 0
                    
                    if severity_pct >= 60:
                        color = '#dc2626'
                        intensity = '🔥🔥🔥'
                    elif severity_pct >= 40:
                        color = '#f59e0b'
                        intensity = '🔥🔥'
                    else:
                        color = '#3b82f6'
                        intensity = '🔥'
                    
                    st.markdown(f"""
                    <div class='section-card' style='padding: 12px; margin: 8px 0;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div style='flex: 1;'>
                                <strong style='color: #ffffff; font-size: 0.95rem;'>{i}. {spot['location'][:35]}</strong>
                                <div style='color: #94a3b8; font-size: 0.8rem; margin-top: 4px;'>
                                    District {spot['district']} • {spot['crimes']} crimes
                                </div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 1rem; margin-bottom: 2px;'>{intensity}</div>
                                <div style='font-size: 0.75rem; color: {color}; font-weight: 600;'>{severity_pct:.0f}% severe</div>
                            </div>
                        </div>
                        <div style='margin-top: 8px; background: rgba(255,255,255,0.1); height: 4px; border-radius: 2px; overflow: hidden;'>
                            <div style='background: {color}; width: {severity_pct}%; height: 100%; transition: width 0.5s ease;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # REAL-TIME ACTIVITY FEED
    # ========================================
    st.markdown("### 🚨 Live Activity Monitor")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Recent Incidents")
        
        recent = db.query("""
            MATCH (c:Crime)
            OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
            OPTIONAL MATCH (p:Person)-[:PARTY_TO]->(c)
            RETURN c.id as id,
                   c.type as type,
                   c.date as date,
                   c.time as time,
                   c.severity as severity,
                   c.status as status,
                   COALESCE(l.name, 'Unknown Location') as location,
                   COALESCE(l.district, 'N/A') as district,
                   collect(DISTINCT p.name)[0] as suspect
            ORDER BY c.date DESC, c.time DESC
            LIMIT 8
        """)
        
        if recent:
            for activity in recent:
                severity = activity['severity']
                
                if severity in ['critical', 'severe']:
                    border_color = '#dc2626'
                    icon = '🚨'
                    status_badge_class = 'badge-critical'
                elif severity in ['high']:
                    border_color = '#f59e0b'
                    icon = '⚠️'
                    status_badge_class = 'badge-warning'
                else:
                    border_color = '#3b82f6'
                    icon = '📍'
                    status_badge_class = 'badge-info'
                
                suspect_text = activity['suspect'] if activity['suspect'] else "No suspect identified"
                
                st.markdown(f"""
                <div class='section-card' style='padding: 16px; margin: 10px 0; border-left: 3px solid {border_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div style='flex: 1;'>
                            <div style='font-size: 1.05rem; font-weight: 600; color: #ffffff; margin-bottom: 8px;'>
                                {icon} {activity['type']}
                            </div>
                            <div style='color: #a0aec0; font-size: 0.85rem; line-height: 1.6;'>
                                📅 {activity['date']} at {activity['time']}<br/>
                                📍 {activity['location'][:45]}<br/>
                                🏛️ District {activity['district']} • 👤 {suspect_text}
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <span class='stat-badge {status_badge_class}' style='margin-bottom: 6px;'>
                                {activity['status'].upper()}
                            </span>
                            <div style='font-size: 0.75rem; color: {border_color}; font-weight: 600; margin-top: 6px;'>
                                {severity.upper()}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📊 Quick Stats")
        
        # Recent activity stats
        if trends_query and len(df_trends) > 0:
            latest_month = df_trends.iloc[-1]
            
            st.metric("Recent Month Crimes", int(latest_month['total_crimes']))
            st.metric("Severe Incidents", int(latest_month['severe_crimes']), 
                     delta_color="inverse")
            st.metric("Cases Solved", int(latest_month['solved_crimes']))
        
        # Peak activity time
        peak_hour = db.query("""
            MATCH (c:Crime)
            WHERE c.time IS NOT NULL
            WITH substring(c.time, 0, 2) as hour, count(c) as crimes
            RETURN hour, crimes
            ORDER BY crimes DESC
            LIMIT 1
        """)
        
        if peak_hour and peak_hour[0]['hour']:
            hour = peak_hour[0]['hour']
            st.metric("🕐 Peak Hour", f"{hour}:00", delta="Most active")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("#### ⚡ Quick Actions")
        
        if st.button("📈 Analyze Trends", use_container_width=True, type="secondary"):
            st.session_state.page = 'Timeline Analysis'
            st.rerun()
        
        if st.button("🗺️ View Map", use_container_width=True, type="secondary"):
            st.session_state.page = 'Geographic Mapping'
            st.rerun()
        
        if st.button("🕸️ Network Viz", use_container_width=True, type="secondary"):
            st.session_state.page = 'Network Visualization'
            st.rerun()
        
        if st.button("📐 View Schema", use_container_width=True, type="secondary"):
            st.session_state.page = 'Graph Schema'
            st.rerun()
    
    st.markdown("---")
    
    # ========================================
    # ACTIONABLE INTELLIGENCE
    # ========================================
    st.markdown("### 💡 Actionable Intelligence & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Priority Targets")
        
        targets = db.query("""
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WITH p, count(c) as crimes
            WHERE crimes >= 2
            OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
            RETURN p.name as name,
                   p.age as age,
                   crimes,
                   count(DISTINCT w) as weapons,
                   COALESCE(o.name, 'Independent') as gang,
                   CASE 
                       WHEN crimes >= 5 AND count(w) > 0 THEN '🔴 CRITICAL'
                       WHEN crimes >= 4 THEN '🟠 HIGH'
                       WHEN crimes >= 2 THEN '🟡 MEDIUM'
                       ELSE '🟢 LOW'
                   END as priority
            ORDER BY crimes DESC, weapons DESC
            LIMIT 10
        """)
        
        if targets:
            for target in targets:
                priority = target['priority']
                
                if '🔴' in priority:
                    bg_color = 'rgba(220, 38, 38, 0.15)'
                    border = '#dc2626'
                elif '🟠' in priority:
                    bg_color = 'rgba(245, 158, 11, 0.15)'
                    border = '#f59e0b'
                elif '🟡' in priority:
                    bg_color = 'rgba(59, 130, 246, 0.15)'
                    border = '#3b82f6'
                else:
                    bg_color = 'rgba(16, 185, 129, 0.15)'
                    border = '#10b981'
                
                st.markdown(f"""
                <div style='background: {bg_color}; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid {border}; display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='color: #ffffff;'>{target['name']}</strong> <span style='color: #94a3b8;'>(Age {target['age']})</span><br/>
                        <span style='color: #a0aec0; font-size: 0.85rem;'>
                            {target['gang']} • {target['crimes']} crimes • {target['weapons']} weapons
                        </span>
                    </div>
                    <span class='stat-badge' style='background: {bg_color}; color: {border}; border-color: {border};'>
                        {priority}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🔍 Investigation Gaps")
        
        # Orphaned crimes (no location)
        orphan_crimes = db.query("""
            MATCH (c:Crime)
            WHERE NOT EXISTS((c)-[:OCCURRED_AT]->())
            RETURN count(c) as count
        """)[0]['count']
        
        # Crimes without evidence
        no_evidence = db.query("""
            MATCH (c:Crime)
            WHERE NOT EXISTS((c)-[:HAS_EVIDENCE]->())
            RETURN count(c) as count
        """)[0]['count']
        
        # Unsolved high severity
        unsolved_severe = db.query("""
            MATCH (c:Crime)
            WHERE c.severity IN ['high', 'critical', 'severe']
              AND NOT c.status IN ['solved', 'closed']
            RETURN count(c) as count
        """)[0]['count']
        
        # Suspects with no gang affiliation
        independent_suspects = db.query("""
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WHERE NOT EXISTS((p)-[:MEMBER_OF]->())
            WITH DISTINCT p
            RETURN count(p) as count
        """)[0]['count']
        
        gaps = [
            ("Orphaned Crimes", orphan_crimes, "Missing location data", "#ef4444"),
            ("Missing Evidence", no_evidence, "No forensic links", "#f59e0b"),
            ("Unsolved Severe", unsolved_severe, "High priority cases", "#dc2626"),
            ("Independent Actors", independent_suspects, "No gang affiliation", "#3b82f6")
        ]
        
        for title, count, description, color in gaps:
            if count > 0:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.03); padding: 14px; border-radius: 8px; margin: 10px 0; border-left: 3px solid {color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='color: #ffffff; font-weight: 600; font-size: 0.95rem;'>{title}</div>
                            <div style='color: #94a3b8; font-size: 0.8rem; margin-top: 4px;'>{description}</div>
                        </div>
                        <div style='font-size: 1.5rem; font-weight: 700; color: {color};'>{count}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)