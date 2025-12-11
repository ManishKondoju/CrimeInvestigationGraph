"""
Timeline Visualization Module for CrimeGraphRAG
Provides interactive timeline views for crime investigation analysis
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import streamlit as st


class TimelineVisualizer:
    """
    Creates interactive timeline visualizations for crime investigation data
    """
    
    def __init__(self, db_connection):
        """
        Initialize timeline visualizer with database connection
        
        Args:
            db_connection: Neo4j database connection object
        """
        self.db = db_connection
        
    def get_crime_timeline_data(self, 
                                start_date: str = None, 
                                end_date: str = None,
                                crime_types: List[str] = None,
                                locations: List[str] = None,
                                severity: List[str] = None) -> pd.DataFrame:
        """
        Fetch crime events with temporal data from Neo4j
        
        Args:
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            crime_types: List of crime types to include
            locations: List of locations to filter
            severity: List of severity levels
            
        Returns:
            DataFrame with crime timeline data
        """
        query = """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        OPTIONAL MATCH (c)<-[:PARTY_TO]-(p:Person)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
        WHERE 1=1
        """
        
        # Add filters by building query string
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
            c.case_number as case_number,
            l.name as location,
            collect(DISTINCT p.name) as suspects,
            collect(DISTINCT o.name) as organizations
        ORDER BY c.date, c.time
        """
        
        try:
            results = self.db.query(query)
            
            if not results:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Combine date and time
            df['datetime'] = pd.to_datetime(
                df['date'].astype(str) + ' ' + df['time'].astype(str),
                errors='coerce'
            )
            
            # Handle cases where time might be missing
            df['datetime'] = df['datetime'].fillna(pd.to_datetime(df['date']))
            
            return df
        except Exception as e:
            st.error(f"Error fetching crime timeline data: {e}")
            return pd.DataFrame()
    
    def get_investigation_timeline_data(self) -> pd.DataFrame:
        """
        Fetch investigation progress events (case status changes, evidence collection)
        
        Returns:
            DataFrame with investigation timeline data
        """
        query = """
        MATCH (c:Crime)
        OPTIONAL MATCH (c)-[:INVESTIGATED_BY]->(i:Investigator)
        OPTIONAL MATCH (c)-[:HAS_EVIDENCE]->(e:Evidence)
        RETURN 
            c.id as crime_id,
            c.case_number as case_number,
            c.date as crime_date,
            c.status as current_status,
            c.type as crime_type,
            i.name as investigator,
            collect(DISTINCT e.type) as evidence_types,
            count(DISTINCT e) as evidence_count
        ORDER BY c.date DESC
        """
        
        try:
            results = self.db.query(query)
            
            if not results:
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            df['crime_date'] = pd.to_datetime(df['crime_date'], errors='coerce')
            
            return df
        except Exception as e:
            st.error(f"Error fetching investigation data: {e}")
            return pd.DataFrame()
    
    def get_gang_activity_timeline(self, organization: str = None) -> pd.DataFrame:
        """
        Fetch gang-related activity over time
        
        Args:
            organization: Specific gang/organization name to filter
            
        Returns:
            DataFrame with gang activity timeline
        """
        query = """
        MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)-[:PARTY_TO]->(c:Crime)
        WHERE 1=1
        """
        
        if organization:
            query += f" AND o.name = '{organization}'"
        
        query += """
        RETURN 
            o.name as organization,
            o.type as org_type,
            c.date as date,
            c.type as crime_type,
            c.severity as severity,
            p.name as member,
            c.case_number as case_number
        ORDER BY c.date
        """
        
        try:
            results = self.db.query(query)
            
            if not results:
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            return df
        except Exception as e:
            st.error(f"Error fetching gang activity data: {e}")
            return pd.DataFrame()
    
    def create_crime_timeline(self, df: pd.DataFrame, title: str = "Crime Timeline") -> go.Figure:
        """
        Create interactive crime timeline visualization
        
        Args:
            df: DataFrame with crime timeline data
            title: Chart title
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Color mapping for severity
        severity_colors = {
            'low': '#2ecc71',      # green
            'medium': '#f39c12',   # orange
            'high': '#e74c3c',     # red
            'critical': '#8e44ad'  # purple
        }
        
        # Color mapping for crime types
        crime_type_colors = px.colors.qualitative.Set3
        unique_types = df['crime_type'].unique()
        type_color_map = {crime_type: crime_type_colors[i % len(crime_type_colors)] 
                         for i, crime_type in enumerate(unique_types)}
        
        fig = go.Figure()
        
        # Add traces for each crime type
        for crime_type in unique_types:
            df_type = df[df['crime_type'] == crime_type]
            
            hover_text = []
            for _, row in df_type.iterrows():
                suspects_str = ', '.join(row['suspects']) if row['suspects'] else 'Unknown'
                orgs_str = ', '.join(row['organizations']) if row['organizations'] else 'None'
                
                text = (f"<b>{row['crime_type']}</b><br>"
                       f"Case: {row['case_number']}<br>"
                       f"Location: {row['location']}<br>"
                       f"Severity: {row['severity']}<br>"
                       f"Status: {row['status']}<br>"
                       f"Suspects: {suspects_str}<br>"
                       f"Organizations: {orgs_str}")
                hover_text.append(text)
            
            fig.add_trace(go.Scatter(
                x=df_type['datetime'],
                y=df_type['crime_type'],
                mode='markers',
                name=crime_type,
                marker=dict(
                    size=12,
                    color=[severity_colors.get(s.lower(), '#95a5a6') 
                          for s in df_type['severity']],
                    line=dict(width=2, color='white'),
                    symbol='circle'
                ),
                text=hover_text,
                hovertemplate='%{text}<extra></extra>',
                showlegend=True
            ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20)),
            xaxis_title="Date/Time",
            yaxis_title="Crime Type",
            height=600,
            hovermode='closest',
            plot_bgcolor='rgba(240,240,240,0.5)',
            xaxis=dict(
                showgrid=True,
                gridcolor='white',
                gridwidth=1
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='white',
                gridwidth=1
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        return fig
    
    def create_activity_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """
        Create temporal heatmap showing crime frequency by day/hour
        
        Args:
            df: DataFrame with crime timeline data
            
        Returns:
            Plotly figure object
        """
        if df.empty or 'datetime' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No temporal data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Extract hour and day of week
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        
        # Create pivot table
        heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        
        # Order days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        heatmap_pivot = heatmap_pivot.reindex(day_order)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Reds',
            hovertemplate='Day: %{y}<br>Hour: %{x}<br>Crimes: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Crime Activity Heatmap by Day and Hour',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            height=400
        )
        
        return fig
    
    def create_gang_activity_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        Create timeline showing gang activity evolution
        
        Args:
            df: DataFrame with gang activity data
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No gang activity data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Aggregate by organization and month
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        activity_by_org = df.groupby(['year_month', 'organization']).size().reset_index(name='crime_count')
        
        fig = go.Figure()
        
        for org in activity_by_org['organization'].unique():
            org_data = activity_by_org[activity_by_org['organization'] == org]
            
            fig.add_trace(go.Scatter(
                x=org_data['year_month'],
                y=org_data['crime_count'],
                mode='lines+markers',
                name=org,
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title='Gang Activity Over Time',
            xaxis_title='Month',
            yaxis_title='Number of Crimes',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_investigation_progress_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        Create chart showing investigation progress and case status
        
        Args:
            df: DataFrame with investigation data
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No investigation data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Status breakdown over time
        df['year_month'] = df['crime_date'].dt.to_period('M').astype(str)
        status_over_time = df.groupby(['year_month', 'current_status']).size().reset_index(name='count')
        
        fig = go.Figure()
        
        status_colors = {
            'open': '#3498db',
            'under investigation': '#f39c12',
            'closed': '#2ecc71',
            'solved': '#2ecc71',
            'cold case': '#95a5a6'
        }
        
        for status in status_over_time['current_status'].unique():
            status_data = status_over_time[status_over_time['current_status'] == status]
            
            fig.add_trace(go.Bar(
                x=status_data['year_month'],
                y=status_data['count'],
                name=status.title(),
                marker_color=status_colors.get(status.lower(), '#34495e')
            ))
        
        fig.update_layout(
            title='Investigation Status Over Time',
            xaxis_title='Month',
            yaxis_title='Number of Cases',
            barmode='stack',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_crime_severity_timeline(self, df: pd.DataFrame) -> go.Figure:
        """
        Create stacked area chart showing severity trends over time
        
        Args:
            df: DataFrame with crime timeline data
            
        Returns:
            Plotly figure object
        """
        if df.empty or 'datetime' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Aggregate by date and severity
        df['date_only'] = df['datetime'].dt.date
        severity_by_date = df.groupby(['date_only', 'severity']).size().reset_index(name='count')
        severity_by_date['date_only'] = pd.to_datetime(severity_by_date['date_only'])
        
        fig = go.Figure()
        
        severity_order = ['low', 'medium', 'high', 'critical']
        severity_colors = {
            'low': '#2ecc71',
            'medium': '#f39c12',
            'high': '#e74c3c',
            'critical': '#8e44ad'
        }
        
        for severity in severity_order:
            if severity in severity_by_date['severity'].values:
                severity_data = severity_by_date[severity_by_date['severity'] == severity]
                
                fig.add_trace(go.Scatter(
                    x=severity_data['date_only'],
                    y=severity_data['count'],
                    mode='lines',
                    name=severity.title(),
                    fill='tonexty' if severity != 'low' else 'tozeroy',
                    line=dict(width=0.5),
                    fillcolor=severity_colors.get(severity, '#95a5a6')
                ))
        
        fig.update_layout(
            title='Crime Severity Trends Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Crimes',
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        return fig


def render_timeline_interface(db_connection):
    """
    Render the complete timeline visualization interface in Streamlit
    
    Args:
        db_connection: Neo4j database connection
    """
    st.header("⏱️ Timeline Analysis")
    st.markdown("Explore crime patterns and investigation progress over time")
    
    # Initialize visualizer
    viz = TimelineVisualizer(db_connection)
    
    # Sidebar filters
    st.sidebar.subheader("Timeline Filters")
    
    # Date range
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)
    
    # Get available options from database
    try:
        locations_query = "MATCH (l:Location) RETURN l.name as name ORDER BY name"
        locations_result = db_connection.query(locations_query)
        available_locations = [r['name'] for r in locations_result] if locations_result else []
        
        crime_types_query = "MATCH (c:Crime) RETURN DISTINCT c.type as type ORDER BY type"
        crime_types_result = db_connection.query(crime_types_query)
        available_crime_types = [r['type'] for r in crime_types_result] if crime_types_result else []
    except Exception as e:
        st.error(f"Error loading filter options: {e}")
        available_locations = []
        available_crime_types = []
    
    # Filters
    selected_locations = st.sidebar.multiselect("Locations", available_locations)
    selected_crime_types = st.sidebar.multiselect("Crime Types", available_crime_types)
    selected_severity = st.sidebar.multiselect("Severity", ["low", "medium", "high", "critical"])
    
    # Timeline view tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Crime Events",
        "🔥 Activity Heatmap", 
        "👥 Gang Activity",
        "📊 Investigation Progress"
    ])
    
    with tab1:
        st.subheader("Crime Events Timeline")
        st.markdown("Interactive timeline of all crime incidents with filtering")
        
        # Fetch data
        df_crimes = viz.get_crime_timeline_data(
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None,
            crime_types=selected_crime_types if selected_crime_types else None,
            locations=selected_locations if selected_locations else None,
            severity=selected_severity if selected_severity else None
        )
        
        if not df_crimes.empty:
            # Show statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Crimes", len(df_crimes))
            with col2:
                st.metric("Crime Types", df_crimes['crime_type'].nunique())
            with col3:
                st.metric("Locations", df_crimes['location'].nunique())
            with col4:
                high_severity = len(df_crimes[df_crimes['severity'].isin(['high', 'critical'])])
                st.metric("High Severity", high_severity)
            
            # Timeline chart
            fig_timeline = viz.create_crime_timeline(df_crimes)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Severity trends
            fig_severity = viz.create_crime_severity_timeline(df_crimes)
            st.plotly_chart(fig_severity, use_container_width=True)
            
            # Show data table
            with st.expander("📋 View Crime Data Table"):
                display_df = df_crimes[['case_number', 'crime_type', 'date', 'time', 
                                       'location', 'severity', 'status']].copy()
                st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info("No crime data found for selected filters. Try adjusting your filters.")
    
    with tab2:
        st.subheader("Crime Activity Heatmap")
        st.markdown("Identify peak crime hours and days")
        
        df_crimes = viz.get_crime_timeline_data(
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None,
            crime_types=selected_crime_types if selected_crime_types else None,
            locations=selected_locations if selected_locations else None,
            severity=selected_severity if selected_severity else None
        )
        
        if not df_crimes.empty:
            fig_heatmap = viz.create_activity_heatmap(df_crimes)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Insights
            st.markdown("### 🔍 Insights")
            if 'datetime' in df_crimes.columns:
                peak_hour = df_crimes['datetime'].dt.hour.mode()[0]
                peak_day = df_crimes['datetime'].dt.day_name().mode()[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Peak Hour:** {peak_hour}:00 - {peak_hour+1}:00")
                with col2:
                    st.info(f"**Peak Day:** {peak_day}")
        else:
            st.info("No data available for heatmap. Try adjusting your filters.")
    
    with tab3:
        st.subheader("Gang Activity Timeline")
        st.markdown("Track criminal organization activity over time")
        
        # Get available organizations
        try:
            orgs_query = "MATCH (o:Organization) RETURN o.name as name ORDER BY name"
            orgs_result = db_connection.query(orgs_query)
            available_orgs = [r['name'] for r in orgs_result] if orgs_result else []
        except Exception as e:
            st.error(f"Error loading organizations: {e}")
            available_orgs = []
        
        selected_org = st.selectbox("Select Organization (leave blank for all)", 
                                    ["All"] + available_orgs)
        
        df_gang = viz.get_gang_activity_timeline(
            organization=None if selected_org == "All" else selected_org
        )
        
        if not df_gang.empty:
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Organizations", df_gang['organization'].nunique())
            with col2:
                st.metric("Total Incidents", len(df_gang))
            with col3:
                st.metric("Active Members", df_gang['member'].nunique())
            
            # Activity chart
            fig_gang = viz.create_gang_activity_chart(df_gang)
            st.plotly_chart(fig_gang, use_container_width=True)
            
            # Top members
            st.markdown("### 👤 Most Active Members")
            top_members = df_gang['member'].value_counts().head(5)
            for i, (member, count) in enumerate(top_members.items(), 1):
                st.markdown(f"{i}. **{member}** - {count} incidents")
        else:
            st.info("No gang activity data found. Try selecting a different organization.")
    
    with tab4:
        st.subheader("Investigation Progress")
        st.markdown("Track case status and investigation outcomes")
        
        df_investigation = viz.get_investigation_timeline_data()
        
        if not df_investigation.empty:
            # Status distribution
            status_counts = df_investigation['current_status'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cases", len(df_investigation))
            with col2:
                open_cases = status_counts.get('open', 0)
                st.metric("Open Cases", open_cases)
            with col3:
                closed_cases = status_counts.get('closed', 0) + status_counts.get('solved', 0)
                st.metric("Closed Cases", closed_cases)
            with col4:
                avg_evidence = df_investigation['evidence_count'].mean()
                st.metric("Avg Evidence/Case", f"{avg_evidence:.1f}")
            
            # Progress chart
            fig_progress = viz.create_investigation_progress_chart(df_investigation)
            st.plotly_chart(fig_progress, use_container_width=True)
            
            # Recent cases
            with st.expander("📋 Recent Cases"):
                recent_df = df_investigation.head(10)[['case_number', 'crime_type', 
                                                       'current_status', 'investigator', 
                                                       'evidence_count']]
                st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("No investigation data available.")