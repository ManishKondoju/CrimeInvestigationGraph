"""
Enhanced Timeline Visualization - Better Styling & Readable Charts
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st


class TimelineVisualizer:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def get_crime_timeline_data(self, start_date=None, end_date=None, crime_types=None, locations=None, severity=None):
        query = """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        OPTIONAL MATCH (c)<-[:PARTY_TO]-(p:Person)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
        WHERE 1=1
        """
        
        if start_date:
            query += f" AND c.date >= date('{start_date}')"
        if end_date:
            query += f" AND c.date <= date('{end_date}')"
        if crime_types:
            types_str = "', '".join(crime_types)
            query += f" AND c.type IN ['{types_str}']"
        if locations:
            locs_str = "', '".join(locations)
            query += f" AND l.name IN ['{locs_str}']"
        if severity:
            sev_str = "', '".join(severity)
            query += f" AND c.severity IN ['{sev_str}']"
        
        query += """
        RETURN 
            c.id as crime_id,
            c.type as crime_type,
            c.date as date,
            c.time as time,
            c.severity as severity,
            c.status as status,
            l.name as location,
            collect(DISTINCT p.name) as suspects,
            collect(DISTINCT o.name) as organizations
        ORDER BY c.date, c.time
        """
        
        results = self.db.query(query)
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce')
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        df['week'] = df['datetime'].dt.isocalendar().week
        df['month'] = df['datetime'].dt.month
        df['date_only'] = df['datetime'].dt.date
        
        return df
    
    def create_daily_timeline(self, df):
        """Weekly crime timeline - visible bars instead of 600+ tiny ones"""
        
        if df.empty:
            return go.Figure()
        
        # Group by WEEK instead of day
        df['week_start'] = df['datetime'].dt.to_period('W').dt.start_time
        weekly = df.groupby(['week_start', 'severity']).size().reset_index(name='count')
        
        fig = go.Figure()
        
        severity_colors = {
            'critical': '#DC2626',
            'high': '#F97316',
            'medium': '#EAB308',
            'low': '#10B981'
        }
        
        for severity in ['low', 'medium', 'high', 'critical']:
            sev_data = weekly[weekly['severity'] == severity]
            if not sev_data.empty:
                fig.add_trace(go.Bar(
                    x=sev_data['week_start'],
                    y=sev_data['count'],
                    name=severity.title(),
                    marker=dict(color=severity_colors[severity]),
                    text=sev_data['count'],
                    textfont=dict(size=11, color='#0f172a', family='Arial Black'),
                    textposition='inside',
                    hovertemplate='<b>Week of %{x|%b %d}</b><br>%{y} crimes<extra></extra>'
                ))
        
        fig.update_layout(
            title=dict(text='<b>Weekly Crime Timeline by Severity</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Week</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Crime Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569'),
                range=[0, 20]  # Max 20 for better visibility
            ),
            barmode='stack',
            bargap=0.2,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            height=500,
            margin=dict(l=70, r=40, t=80, b=70),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, color='#1e293b')
            ),
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_advanced_heatmap(self, df):
        """Enhanced heatmap with readable text"""
        
        if df.empty:
            return go.Figure()
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        pivot = pivot.reindex(day_order)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}:00" for h in pivot.columns],
            y=pivot.index,
            colorscale='RdYlBu_r',
            text=pivot.values,
            texttemplate='<b>%{text:.0f}</b>',
            textfont=dict(size=11, color='#0f172a'),
            hovertemplate='<b>%{y}</b><br>%{x}<br><b>%{z} crimes</b><extra></extra>',
            colorbar=dict(
                title=dict(text='<b>Crimes</b>', font=dict(size=12, color='#1e293b')),
                tickfont=dict(size=11, color='#1e293b')
            )
        ))
        
        fig.update_layout(
            title=dict(text='<b>Activity Heatmap - Day × Hour</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Hour of Day</b>', font=dict(size=14, color='#1e293b')),
                tickfont=dict(size=11, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Day of Week</b>', font=dict(size=14, color='#1e293b')),
                tickfont=dict(size=12, color='#475569')
            ),
            height=400,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            margin=dict(l=100, r=140, t=80, b=70),
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_hourly_bars(self, df):
        """24-hour bar chart with peak highlighting"""
        
        if df.empty:
            return go.Figure()
        
        hourly = df.groupby('hour').size().reset_index(name='crimes')
        hourly = hourly.sort_values('hour')
        
        # Highlight peak hours
        peak_threshold = hourly['crimes'].quantile(0.75)
        colors = ['#DC2626' if c >= peak_threshold else '#3B82F6' for c in hourly['crimes']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=hourly['hour'],
            y=hourly['crimes'],
            marker=dict(color=colors, line=dict(color='#1e293b', width=1)),
            text=hourly['crimes'],
            textposition='outside',
            textfont=dict(size=12, color='#0f172a', family='Arial Black'),
            hovertemplate='<b>Hour %{x}:00</b><br>%{y} crimes<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text='<b>Hourly Distribution - Peak Hours in Red</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Hour of Day</b>', font=dict(size=14, color='#1e293b')),
                tickmode='linear',
                tick0=0,
                dtick=2,
                tickfont=dict(size=11, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Crime Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            height=400,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            margin=dict(l=70, r=40, t=80, b=70),
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_cumulative_area(self, df):
        """Cumulative growth by severity"""
        
        if df.empty:
            return go.Figure()
        
        df_sorted = df.sort_values('datetime')
        
        fig = go.Figure()
        
        colors = {
            'critical': '#DC2626',
            'high': '#F97316', 
            'medium': '#EAB308',
            'low': '#10B981'
        }
        
        for severity in ['low', 'medium', 'high', 'critical']:
            sev_df = df_sorted[df_sorted['severity'] == severity].copy()
            if not sev_df.empty:
                sev_df = sev_df.sort_values('datetime')
                sev_df['cumulative'] = range(1, len(sev_df) + 1)
                
                fig.add_trace(go.Scatter(
                    x=sev_df['datetime'],
                    y=sev_df['cumulative'],
                    name=severity.title(),
                    mode='lines',
                    line=dict(width=2, color=colors[severity]),
                    fill='tonexty' if severity != 'low' else 'tozeroy',
                    stackgroup='one',
                    hovertemplate='<b>%{y}</b> crimes<extra></extra>'
                ))
        
        fig.update_layout(
            title=dict(text='<b>Cumulative Crime Growth by Severity</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Date</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Cumulative Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            height=450,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            hovermode='x unified',
            margin=dict(l=70, r=40, t=80, b=70),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, color='#1e293b')
            ),
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_weekly_combo(self, df):
        """Weekly bars with trend line"""
        
        if df.empty:
            return go.Figure()
        
        weekly = df.groupby('week').size().reset_index(name='crimes')
        weekly = weekly.sort_values('week')
        weekly['week_label'] = 'W' + weekly['week'].astype(str)
        
        # Calculate trend
        if len(weekly) >= 3:
            weekly['trend'] = weekly['crimes'].rolling(window=3, center=True).mean()
        else:
            weekly['trend'] = weekly['crimes']
        
        fig = go.Figure()
        
        # Bars
        fig.add_trace(go.Bar(
            x=weekly['week_label'],
            y=weekly['crimes'],
            name='Weekly Crimes',
            marker=dict(
                color='#3B82F6',
                line=dict(color='#1e293b', width=1)
            ),
            text=weekly['crimes'],
            textposition='outside',
            textfont=dict(size=11, color='#0f172a', family='Arial Black')
        ))
        
        # Trend line
        fig.add_trace(go.Scatter(
            x=weekly['week_label'],
            y=weekly['trend'],
            name='Trend',
            mode='lines+markers',
            line=dict(color='#DC2626', width=4),
            marker=dict(size=8, color='#DC2626', line=dict(color='white', width=2))
        ))
        
        fig.update_layout(
            title=dict(text='<b>Weekly Crime Volume & Trend</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Week</b>', font=dict(size=14, color='#1e293b')),
                tickangle=-45,
                tickfont=dict(size=10, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Crime Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            height=450,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            margin=dict(l=70, r=40, t=80, b=100),
            legend=dict(
                orientation='h',
                yanchor='top',
                y=-0.2,
                xanchor='center',
                x=0.5,
                font=dict(size=12, color='#1e293b')
            ),
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_severity_breakdown(self, df):
        """Severity counts with percentages"""
        
        if df.empty:
            return go.Figure()
        
        severity_counts = df['severity'].value_counts().reindex(['critical', 'high', 'medium', 'low'], fill_value=0)
        severity_pcts = (severity_counts / len(df) * 100).round(1)
        
        colors = ['#DC2626', '#F97316', '#EAB308', '#10B981']
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=severity_counts.index,
            y=severity_counts.values,
            marker=dict(
                color=colors,
                line=dict(color='#1e293b', width=2)
            ),
            text=[f'<b>{count}</b><br>({pct}%)' for count, pct in zip(severity_counts.values, severity_pcts.values)],
            textposition='outside',
            textfont=dict(size=13, color='#0f172a', family='Arial Black'),
            hovertemplate='<b>%{x}</b><br>%{y} crimes<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text='<b>Crime Severity Distribution</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Severity Level</b>', font=dict(size=14, color='#1e293b')),
                tickfont=dict(size=13, color='#475569')
            ),
            yaxis=dict(
                title=dict(text='<b>Crime Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            height=400,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            margin=dict(l=70, r=40, t=80, b=70),
            showlegend=False,
            font=dict(color='#1e293b')
        )
        
        return fig
    
    def create_crime_type_chart(self, df):
        """Top crime types horizontal bars"""
        
        if df.empty:
            return go.Figure()
        
        type_counts = df['crime_type'].value_counts().head(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=type_counts.index,
            x=type_counts.values,
            orientation='h',
            marker=dict(
                color=type_counts.values,
                colorscale='Turbo',
                showscale=True,
                colorbar=dict(
                    title=dict(text='<b>Count</b>', font=dict(size=12, color='#1e293b')),
                    tickfont=dict(color='#1e293b')
                ),
                line=dict(color='#1e293b', width=1)
            ),
            text=type_counts.values,
            textposition='outside',
            textfont=dict(size=13, color='#0f172a', family='Arial Black'),
            hovertemplate='<b>%{y}</b><br>%{x} crimes<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text='<b>Top 10 Crime Types</b>', font=dict(size=22, color='#0f172a')),
            xaxis=dict(
                title=dict(text='<b>Crime Count</b>', font=dict(size=14, color='#1e293b')),
                showgrid=True,
                gridcolor='#e5e7eb',
                tickfont=dict(size=11, color='#475569')
            ),
            yaxis=dict(
                title='',
                tickfont=dict(size=12, color='#1e293b')
            ),
            height=500,
            plot_bgcolor='#f8fafc',
            paper_bgcolor='white',
            margin=dict(l=220, r=140, t=80, b=70),
            showlegend=False,
            font=dict(color='#1e293b')
        )
        
        return fig


def render_timeline_interface(db_connection):
    """Render enhanced timeline interface"""
    
    st.markdown("## ⏱️ Timeline Analysis")
    st.markdown("Temporal crime patterns and trends")
    
    viz = TimelineVisualizer(db_connection)
    
    # Filters
    with st.expander("🎛️ Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            crime_types_result = db_connection.query("MATCH (c:Crime) RETURN DISTINCT c.type as type ORDER BY type")
            crime_types_available = [r['type'] for r in crime_types_result] if crime_types_result else []
            selected_crime_types = st.multiselect("Crime Types", crime_types_available)
        
        with col2:
            severity_filter = st.multiselect("Severity", ['critical', 'high', 'medium', 'low'])
        
        with col3:
            locations_result = db_connection.query("MATCH (l:Location) RETURN DISTINCT l.name as name ORDER BY name LIMIT 50")
            locations_available = [r['name'] for r in locations_result] if locations_result else []
            selected_locations = st.multiselect("Locations", locations_available)
    
    # Fetch data
    with st.spinner("Loading timeline..."):
        df = viz.get_crime_timeline_data(
            crime_types=selected_crime_types if selected_crime_types else None,
            severity=severity_filter if severity_filter else None,
            locations=selected_locations if selected_locations else None
        )
    
    if df.empty:
        st.warning("No data available. Load database first.")
        return
    
    # Key metrics
    st.markdown("### 📊 Temporal Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak_hour = df['hour'].mode()[0] if not df.empty else 0
        count_at_peak = len(df[df['hour'] == peak_hour])
        st.metric("Peak Hour", f"{peak_hour:02d}:00", f"{count_at_peak} crimes")
    
    with col2:
        peak_day = df['day_of_week'].mode()[0] if not df.empty else "Unknown"
        count_on_peak = len(df[df['day_of_week'] == peak_day])
        st.metric("Busiest Day", peak_day, f"{count_on_peak} crimes")
    
    with col3:
        date_range = (df['datetime'].max() - df['datetime'].min()).days
        st.metric("Time Span", f"{date_range} days", f"{len(df)} total")
    
    with col4:
        avg_daily = len(df) / date_range if date_range > 0 else 0
        st.metric("Daily Avg", f"{avg_daily:.1f}", "crimes/day")
    
    st.markdown("---")
    
    # Tabbed views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Weekly Timeline", 
        "🔥 Heatmap Analysis", 
        "📈 Weekly Trends",
        "📊 Crime Breakdown"
    ])
    
    with tab1:
        st.plotly_chart(viz.create_daily_timeline(df), use_container_width=True)
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            critical = len(df[df['severity'] == 'critical'])
            st.metric("Critical Crimes", critical, f"{critical/len(df)*100:.1f}%")
        with col2:
            solved = len(df[df['status'] == 'solved'])
            st.metric("Solved Cases", solved, f"{solved/len(df)*100:.1f}%")
        with col3:
            active = len(df[df['status'] == 'active'])
            st.metric("Active Cases", active, f"{active/len(df)*100:.1f}%")
    
    with tab2:
        st.plotly_chart(viz.create_advanced_heatmap(df), use_container_width=True)
        st.plotly_chart(viz.create_hourly_bars(df), use_container_width=True)
        
        # Peak insights
        peak_hour = df['hour'].mode()[0]
        peak_day = df['day_of_week'].mode()[0]
        peak_combo = len(df[(df['hour'] == peak_hour) & (df['day_of_week'] == peak_day)])
        
        st.info(f"🔥 **Peak Activity:** {peak_day}s at {peak_hour:02d}:00 with **{peak_combo} crimes**")
        
        # Find dangerous hours
        hourly = df.groupby('hour').size()
        dangerous_hours = hourly[hourly >= hourly.quantile(0.75)].index.tolist()
        st.warning(f"⚠️ **High-Risk Hours:** {', '.join([f'{h:02d}:00' for h in dangerous_hours])}")
    
    with tab3:
        st.plotly_chart(viz.create_weekly_combo(df), use_container_width=True)
        
        # Weekly insights
        weekly = df.groupby('week').size()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Weekly", f"{weekly.mean():.1f}", "crimes/week")
        with col2:
            st.metric("Peak Week", f"Week {weekly.idxmax()}", f"{weekly.max()} crimes")
        with col3:
            st.metric("Quietest Week", f"Week {weekly.idxmin()}", f"{weekly.min()} crimes")
        
        # Trend analysis
        first_half = weekly[:len(weekly)//2].mean()
        second_half = weekly[len(weekly)//2:].mean()
        trend = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if trend > 10:
            st.error(f"📈 **Crime Trend:** Increasing by {trend:.1f}% in recent weeks")
        elif trend < -10:
            st.success(f"📉 **Crime Trend:** Decreasing by {abs(trend):.1f}% in recent weeks")
        else:
            st.info(f"➡️ **Crime Trend:** Stable (±{abs(trend):.1f}%)")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(viz.create_severity_breakdown(df), use_container_width=True)
            
            # Severity stats
            severity_counts = df['severity'].value_counts()
            total = len(df)
            
            st.markdown("**Severity Breakdown:**")
            for sev in ['critical', 'high', 'medium', 'low']:
                count = severity_counts.get(sev, 0)
                pct = count / total * 100
                
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                st.markdown(f"{emoji.get(sev)} **{sev.title()}:** {count} crimes ({pct:.1f}%)")
        
        with col2:
            st.plotly_chart(viz.create_crime_type_chart(df), use_container_width=True)
            
            # Top types percentage
            top_3 = df['crime_type'].value_counts().head(3)
            top_3_total = top_3.sum()
            top_3_pct = top_3_total / len(df) * 100
            
            st.info(f"📊 **Top 3 Types:** {top_3_total} crimes ({top_3_pct:.1f}% of total)")


if __name__ == "__main__":
    from database import Database
    st.set_page_config(layout="wide")
    db = Database()
    render_timeline_interface(db)