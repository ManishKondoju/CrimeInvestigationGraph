# enhanced_dashboard.py - Modern Interactive Dashboard
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

def render_enhanced_dashboard(db):
    """Render modern interactive dashboard with advanced visualizations"""
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 40px;'>📊 Crime Intelligence Dashboard</h2>", unsafe_allow_html=True)
    
    # ========================================
    # INTERACTIVE FILTERS (NEW!)
    # ========================================
    with st.expander("🔍 Dashboard Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.selectbox(
                "📅 Time Period",
                ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Year to Date", "All Time"],
                index=4
            )
        
        with col2:
            # Get available districts
            districts_query = db.query("MATCH (l:Location) RETURN DISTINCT l.district as district ORDER BY district")
            all_districts = [str(d['district']) for d in districts_query] if districts_query else []
            
            selected_districts = st.multiselect(
                "🏛️ Districts",
                options=all_districts,
                default=[]
            )
        
        with col3:
            severity_filter = st.multiselect(
                "⚠️ Severity",
                ["low", "medium", "high", "critical"],
                default=[]
            )
    
    st.markdown("---")
    
    # ========================================
    # KPI CARDS WITH TRENDS (ENHANCED!)
    # ========================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    crime_count = db.query("MATCH (c:Crime) RETURN count(c) as count")[0]['count']
    person_count = db.query("MATCH (p:Person) RETURN count(p) as count")[0]['count']
    org_count = db.query("MATCH (o:Organization) RETURN count(o) as count")[0]['count']
    evidence_count = db.query("MATCH (e:Evidence) RETURN count(e) as count")[0]['count']
    weapon_count = db.query("MATCH (w:Weapon) RETURN count(w) as count")[0]['count']
    
    # Calculate trends (if possible)
    solved_rate_query = db.query("""
        MATCH (c:Crime)
        WITH count(c) as total,
             count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved
        RETURN (solved * 100.0 / total) as rate
    """)
    solved_rate = solved_rate_query[0]['rate'] if solved_rate_query else 0
    
    with col1:
        st.metric("🚨 Total Crimes", f"{crime_count:,}", delta=f"{solved_rate:.1f}% solved")
    
    with col2:
        # Get high-risk suspects
        high_risk = db.query("""
            MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
            WITH p, count(c) as crimes
            WHERE crimes >= 3
            RETURN count(p) as count
        """)[0]['count']
        st.metric("👤 Suspects", person_count, delta=f"{high_risk} high-risk", delta_color="inverse")
    
    with col3:
        # Get active gangs
        active_gangs = db.query("""
            MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
            WHERE c.date >= '2024-01-01'
            RETURN count(DISTINCT o) as count
        """)[0]['count']
        st.metric("🏴 Gangs", org_count, delta=f"{active_gangs} active", delta_color="inverse")
    
    with col4:
        # Critical evidence
        critical_evidence = db.query("""
            MATCH (e:Evidence)
            WHERE e.significance IN ['critical', 'high']
            RETURN count(e) as count
        """)[0]['count']
        st.metric("📦 Evidence", evidence_count, delta=f"{critical_evidence} critical")
    
    with col5:
        # Recovered weapons
        recovered = db.query("""
            MATCH (w:Weapon)
            WHERE w.recovered = true
            RETURN count(w) as count
        """)[0]['count']
        st.metric("🔫 Weapons", weapon_count, delta=f"{recovered} recovered")
    
    st.markdown("---")
    
    # ========================================
    # CRIME TRENDS OVER TIME (NEW!)
    # ========================================
    st.markdown('<div class="section-title">📈 Crime Trends & Temporal Analysis</div>', unsafe_allow_html=True)
    
    # Get crimes by month
    trends_query = db.query("""
        MATCH (c:Crime)
        WHERE c.date IS NOT NULL
        WITH c, 
             substring(c.date, 0, 7) as year_month,
             c.severity as severity
        RETURN year_month, 
               count(c) as total_crimes,
               count(CASE WHEN severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe_crimes
        ORDER BY year_month
    """)
    
    if trends_query and len(trends_query) > 0:
        df_trends = pd.DataFrame(trends_query)
        
        # Create dual-axis trend chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(
                x=df_trends['year_month'],
                y=df_trends['total_crimes'],
                name='Total Crimes',
                mode='lines+markers',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_trends['year_month'],
                y=df_trends['severe_crimes'],
                name='Severe Crimes',
                mode='lines+markers',
                line=dict(color='#ef4444', width=3, dash='dot'),
                marker=dict(size=8, symbol='diamond')
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Month")
        fig.update_yaxes(title_text="Total Crimes", secondary_y=False)
        fig.update_yaxes(title_text="Severe Crimes", secondary_y=True)
        
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
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # CRIME ANALYTICS WITH BETTER CHARTS
    # ========================================
    st.markdown('<div class="section-title">📊 Crime Analytics & Distribution</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
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
            
            # Horizontal bar chart (better for long labels)
            fig = go.Figure(go.Bar(
                x=df['count'],
                y=df['type'],
                orientation='h',
                marker=dict(
                    color=df['count'],
                    colorscale='Reds',
                    showscale=False
                ),
                text=df['count'],
                textposition='outside'
            ))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Number of Incidents",
                yaxis_title="",
                height=400,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Severity Breakdown")
        severity = db.query("""
            MATCH (c:Crime)
            RETURN c.severity as severity, count(c) as count
            ORDER BY 
                CASE c.severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'severe' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'moderate' THEN 3
                    ELSE 4
                END
        """)
        
        if severity:
            df = pd.DataFrame(severity)
            
            colors = {
                'critical': '#8e44ad',
                'severe': '#e74c3c',
                'high': '#e74c3c',
                'moderate': '#f39c12',
                'medium': '#f39c12',
                'minor': '#2ecc71',
                'low': '#2ecc71'
            }
            
            # Donut chart with better styling
            fig = go.Figure(data=[go.Pie(
                labels=df['severity'],
                values=df['count'],
                hole=0.5,
                marker=dict(
                    colors=[colors.get(s, '#3b82f6') for s in df['severity']],
                    line=dict(color='rgba(255,255,255,0.2)', width=2)
                ),
                textinfo='label+percent',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # CASE PROGRESSION FUNNEL (NEW!)
    # ========================================
    st.markdown('<div class="section-title">⚖️ Investigation Pipeline & Case Progression</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("#### Case Status Funnel")
        
        # Get case progression data
        status_progression = db.query("""
            MATCH (c:Crime)
            WITH count(c) as total_cases,
                 count(CASE WHEN c.status = 'open' THEN 1 END) as open,
                 count(CASE WHEN c.status = 'under investigation' THEN 1 END) as investigating,
                 count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved,
                 count(CASE WHEN c.status = 'cold case' THEN 1 END) as cold
            RETURN total_cases, open, investigating, solved, cold
        """)
        
        if status_progression:
            data = status_progression[0]
            
            # Funnel chart showing case progression
            fig = go.Figure(go.Funnel(
                y=['📋 Reported', '🔍 Under Investigation', '✅ Solved', '❄️ Cold Case'],
                x=[data['total_cases'], data['investigating'], data['solved'], data['cold']],
                textposition="inside",
                textinfo="value+percent initial",
                marker=dict(
                    color=['#3b82f6', '#f59e0b', '#10b981', '#6b7280']
                ),
                connector=dict(line=dict(color='rgba(255,255,255,0.2)', width=2))
            ))
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0', size=14)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Clearance Metrics")
        
        # Calculate clearance rates
        if status_progression:
            data = status_progression[0]
            total = data['total_cases']
            solved = data['solved']
            cold = data['cold']
            active = data['open'] + data['investigating']
            
            clearance_rate = (solved / total * 100) if total > 0 else 0
            active_rate = (active / total * 100) if total > 0 else 0
            cold_rate = (cold / total * 100) if total > 0 else 0
            
            # Gauge chart for clearance rate
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=clearance_rate,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Clearance Rate", 'font': {'size': 16, 'color': '#e2e8f0'}},
                delta={'reference': 50, 'increasing': {'color': "#10b981"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': '#e2e8f0'},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 33], 'color': 'rgba(239, 68, 68, 0.3)'},
                        {'range': [33, 66], 'color': 'rgba(245, 158, 11, 0.3)'},
                        {'range': [66, 100], 'color': 'rgba(16, 185, 129, 0.3)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Mini metrics
            st.metric("🔄 Active Cases", f"{active_rate:.1f}%", delta=f"{active} cases")
            st.metric("❄️ Cold Cases", f"{cold_rate:.1f}%", delta=f"{cold} cases", delta_color="inverse")
    
    st.markdown("---")
    
    # ========================================
    # GANG INTELLIGENCE MATRIX (NEW!)
    # ========================================
    st.markdown('<div class="section-title">🏴 Gang Intelligence Matrix</div>', unsafe_allow_html=True)
    
    gang_matrix = db.query("""
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
               members,
               crimes,
               weapons,
               severe_crimes,
               CASE 
                   WHEN crimes > 40 AND weapons > 8 THEN 5
                   WHEN crimes > 30 AND weapons > 5 THEN 4
                   WHEN crimes > 20 THEN 3
                   WHEN crimes > 10 THEN 2
                   ELSE 1
               END as threat_level
        ORDER BY threat_level DESC, crimes DESC
    """)
    
    if gang_matrix:
        df_gangs = pd.DataFrame(gang_matrix)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bubble chart: x=members, y=crimes, size=weapons, color=threat
            fig = px.scatter(
                df_gangs,
                x='members',
                y='crimes',
                size='weapons',
                color='threat_level',
                hover_name='gang',
                hover_data={'territory': True, 'severe_crimes': True, 'threat_level': True},
                color_continuous_scale='Reds',
                size_max=60,
                labels={
                    'members': 'Gang Members',
                    'crimes': 'Total Crimes',
                    'weapons': 'Weapons',
                    'threat_level': 'Threat Level (1-5)'
                }
            )
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                title=None
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Threat Matrix")
            
            for _, gang in df_gangs.iterrows():
                threat = gang['threat_level']
                if threat >= 4:
                    color = '#dc2626'
                    badge = '🔴 CRITICAL'
                elif threat == 3:
                    color = '#f59e0b'
                    badge = '🟠 HIGH'
                elif threat == 2:
                    color = '#3b82f6'
                    badge = '🟡 MEDIUM'
                else:
                    color = '#10b981'
                    badge = '🟢 LOW'
                
                st.markdown(f"""
                <div class='glass-card' style='border-left: 4px solid {color}; padding: 12px; margin: 8px 0;'>
                    <strong style='color: #ffffff;'>{gang['gang']}</strong>
                    <div style='color: #a0aec0; font-size: 0.85rem; margin-top: 4px;'>
                        👥 {gang['members']} members • 🚨 {gang['crimes']} crimes • 🔫 {gang['weapons']} weapons
                    </div>
                    <div style='margin-top: 6px; font-weight: 600; color: {color}; font-size: 0.9rem;'>
                        {badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # GEOGRAPHIC HOTSPOTS (ENHANCED)
    # ========================================
    st.markdown('<div class="section-title">🗺️ Geographic Crime Hotspots</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("#### District Crime Heatmap")
        
        district_data = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            WHERE l.district IS NOT NULL
            WITH l.district as district, 
                 count(c) as total,
                 count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe
            RETURN district, total, severe
            ORDER BY total DESC
            LIMIT 20
        """)
        
        if district_data:
            df_districts = pd.DataFrame(district_data)
            
            # Stacked horizontal bar
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Severe',
                y=df_districts['district'],
                x=df_districts['severe'],
                orientation='h',
                marker=dict(color='#ef4444'),
                text=df_districts['severe'],
                textposition='inside'
            ))
            
            fig.add_trace(go.Bar(
                name='Other',
                y=df_districts['district'],
                x=df_districts['total'] - df_districts['severe'],
                orientation='h',
                marker=dict(color='#3b82f6'),
                text=df_districts['total'] - df_districts['severe'],
                textposition='inside'
            ))
            
            fig.update_layout(
                barmode='stack',
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Crime Count",
                yaxis_title="District",
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Top 15 Hotspots")
        
        hotspots = db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            RETURN l.name as location, 
                   l.district as district, 
                   count(c) as crimes,
                   count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as severe
            ORDER BY crimes DESC
            LIMIT 15
        """)
        
        if hotspots:
            for i, spot in enumerate(hotspots, 1):
                severity_ratio = (spot['severe'] / spot['crimes'] * 100) if spot['crimes'] > 0 else 0
                
                if severity_ratio > 50:
                    color = '#dc2626'
                    intensity = '🔥🔥🔥'
                elif severity_ratio > 25:
                    color = '#f59e0b'
                    intensity = '🔥🔥'
                else:
                    color = '#3b82f6'
                    intensity = '🔥'
                
                st.markdown(f"""
                <div class='glass-card' style='padding: 10px; margin: 6px 0;'>
                    <strong style='color: #ffffff; font-size: 0.95rem;'>{i}. {spot['location'][:40]}</strong>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 6px;'>
                        <span style='color: #a0aec0; font-size: 0.85rem;'>
                            District {spot['district']} • {spot['crimes']} crimes
                        </span>
                        <span style='font-size: 0.85rem;'>{intensity}</span>
                    </div>
                    <div style='margin-top: 6px;'>
                        <div style='background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;'>
                            <div style='background: {color}; width: {severity_ratio}%; height: 100%;'></div>
                        </div>
                        <span style='color: {color}; font-size: 0.75rem; font-weight: 600;'>{severity_ratio:.0f}% severe</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # INVESTIGATOR PERFORMANCE MATRIX (ENHANCED)
    # ========================================
    st.markdown('<div class="section-title">👮 Investigator Performance Analytics</div>', unsafe_allow_html=True)
    
    inv_performance = db.query("""
        MATCH (i:Investigator)<-[:INVESTIGATED_BY]-(c:Crime)
        WITH i,
             count(c) as total_cases,
             count(CASE WHEN c.status IN ['solved', 'closed'] THEN 1 END) as solved,
             count(CASE WHEN c.status = 'open' OR c.status = 'under investigation' THEN 1 END) as active,
             count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as high_severity
        RETURN i.name as investigator,
               i.department as department,
               total_cases,
               solved,
               active,
               high_severity,
               CASE WHEN total_cases > 0 THEN (solved * 100.0 / total_cases) ELSE 0 END as solve_rate
        ORDER BY solve_rate DESC, solved DESC
    """)
    
    if inv_performance:
        df_inv = pd.DataFrame(inv_performance)
        
        # Grouped bar chart showing solved vs active
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='✅ Solved',
            x=df_inv['investigator'],
            y=df_inv['solved'],
            marker=dict(color='#10b981'),
            text=df_inv['solved'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='🔄 Active',
            x=df_inv['investigator'],
            y=df_inv['active'],
            marker=dict(color='#f59e0b'),
            text=df_inv['active'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Scatter(
            name='Solve Rate %',
            x=df_inv['investigator'],
            y=df_inv['solve_rate'],
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#667eea', width=3),
            marker=dict(size=10, symbol='diamond')
        ))
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            xaxis_tickangle=-45,
            yaxis=dict(title='Cases'),
            yaxis2=dict(title='Solve Rate %', overlaying='y', side='right', range=[0, 100]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # WEAPON & EVIDENCE TRACKING (NEW!)
    # ========================================
    st.markdown('<div class="section-title">🔫 Weapons & Evidence Intelligence</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Weapon Distribution")
        
        weapon_data = db.query("""
            MATCH (w:Weapon)
            OPTIONAL MATCH (p:Person)-[:OWNS]->(w)
            OPTIONAL MATCH (c:Crime)-[:USED_WEAPON]->(w)
            WITH w.type as type,
                 count(DISTINCT w) as total,
                 count(DISTINCT p) as owners,
                 count(DISTINCT c) as used_in_crimes,
                 count(CASE WHEN w.recovered = true THEN 1 END) as recovered
            RETURN type, total, owners, used_in_crimes, recovered
            ORDER BY total DESC
        """)
        
        if weapon_data:
            df_weapons = pd.DataFrame(weapon_data)
            
            # Stacked bar for weapons
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Recovered',
                x=df_weapons['type'],
                y=df_weapons['recovered'],
                marker=dict(color='#10b981')
            ))
            
            fig.add_trace(go.Bar(
                name='At Large',
                x=df_weapons['type'],
                y=df_weapons['total'] - df_weapons['recovered'],
                marker=dict(color='#ef4444')
            ))
            
            fig.update_layout(
                barmode='stack',
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_title="Weapon Type",
                yaxis_title="Count",
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Evidence by Significance")
        
        evidence_data = db.query("""
            MATCH (e:Evidence)
            OPTIONAL MATCH (e)-[:LINKS_TO]->(p:Person)
            WITH e.significance as significance,
                 count(DISTINCT e) as total,
                 count(DISTINCT p) as linked_suspects,
                 count(CASE WHEN e.verified = true THEN 1 END) as verified
            RETURN significance, total, linked_suspects, verified
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
            
            # Radar chart for evidence
            categories = df_evidence['significance'].tolist()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=df_evidence['total'],
                theta=categories,
                fill='toself',
                name='Total Evidence',
                fillcolor='rgba(102, 126, 234, 0.3)',
                line=dict(color='#667eea', width=2)
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=df_evidence['verified'],
                theta=categories,
                fill='toself',
                name='Verified',
                fillcolor='rgba(16, 185, 129, 0.3)',
                line=dict(color='#10b981', width=2)
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        gridcolor='rgba(255,255,255,0.1)',
                        tickfont=dict(color='#e2e8f0')
                    ),
                    angularaxis=dict(
                        gridcolor='rgba(255,255,255,0.1)',
                        tickfont=dict(color='#e2e8f0')
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=-0.15)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # REAL-TIME ACTIVITY FEED (NEW!)
    # ========================================
    st.markdown('<div class="section-title">🚨 Recent Activity Feed</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Latest 24-Hour Activity")
        
        recent_activity = db.query("""
            MATCH (c:Crime)
            OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
            OPTIONAL MATCH (p:Person)-[:PARTY_TO]->(c)
            RETURN c.id as id,
                   c.type as type,
                   c.date as date,
                   c.time as time,
                   c.severity as severity,
                   c.status as status,
                   COALESCE(l.name, 'Unknown') as location,
                   COALESCE(l.district, 'N/A') as district,
                   collect(DISTINCT p.name)[0] as primary_suspect
            ORDER BY c.date DESC, c.time DESC
            LIMIT 10
        """)
        
        if recent_activity:
            for activity in recent_activity:
                severity = activity['severity']
                
                if severity in ['critical', 'severe']:
                    border_color = '#dc2626'
                    icon = '🚨'
                elif severity in ['high']:
                    border_color = '#f59e0b'
                    icon = '⚠️'
                else:
                    border_color = '#3b82f6'
                    icon = '📍'
                
                suspect_info = f"Suspect: {activity['primary_suspect']}" if activity['primary_suspect'] else "No suspects"
                
                st.markdown(f"""
                <div class='glass-card' style='border-left: 4px solid {border_color}; padding: 14px; margin: 8px 0;'>
                    <div style='display: flex; justify-content: between; align-items: start;'>
                        <div style='flex: 1;'>
                            <div style='font-size: 1.05rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;'>
                                {icon} {activity['type']}
                            </div>
                            <div style='color: #a0aec0; font-size: 0.85rem; line-height: 1.6;'>
                                📅 {activity['date']} at {activity['time']}<br/>
                                📍 {activity['location'][:50]}<br/>
                                🏛️ District {activity['district']} • {suspect_info}
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: rgba(102, 126, 234, 0.2); padding: 4px 10px; border-radius: 12px; 
                                        font-size: 0.75rem; font-weight: 600; color: #a5b4fc;'>
                                {activity['status'].upper()}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Quick Stats")
        
        # Today's stats (if data supports it)
        today_stats = db.query("""
            MATCH (c:Crime)
            WHERE c.date >= '2024-01-01'
            WITH count(c) as today_total,
                 count(CASE WHEN c.severity IN ['high', 'critical', 'severe'] THEN 1 END) as today_severe
            RETURN today_total, today_severe
        """)
        
        if today_stats:
            data = today_stats[0]
            
            st.metric("📊 Recent Cases", data['today_total'])
            st.metric("⚠️ Severe Cases", data['today_severe'], delta_color="inverse")
            
            # Most active hour
            active_hour = db.query("""
                MATCH (c:Crime)
                WHERE c.time IS NOT NULL
                WITH substring(c.time, 0, 2) as hour, count(c) as crimes
                ORDER BY crimes DESC
                LIMIT 1
            """)
            
            if active_hour and active_hour[0]['hour']:
                peak_hour = active_hour[0]['hour']
                st.metric("🕐 Peak Hour", f"{peak_hour}:00", delta=f"Most active")
        
        st.markdown("---")
        
        # Quick action buttons
        st.markdown("#### Quick Actions")
        
        if st.button("🔍 Analyze Trends", use_container_width=True):
            st.session_state.page = 'Timeline Analysis'
            st.rerun()
        
        if st.button("🗺️ View Hotspots", use_container_width=True):
            st.session_state.page = 'Geographic Mapping'
            st.rerun()
        
        if st.button("🕸️ Network Analysis", use_container_width=True):
            st.session_state.page = 'Network Visualization'
            st.rerun()