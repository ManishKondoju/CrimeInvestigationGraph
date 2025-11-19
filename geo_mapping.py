# geo_mapping.py - Geographic Crime Mapping for CrimeGraphRAG
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class CrimeGeographicMapper:
    """
    Geographic visualization component for CrimeGraphRAG system.
    Provides interactive maps with crime locations, heatmaps, hotspot analysis, and predictive analytics.
    """
    
    def __init__(self, db):
        """
        Initialize the geographic mapper.
        
        Args:
            db: Database instance with Neo4j driver
        """
        self.db = db
        self.chicago_center = {"lat": 41.8781, "lon": -87.6298}
        
    def get_crime_locations(self, 
                           crime_types: Optional[List[str]] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           districts: Optional[List[str]] = None,
                           limit: int = 5000) -> pd.DataFrame:
        """
        Query Neo4j for crime location data with filters.
        """
        query = """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
        """
        
        params = {"limit": limit}
        
        if crime_types:
            query += " AND c.type IN $crime_types"
            params["crime_types"] = crime_types
            
        if start_date:
            query += " AND c.date >= $start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND c.date <= $end_date"
            params["end_date"] = end_date
            
        if districts:
            query += " AND l.district IN $districts"
            params["districts"] = districts
        
        query += """
        RETURN 
            c.id as case_id,
            c.type as crime_type,
            c.description as description,
            c.date as date,
            c.time as time,
            c.severity as severity,
            c.status as status,
            c.arrest_made as arrest_made,
            l.latitude as latitude,
            l.longitude as longitude,
            l.name as location_name,
            l.district as district,
            l.beat as beat
        ORDER BY c.date DESC
        LIMIT $limit
        """
        
        try:
            records = self.db.query(query, params)
            df = pd.DataFrame(records)
            
            if not df.empty:
                df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
                df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
                df = df.dropna(subset=['latitude', 'longitude'])
                
                # Filter out invalid Chicago coordinates
                df = df[
                    (df['latitude'] >= 41.6) & (df['latitude'] <= 42.1) &
                    (df['longitude'] >= -87.9) & (df['longitude'] <= -87.5)
                ]
                
            return df
        except Exception as e:
            st.error(f"Error fetching crime locations: {e}")
            return pd.DataFrame()
    
    def predict_crime_hotspots(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Use DBSCAN clustering to predict future crime hotspots based on historical patterns.
        Returns DataFrame with predicted hotspot locations and risk scores.
        """
        if df.empty or len(df) < 20:
            return pd.DataFrame()
        
        try:
            from sklearn.cluster import DBSCAN
            
            coords = df[['latitude', 'longitude']].values
            
            # DBSCAN clustering
            clustering = DBSCAN(eps=0.005, min_samples=10).fit(coords)
            df['cluster'] = clustering.labels_
            
            # Calculate cluster statistics for prediction
            predictions = []
            
            for cluster_id in df['cluster'].unique():
                if cluster_id == -1:  # Skip noise
                    continue
                
                cluster_data = df[df['cluster'] == cluster_id]
                
                # Calculate risk metrics
                crime_count = len(cluster_data)
                severe_count = len(cluster_data[cluster_data['severity'] == 'severe'])
                arrest_rate = cluster_data['arrest_made'].mean() if 'arrest_made' in cluster_data.columns else 0
                
                # Risk score calculation (0-100)
                risk_score = min(100, (
                    (crime_count / 10) * 40 +  # Frequency weight
                    (severe_count / max(1, crime_count)) * 30 +  # Severity weight
                    (1 - arrest_rate) * 30  # Low arrest rate increases risk
                ))
                
                predictions.append({
                    'cluster_id': cluster_id,
                    'latitude': cluster_data['latitude'].mean(),
                    'longitude': cluster_data['longitude'].mean(),
                    'crime_count': crime_count,
                    'risk_score': round(risk_score, 1),
                    'risk_level': 'Critical' if risk_score >= 70 else 'High' if risk_score >= 50 else 'Medium' if risk_score >= 30 else 'Low',
                    'primary_crime': cluster_data['crime_type'].mode()[0] if len(cluster_data) > 0 else 'Unknown',
                    'district': cluster_data['district'].mode()[0] if len(cluster_data) > 0 else 'Unknown'
                })
            
            return pd.DataFrame(predictions)
            
        except ImportError:
            st.warning("⚠️ scikit-learn required for predictions. Install: pip install scikit-learn scipy")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error in prediction: {e}")
            return pd.DataFrame()
    
    def create_unified_map(self, df: pd.DataFrame, show_heatmap: bool = False, 
                          show_predictions: bool = False) -> go.Figure:
        """
        Create a unified map that can toggle between scatter, heatmap, and predictive overlays.
        """
        if df.empty:
            fig = go.Figure(go.Scattermapbox())
            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=self.chicago_center,
                    zoom=10
                ),
                title="No Crime Data Available",
                height=700,
                margin={"r": 0, "t": 50, "l": 0, "b": 0}
            )
            return fig
        
        fig = go.Figure()
        
        center_lat = df['latitude'].mean()
        center_lon = df['longitude'].mean()
        
        # LAYER 1: Heatmap (if enabled)
        if show_heatmap:
            fig.add_trace(go.Densitymapbox(
                lat=df['latitude'],
                lon=df['longitude'],
                radius=15,
                colorscale=[
                    [0, 'rgba(16, 185, 129, 0.4)'],      # Green (low)
                    [0.3, 'rgba(245, 158, 11, 0.5)'],    # Yellow
                    [0.6, 'rgba(239, 68, 68, 0.7)'],     # Orange  
                    [1, 'rgba(220, 38, 38, 0.9)']        # Red (high)
                ],
                showscale=True,
                hovertemplate='<b>Crime Density Zone</b><extra></extra>',
                colorbar=dict(
                    title="Density",
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='#d1d5db',
                    borderwidth=2,
                    x=1.02
                ),
                name='Crime Density',
                visible=True
            ))
        
        # LAYER 2: Crime Scatter Points (color by severity)
        severity_colors = {
            'severe': '#dc2626',    # Red
            'moderate': '#f59e0b',  # Orange
            'minor': '#10b981'      # Green
        }
        
        severity_sizes = {
            'severe': 18,
            'moderate': 14,
            'minor': 10
        }
        
        for severity in ['minor', 'moderate', 'severe']:
            df_severity = df[df['severity'] == severity]
            
            if not df_severity.empty:
                hover_text = df_severity.apply(
                    lambda row: (
                        f"<b>{row['crime_type']}</b><br>"
                        f"📅 {row['date']} {row.get('time', '')}<br>"
                        f"📍 {row['location_name'][:40]}<br>"
                        f"🚨 Severity: {row['severity'].title()}<br>"
                        f"🏛️ District: {row['district']}<br>"
                        f"{'✅ Arrest Made' if row.get('arrest_made') else '❌ No Arrest'}"
                    ),
                    axis=1
                )
                
                fig.add_trace(go.Scattermapbox(
                    lat=df_severity['latitude'],
                    lon=df_severity['longitude'],
                    mode='markers',
                    marker=dict(
                        size=severity_sizes[severity],
                        color=severity_colors[severity],
                        opacity=0.5 if show_heatmap else 0.6
                    ),
                    name=f'{severity.title()} ({len(df_severity)})',
                    text=hover_text,
                    hovertemplate='%{text}<extra></extra>',
                    visible=True
                ))
        
        # LAYER 3: Predictive Hotspots (if enabled)
        if show_predictions and len(df) >= 20:
            predictions = self.predict_crime_hotspots(df)
            
            if not predictions.empty:
                risk_colors = {
                    'Critical': '#dc2626',
                    'High': '#f59e0b', 
                    'Medium': '#3b82f6',
                    'Low': '#10b981'
                }
                
                for risk_level in ['Low', 'Medium', 'High', 'Critical']:
                    risk_data = predictions[predictions['risk_level'] == risk_level]
                    
                    if not risk_data.empty:
                        hover_text = risk_data.apply(
                            lambda row: (
                                f"<b>🎯 Predicted Hotspot</b><br>"
                                f"Risk Level: {row['risk_level']}<br>"
                                f"Risk Score: {row['risk_score']}/100<br>"
                                f"📊 Historical Crimes: {row['crime_count']}<br>"
                                f"🚨 Primary Type: {row['primary_crime']}<br>"
                                f"🏛️ District: {row['district']}"
                            ),
                            axis=1
                        )
                        
                        fig.add_trace(go.Scattermapbox(
                            lat=risk_data['latitude'],
                            lon=risk_data['longitude'],
                            mode='markers',
                            marker=dict(
                                size=risk_data['risk_score'] / 3,
                                color=risk_colors[risk_level],
                                opacity=0.8,
                                symbol='circle',
                                line=dict(width=3, color='white')
                            ),
                            name=f'🎯 {risk_level} Risk ({len(risk_data)})',
                            text=hover_text,
                            hovertemplate='%{text}<extra></extra>',
                            visible=True
                        ))
        
        # Map layout
        title_parts = [f"📍 Chicago Crime Map - {len(df):,} Incidents"]
        if show_heatmap:
            title_parts.append("🔥 Density Layer")
        if show_predictions:
            title_parts.append("🎯 Predictive Hotspots")
        
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11
            ),
            title={
                'text': " | ".join(title_parts),
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#1f2937'}
            },
            height=700,
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#d1d5db",
                borderwidth=2,
                font=dict(size=11, color='#1f2937')
            ),
            hovermode='closest'
        )
        
        return fig
    
    def render_map_interface(self):
        """
        Render the complete Streamlit interface for geographic mapping.
        """
        st.markdown("## 🗺️ Geographic Crime Analysis & Prediction")
        st.markdown("Interactive visualization and predictive analytics for crime patterns across Chicago")
        
        # Main controls at the top
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 🎛️ Visualization Controls")
        
        with col2:
            show_heatmap = st.toggle("🔥 Show Heatmap Layer", value=False, 
                                     help="Overlay crime density heatmap")
        
        with col3:
            show_predictions = st.toggle("🎯 Show Predictions", value=False,
                                        help="Show AI-predicted hotspots")
        
        st.markdown("---")
        
        # Sidebar filters
        with st.sidebar:
            st.markdown("### 🔍 Filter Options")
            
            # Date range filter
            use_date_filter = st.checkbox("📅 Filter by Date", value=False)
            
            start_date = None
            end_date = None
            
            if use_date_filter:
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("From", value=datetime(2024, 1, 1))
                with col2:
                    end_date = st.date_input("To", value=datetime.now())
                
                start_date = start_date.strftime("%Y-%m-%d")
                end_date = end_date.strftime("%Y-%m-%d")
            
            # Get available crime types
            try:
                crime_type_query = """
                MATCH (c:Crime)
                RETURN DISTINCT c.type as type
                ORDER BY type
                """
                crime_types_available = [r['type'] for r in self.db.query(crime_type_query) if r['type']]
            except:
                crime_types_available = []
            
            # Crime type filter
            crime_types = st.multiselect(
                "🚨 Crime Types",
                options=crime_types_available,
                help="Select specific crime types to analyze"
            )
            
            # Get available districts
            try:
                district_query = """
                MATCH (l:Location)
                WHERE l.district IS NOT NULL
                RETURN DISTINCT l.district as district
                ORDER BY district
                """
                districts_available = [str(r['district']) for r in self.db.query(district_query) if r['district']]
            except:
                districts_available = []
            
            # District filter
            districts = st.multiselect(
                "🏛️ Police Districts",
                options=districts_available,
                help="Filter by police district boundaries"
            )
            
            # Data limit
            data_limit = st.slider(
                "📊 Maximum Records",
                min_value=500,
                max_value=50000,
                value=10000,
                step=1000,
                help="Number of records to load (higher = more complete but slower)"
            )
            
            # Option to load ALL crimes
            load_all = st.checkbox("🌐 Load ALL Crimes", value=False, 
                                  help="⚠️ May be slow with large datasets")
            
            if load_all:
                st.warning("⚠️ Loading all crimes - this may take a moment")
            else:
                st.info(f"💡 Currently loading up to **{data_limit:,}** crime records")
            
            st.markdown("---")
            
            # Apply filters button
            apply_filters = st.button("🔄 Apply Filters", use_container_width=True, type="primary")
        
        # Load data
        if 'geo_data' not in st.session_state or apply_filters:
            with st.spinner("🔍 Loading crime data..."):
                # If load_all is checked, set limit to a very high number
                actual_limit = 999999 if load_all else data_limit
                
                st.session_state.geo_data = self.get_crime_locations(
                    crime_types=crime_types if crime_types else None,
                    start_date=start_date,
                    end_date=end_date,
                    districts=districts if districts else None,
                    limit=actual_limit
                )
        
        df = st.session_state.geo_data
        
        # Show data loading info
        if not df.empty:
            actual_limit_display = "ALL" if load_all else f"{data_limit:,}"
            
            if load_all:
                with st.sidebar:
                    st.success(f"✅ Loaded **{len(df):,}** total crimes with locations")
            elif len(df) < data_limit:
                with st.sidebar:
                    st.info(f"ℹ️ Loaded {len(df):,} of {data_limit:,} requested")
                    st.caption("Reasons for fewer records:")
                    st.caption("• Active filters applied")
                    st.caption("• Missing GPS coordinates")
                    st.caption("• Invalid location data")
                    st.caption("")
                    st.caption("💡 Check '🌐 Load ALL Crimes' to see everything")
        
        # Display statistics
        if not df.empty:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📍 Total Incidents", f"{len(df):,}")
            
            with col2:
                if 'arrest_made' in df.columns:
                    arrest_rate = (df['arrest_made'].sum() / len(df) * 100)
                    st.metric("🚔 Arrest Rate", f"{arrest_rate:.1f}%")
                else:
                    st.metric("🚔 Arrest Rate", "N/A")
            
            with col3:
                unique_districts = df['district'].nunique() if 'district' in df.columns else 0
                st.metric("🏛️ Districts", unique_districts)
            
            with col4:
                unique_types = df['crime_type'].nunique() if 'crime_type' in df.columns else 0
                st.metric("🚨 Crime Types", unique_types)
            
            with col5:
                severe_crimes = len(df[df['severity'] == 'severe']) if 'severity' in df.columns else 0
                st.metric("⚠️ Severe Cases", severe_crimes)
            
            st.markdown("---")
            
            # Show prediction warning if enabled but not enough data
            if show_predictions and len(df) < 20:
                st.warning("⚠️ Need at least 20 incidents for predictive analysis. Showing map without predictions.")
                show_predictions = False
            
            # Main unified map
            fig = self.create_unified_map(df, show_heatmap, show_predictions)
            st.plotly_chart(fig, use_container_width=True, key="unified_crime_map")
            
            # Info boxes based on what's enabled
            info_cols = []
            if show_heatmap:
                info_cols.append("🔥 **Heatmap**: Darker areas indicate higher crime concentration")
            if show_predictions:
                info_cols.append("🎯 **Predictions**: Larger circles with borders show AI-predicted high-risk zones")
            
            if info_cols:
                st.info(" | ".join(info_cols))
            
            st.markdown("---")
            
            # Prediction details (only show if predictions are enabled)
            if show_predictions and len(df) >= 20:
                predictions = self.predict_crime_hotspots(df)
                
                if not predictions.empty:
                    st.markdown("### 📈 Predicted Risk Zone Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        critical = len(predictions[predictions['risk_level'] == 'Critical'])
                        st.metric("🔴 Critical Risk", critical)
                    
                    with col2:
                        high = len(predictions[predictions['risk_level'] == 'High'])
                        st.metric("🟠 High Risk", high)
                    
                    with col3:
                        medium = len(predictions[predictions['risk_level'] == 'Medium'])
                        st.metric("🟡 Medium Risk", medium)
                    
                    with col4:
                        low = len(predictions[predictions['risk_level'] == 'Low'])
                        st.metric("🟢 Low Risk", low)
                    
                    # Detailed predictions table
                    with st.expander("📋 View Detailed Risk Assessments"):
                        display_predictions = predictions.sort_values('risk_score', ascending=False)
                        display_predictions = display_predictions[['district', 'primary_crime', 'crime_count', 'risk_score', 'risk_level']]
                        display_predictions.columns = ['District', 'Primary Crime Type', 'Historical Count', 'Risk Score', 'Risk Level']
                        
                        st.dataframe(
                            display_predictions,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # CSV export for predictions
                        pred_csv = predictions.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Predictions (CSV)",
                            data=pred_csv,
                            file_name=f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    st.markdown("---")
            
            # Analytics section
            with st.expander("📊 Crime Analytics Dashboard"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🚨 Crime Type Distribution")
                    crime_counts = df['crime_type'].value_counts().head(15)
                    fig_bar = px.bar(
                        x=crime_counts.index,
                        y=crime_counts.values,
                        labels={'x': 'Crime Type', 'y': 'Count'},
                        color=crime_counts.values,
                        color_continuous_scale='Reds'
                    )
                    fig_bar.update_layout(
                        showlegend=False,
                        height=350,
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_bar, use_container_width=True, key="crime_type_bar")
                
                with col2:
                    st.markdown("#### 🏛️ District Analysis")
                    district_counts = df['district'].value_counts().head(15)
                    fig_bar2 = px.bar(
                        x=district_counts.index,
                        y=district_counts.values,
                        labels={'x': 'District', 'y': 'Incidents'},
                        color=district_counts.values,
                        color_continuous_scale='Oranges'
                    )
                    fig_bar2.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig_bar2, use_container_width=True, key="district_bar")
                
                # Severity pie chart
                if 'severity' in df.columns:
                    st.markdown("#### ⚠️ Severity Distribution")
                    severity_counts = df['severity'].value_counts()
                    
                    colors_map = {'severe': '#dc2626', 'moderate': '#f59e0b', 'minor': '#10b981'}
                    
                    fig_pie = px.pie(
                        values=severity_counts.values,
                        names=severity_counts.index,
                        color=severity_counts.index,
                        color_discrete_map=colors_map,
                        hole=0.4
                    )
                    fig_pie.update_layout(height=350)
                    st.plotly_chart(fig_pie, use_container_width=True, key="severity_pie")
            
            # Methodology explanation
            with st.expander("🔬 How Predictive Analysis Works"):
                st.markdown("""
                ### 🎯 Predictive Methodology
                
                Our system uses **Machine Learning (DBSCAN clustering)** to identify and predict crime hotspots:
                
                **📊 Risk Score Calculation (0-100):**
                - **40%** Crime Frequency - How many crimes occurred in this cluster
                - **30%** Crime Severity - Proportion of severe crimes
                - **30%** Arrest Rate (inverse) - Lower arrest rates indicate higher future risk
                
                **🎨 Risk Levels:**
                - 🔴 **Critical** (70-100): Immediate intervention recommended
                - 🟠 **High** (50-69): Enhanced patrol presence needed
                - 🟡 **Medium** (30-49): Regular monitoring advised
                - 🟢 **Low** (0-29): Standard vigilance
                
                **💡 Practical Applications:**
                - Resource allocation for police departments
                - Community safety awareness programs
                - Urban planning and infrastructure improvements
                - Targeted intervention strategies
                
                **🔄 The heatmap overlay shows historical density, while predictions show future risk zones.**
                """)
            
            # Data export
            st.markdown("---")
            with st.expander("💾 Export Data"):
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Crime Data (CSV)",
                    data=csv,
                    file_name=f"crime_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.warning("⚠️ No crime data found matching the selected filters.")
            st.info("💡 Try adjusting your filters or increasing the data limit.")


def render_geographic_page(db):
    """
    Standalone function to render the geographic mapping page.
    Can be called directly from app.py
    
    Args:
        db: Database instance
    """
    mapper = CrimeGeographicMapper(db)
    mapper.render_map_interface()