# geo_mapping.py - Enhanced Geographic Mapping with Heatmap + Predictions
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

class CrimeGeographicMapper:
    """Geographic visualization with heatmap and ML-powered predictions"""
    
    def __init__(self, db):
        self.db = db
        self.chicago_center = {"lat": 41.8781, "lon": -87.6298}
        
    def get_crime_locations(self, crime_types=None, start_date=None, end_date=None, 
                           districts=None, limit=5000):
        """Query crime locations from database"""
        query = """
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
        """
        
        # Build filter conditions
        if crime_types:
            types_str = "', '".join(crime_types)
            query += f" AND c.type IN ['{types_str}']"
            
        if start_date:
            query += f" AND c.date >= '{start_date}'"
            
        if end_date:
            query += f" AND c.date <= '{end_date}'"
            
        if districts:
            districts_str = "', '".join(districts)
            query += f" AND l.district IN ['{districts_str}']"
        
        query += f"""
        RETURN 
            c.id as case_id,
            c.type as crime_type,
            c.date as date,
            c.severity as severity,
            c.status as status,
            c.arrest_made as arrest_made,
            l.latitude as latitude,
            l.longitude as longitude,
            l.name as location_name,
            l.district as district
        ORDER BY c.date DESC
        LIMIT {limit}
        """
        
        try:
            records = self.db.query(query)
            if not records:
                return pd.DataFrame()
                
            df = pd.DataFrame(records)
            
            if not df.empty:
                # Convert to numeric
                df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
                df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
                df = df.dropna(subset=['latitude', 'longitude'])
                
                # Filter to Chicago bounds
                df = df[
                    (df['latitude'] >= 41.6) & (df['latitude'] <= 42.1) &
                    (df['longitude'] >= -87.95) & (df['longitude'] <= -87.5)
                ]
                
            return df
        except Exception as e:
            st.error(f"Database query error: {e}")
            return pd.DataFrame()
    
    def predict_hotspots(self, df):
        """Use DBSCAN clustering to predict crime hotspots with better distribution"""
        if df.empty or len(df) < 15:
            return pd.DataFrame()
        
        try:
            from sklearn.cluster import DBSCAN
            
            coords = df[['latitude', 'longitude']].values
            
            # More sensitive DBSCAN parameters for better cluster distribution
            # eps=0.005 degrees ≈ 0.55 km (creates more, smaller clusters)
            # min_samples=5 (lower threshold = more clusters detected)
            clustering = DBSCAN(eps=0.005, min_samples=5).fit(coords)
            df['cluster'] = clustering.labels_
            
            predictions = []
            
            for cluster_id in df['cluster'].unique():
                if cluster_id == -1:  # Noise points
                    continue
                
                cluster_data = df[df['cluster'] == cluster_id]
                crime_count = len(cluster_data)
                
                # Skip very small clusters (noise)
                if crime_count < 5:
                    continue
                
                # Calculate risk factors
                severe_count = len(cluster_data[cluster_data['severity'].isin(['severe', 'high', 'critical'])])
                arrest_rate = cluster_data['arrest_made'].mean() if 'arrest_made' in cluster_data.columns else 0
                
                # NEW: More granular risk scoring for better distribution
                # Volume component (0-30 points) - using sqrt for diminishing returns
                volume_score = min(30, np.sqrt(crime_count) * 5)
                
                # Severity component (0-40 points) - weighted by ratio
                severity_ratio = severe_count / crime_count
                severity_score = severity_ratio * 40
                
                # Unsolved component (0-30 points)
                unsolved_score = (1 - arrest_rate) * 30
                
                # Total risk score (0-100)
                risk_score = volume_score + severity_score + unsolved_score
                
                # More granular risk level classification for better spread
                if risk_score >= 70:
                    risk_level = 'Critical'
                elif risk_score >= 50:
                    risk_level = 'High'
                elif risk_score >= 30:
                    risk_level = 'Medium'
                else:
                    risk_level = 'Low'
                
                predictions.append({
                    'latitude': cluster_data['latitude'].mean(),
                    'longitude': cluster_data['longitude'].mean(),
                    'crime_count': crime_count,
                    'severe_count': severe_count,
                    'risk_score': round(risk_score, 1),
                    'risk_level': risk_level,
                    'primary_crime': cluster_data['crime_type'].mode()[0] if len(cluster_data) > 0 else 'MIXED',
                    'district': str(cluster_data['district'].mode()[0]) if 'district' in cluster_data.columns else 'Unknown',
                    'arrest_rate': round(arrest_rate * 100, 1)
                })
            
            return pd.DataFrame(predictions)
            
        except Exception as e:
            st.error(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def create_map(self, df, show_heatmap=False, show_predictions=False):
        """Create interactive Plotly mapbox visualization"""
        
        if df.empty:
            # Empty state with helpful message
            fig = go.Figure()
            fig.add_annotation(
                text="No crime data available<br>Try adjusting filters or reload database",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="#94a3b8")
            )
            fig.update_layout(height=600)
            return fig
        
        fig = go.Figure()
        
        center_lat = df['latitude'].mean()
        center_lon = df['longitude'].mean()
        
        # ========================================
        # HEATMAP MODE: Density visualization
        # ========================================
        if show_heatmap:
            # Weight by severity for intelligent heatmap
            severity_weights = {
                'low': 1, 
                'minor': 1,
                'medium': 2, 
                'moderate': 2,
                'high': 3, 
                'severe': 3,
                'critical': 4
            }
            
            z_values = df['severity'].map(severity_weights).fillna(1).tolist()
            
            # Main density heatmap layer
            fig.add_trace(go.Densitymapbox(
                lat=df['latitude'],
                lon=df['longitude'],
                z=z_values,  # Weighted by severity!
                radius=25,
                colorscale=[
                    [0, 'rgba(16, 185, 129, 0.5)'],      # Green (low)
                    [0.25, 'rgba(34, 197, 94, 0.6)'],    # Light green
                    [0.5, 'rgba(251, 191, 36, 0.7)'],    # Yellow
                    [0.7, 'rgba(249, 115, 22, 0.8)'],    # Orange
                    [0.85, 'rgba(239, 68, 68, 0.85)'],   # Red
                    [1, 'rgba(153, 27, 27, 0.9)']        # Dark red
                ],
                showscale=True,
                colorbar=dict(
                    title=dict(text="Crime<br>Intensity", side="right"),
                    x=1.02,
                    thickness=15,
                    len=0.7,
                    bgcolor='rgba(26, 31, 58, 0.9)',
                    bordercolor='rgba(102, 126, 234, 0.3)',
                    borderwidth=1,
                    tickfont=dict(color='#e2e8f0')
                ),
                hoverinfo='skip',
                name='Crime Density',
                zmin=0,
                zmax=4
            ))
            
            # Add hover points at cluster centers for info
            df['lat_round'] = (df['latitude'] * 100).round() / 100
            df['lon_round'] = (df['longitude'] * 100).round() / 100
            
            cluster_info = df.groupby(['lat_round', 'lon_round']).agg({
                'crime_type': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
                'severity': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
                'case_id': 'count',
                'latitude': 'mean',
                'longitude': 'mean',
                'district': lambda x: str(x.mode()[0]) if len(x) > 0 else 'Unknown'
            }).reset_index()
            
            cluster_info.columns = ['lat_r', 'lon_r', 'primary_type', 'primary_severity', 
                                   'crime_count', 'lat', 'lon', 'district']
            
            # Invisible hover markers
            hover_text = cluster_info.apply(
                lambda r: (
                    f"<b>📍 CRIME CLUSTER</b><br>"
                    f"━━━━━━━━━━━━━━━━<br>"
                    f"<b>Primary Type:</b> {r['primary_type']}<br>"
                    f"<b>Severity:</b> {r['primary_severity'].title()}<br>"
                    f"<b>Total Crimes:</b> {r['crime_count']}<br>"
                    f"<b>District:</b> {r['district']}"
                ),
                axis=1
            )
            
            fig.add_trace(go.Scattermapbox(
                lat=cluster_info['lat'],
                lon=cluster_info['lon'],
                mode='markers',
                marker=dict(
                    size=12,
                    color='rgba(255,255,255,0.05)',  # Nearly invisible
                    opacity=0.6,
                ),
                text=hover_text,
                hovertemplate='%{text}<extra></extra>',
                showlegend=False,
                name='Hover for details'
            ))
        
        # ========================================
        # PREDICTION MODE: ML Hotspots
        # ========================================
        elif show_predictions and len(df) >= 20:
            preds = self.predict_hotspots(df)
            
            if not preds.empty:
                # Info message
                st.success(f"🎯 ML Analysis: Identified {len(preds)} high-risk zones across Chicago")
                
                # Show background crimes more clearly for context
                fig.add_trace(go.Scattermapbox(
                    lat=df['latitude'],
                    lon=df['longitude'],
                    mode='markers',
                    marker=dict(
                        size=5, 
                        color='rgba(100, 116, 139, 0.4)',  # Lighter gray, more visible
                        opacity=0.5
                    ),
                    showlegend=True,
                    hoverinfo='skip',
                    name=f'Historical Crimes ({len(df)})'
                ))
                
                # Prediction circles by risk level
                risk_colors = {
                    'Low': '#10b981',
                    'Medium': '#3b82f6', 
                    'High': '#f59e0b',
                    'Critical': '#dc2626'
                }
                
                for risk_level in ['Low', 'Medium', 'High', 'Critical']:
                    subset = preds[preds['risk_level'] == risk_level]
                    
                    if not subset.empty:
                        color = risk_colors[risk_level]
                        
                        # Better sizing: smaller circles, scaled by risk level
                        # Critical: 35-50px, High: 28-42px, Medium: 22-35px, Low: 15-28px
                        base_sizes = {
                            'Critical': 35,
                            'High': 28,
                            'Medium': 22,
                            'Low': 15
                        }
                        base_size = base_sizes.get(risk_level, 20)
                        
                        # Scale by crime count (max +15px)
                        sizes = subset.apply(
                            lambda r: min(base_size + 15, base_size + (r['crime_count'] * 0.8)), 
                            axis=1
                        )
                        
                        # Outer glow layer (subtle)
                        fig.add_trace(go.Scattermapbox(
                            lat=subset['latitude'],
                            lon=subset['longitude'],
                            mode='markers',
                            marker=dict(
                                size=sizes * 1.6,  # Moderate glow
                                color=color,
                                opacity=0.15  # Very subtle
                            ),
                            showlegend=False,
                            hoverinfo='skip',
                            name=f'{risk_level} Glow'
                        ))
                        
                        # Main prediction circles with detailed tooltips
                        hover_text = subset.apply(
                            lambda r: (
                                f"<b>🎯 PREDICTED HOTSPOT</b><br>"
                                f"<b style='font-size: 14px;'>Risk Level: {r['risk_level']} ({r['risk_score']:.0f}/100)</b><br>"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                                f"📊 Historical Crimes: <b>{r['crime_count']}</b><br>"
                                f"⚠️ Severe Incidents: <b>{r['severe_count']}</b><br>"
                                f"🚨 Primary Type: <b>{r['primary_crime']}</b><br>"
                                f"🏛️ District: <b>{r['district']}</b><br>"
                                f"🚔 Arrest Rate: <b>{r['arrest_rate']:.1f}%</b><br>"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━<br>"
                                f"💡 This area has <b>{r['crime_count']}</b> historical crimes<br>"
                                f"with <b>{r['risk_score']:.0f}%</b> likelihood of future incidents"
                            ),
                            axis=1
                        )
                        
                        fig.add_trace(go.Scattermapbox(
                            lat=subset['latitude'],
                            lon=subset['longitude'],
                            mode='markers',
                            marker=dict(
                                size=sizes,
                                color=color,
                                opacity=0.8  # More visible
                            ),
                            name=f'🎯 {risk_level} Risk ({len(subset)})',
                            text=hover_text,
                            hovertemplate='%{text}<extra></extra>',
                            showlegend=True
                        ))
            else:
                st.info("🎯 Not enough data for predictions. Need at least 20 crimes.")
        
        # ========================================
        # DEFAULT MODE: Individual crime markers
        # ========================================
        else:
            severity_colors = {
                'critical': '#8e44ad',
                'severe': '#dc2626', 
                'high': '#dc2626',
                'moderate': '#f59e0b',
                'medium': '#f59e0b', 
                'minor': '#10b981',
                'low': '#10b981'
            }
            
            for severity in df['severity'].unique():
                df_sev = df[df['severity'] == severity]
                
                if not df_sev.empty:
                    color = severity_colors.get(severity, '#3b82f6')
                    
                    hover_text = df_sev.apply(
                        lambda r: (
                            f"<b>🚨 {r['crime_type']}</b><br>"
                            f"━━━━━━━━━━━━━━━━<br>"
                            f"📅 Date: {r['date']}<br>"
                            f"📍 Location: {r['location_name'][:50]}<br>"
                            f"🏛️ District: {r['district']}<br>"
                            f"⚠️ Severity: {r['severity'].title()}<br>"
                            f"📊 Status: {r['status'].title()}"
                        ),
                        axis=1
                    )
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=df_sev['latitude'],
                        lon=df_sev['longitude'],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color=color,
                            opacity=0.7,
                        ),
                        name=f'{severity.title()} ({len(df_sev)})',
                        text=hover_text,
                        hovertemplate='%{text}<extra></extra>',
                        showlegend=True
                    ))
        
        # Map layout
        title_parts = [f"📍 Chicago Crime Map - {len(df):,} Incidents"]
        if show_heatmap:
            title_parts.append("🔥 Density Heatmap")
        if show_predictions:
            title_parts.append("🎯 ML Predicted Hotspots")
        
        fig.update_layout(
            mapbox=dict(
                style="carto-darkmatter",  # Dark theme matches your UI
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11  # Slightly zoomed out to show distribution better
            ),
            title={
                'text': " | ".join(title_parts), 
                'x': 0.5, 
                'xanchor': 'center',
                'font': dict(size=20, color='#ffffff')
            },
            height=700,
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
            showlegend=True,
            legend=dict(
                yanchor="top", y=0.99,
                xanchor="right", x=0.99,
                bgcolor="rgba(26, 31, 58, 0.9)",
                bordercolor="rgba(102, 126, 234, 0.3)",
                borderwidth=1,
                font=dict(color='#e2e8f0')
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='closest'
        )
        
        return fig
    
    def render_map_interface(self):
        """Render the complete geographic mapping interface"""
        st.markdown("## 🗺️ Geographic Crime Analysis")
        st.markdown("Interactive crime heatmap with ML-powered hotspot predictions")
        
        # Animation CSS for predictions
        st.markdown("""
        <style>
        @keyframes pulse-glow {
            0%, 100% { 
                box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
                transform: scale(1);
            }
            50% { 
                box-shadow: 0 0 25px rgba(239, 68, 68, 0.8);
                transform: scale(1.02);
            }
        }
        
        .prediction-badge {
            animation: pulse-glow 2s ease-in-out infinite;
            padding: 14px 24px;
            border-radius: 12px;
            background: rgba(239, 68, 68, 0.15);
            border: 2px solid #ef4444;
            margin: 15px 0;
            font-weight: 600;
            text-align: center;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 16px;
            margin: 10px 0;
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Visualization controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 🎛️ Visualization Mode")
        
        with col2:
            show_heatmap = st.toggle("🔥 Heatmap", value=False, 
                                    help="Smooth density gradient weighted by crime severity")
        
        with col3:
            show_predictions = st.toggle("🎯 Predictions", value=False, 
                                        help="ML-identified high-risk zones using DBSCAN clustering")
        
        # Additional option to show all location coverage
        show_all_locations = st.sidebar.checkbox("📍 Show All Locations", value=False,
                                                 help="Display all database locations to verify coverage")
        
        # Mode descriptions with visual styling
        if show_heatmap:
            st.success("🔥 **Heatmap Mode:** Gradient overlay weighted by severity - Green (low) → Yellow → Orange → Red (high)")
        elif show_predictions:
            st.markdown(
                '<div class="prediction-badge">'
                '🎯 <b>Prediction Mode:</b> Large circles show AI-identified high-risk zones with detailed risk scores!'
                '</div>', 
                unsafe_allow_html=True
            )
        else:
            st.info("📍 **Default Mode:** Individual crime incidents color-coded by severity with detailed hover info")
        
        st.markdown("---")
        
        # Sidebar filters
        with st.sidebar:
            st.markdown("### 🔍 Map Filters")
            
            # Date range filter
            use_date_filter = st.checkbox("📅 Filter by Date Range", value=False)
            start_date, end_date = None, None
            
            if use_date_filter:
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("From", value=datetime(2024, 1, 1)).strftime("%Y-%m-%d")
                with col2:
                    end_date = st.date_input("To", value=datetime.now()).strftime("%Y-%m-%d")
            
            # Get available crime types
            try:
                types_result = self.db.query("MATCH (c:Crime) RETURN DISTINCT c.type as type ORDER BY type")
                types_avail = [r['type'] for r in types_result] if types_result else []
            except:
                types_avail = []
            
            crime_types = st.multiselect("🚨 Crime Types", options=types_avail)
            
            # Get available districts
            try:
                districts_result = self.db.query("MATCH (l:Location) WHERE l.district IS NOT NULL RETURN DISTINCT l.district as district ORDER BY district")
                districts_avail = [str(r['district']) for r in districts_result] if districts_result else []
            except:
                districts_avail = []
            
            districts = st.multiselect("🏛️ Districts", options=districts_avail)
            
            # Data limit
            data_limit = st.slider("📊 Max Records", 500, 10000, 5000, 500)
            
            st.markdown("---")
            apply_filters = st.button("🔄 Apply Filters", use_container_width=True, type="primary")
        
        # Load data (cache unless filters applied)
        if 'geo_data' not in st.session_state or apply_filters:
            with st.spinner("📡 Loading crime data from database..."):
                st.session_state.geo_data = self.get_crime_locations(
                    crime_types=crime_types if crime_types else None,
                    start_date=start_date,
                    end_date=end_date,
                    districts=districts if districts else None,
                    limit=data_limit
                )
        
        df = st.session_state.geo_data
        
        # Display results
        if not df.empty:
            # Statistics row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📍 Total Incidents", f"{len(df):,}")
            
            with col2:
                if 'arrest_made' in df.columns:
                    arrest_rate = (df['arrest_made'].sum() / len(df) * 100)
                    st.metric("🚔 Arrest Rate", f"{arrest_rate:.1f}%")
                else:
                    st.metric("🚔 With Arrests", 0)
            
            with col3:
                st.metric("🚨 Crime Types", df['crime_type'].nunique())
            
            with col4:
                severe = len(df[df['severity'].isin(['severe', 'high', 'critical'])])
                st.metric("⚠️ High Severity", severe)
            
            with col5:
                st.metric("🏛️ Districts", df['district'].nunique())
            
            st.markdown("---")
            
            # Create and display map
            with st.spinner("🗺️ Generating map..."):
                fig = self.create_map(df, show_heatmap, show_predictions)
                
                # Add all locations if requested (for coverage verification)
                if show_all_locations:
                    all_locs_query = """
                    MATCH (l:Location)
                    WHERE l.latitude IS NOT NULL AND l.longitude IS NOT NULL
                    RETURN l.latitude as lat, l.longitude as lon, l.name as name, 
                           l.district as district, l.source as source
                    """
                    all_locs = self.db.query(all_locs_query)
                    
                    if all_locs:
                        locs_df = pd.DataFrame(all_locs)
                        locs_df['lat'] = pd.to_numeric(locs_df['lat'], errors='coerce')
                        locs_df['lon'] = pd.to_numeric(locs_df['lon'], errors='coerce')
                        locs_df = locs_df.dropna()
                        
                        # Add as small blue markers
                        fig.add_trace(go.Scattermapbox(
                            lat=locs_df['lat'],
                            lon=locs_df['lon'],
                            mode='markers',
                            marker=dict(size=6, color='#3b82f6', opacity=0.6),
                            name=f'All Locations ({len(locs_df)})',
                            text=locs_df.apply(lambda r: f"<b>{r['name'][:40]}</b><br>District: {r['district']}<br>Source: {r['source']}", axis=1),
                            hovertemplate='%{text}<extra></extra>'
                        ))
                        
                        st.info(f"📍 Showing all {len(locs_df)} database locations")
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Geographic distribution diagnostic
            st.markdown("---")
            st.markdown("### 🌍 Geographic Distribution Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Crime Count by District")
                district_crimes = df.groupby('district').size().reset_index(name='crimes')
                district_crimes = district_crimes.sort_values('crimes', ascending=False).head(15)
                
                fig_dist = px.bar(
                    district_crimes,
                    x='district',
                    y='crimes',
                    color='crimes',
                    color_continuous_scale='Reds',
                    text='crimes'
                )
                
                fig_dist.update_traces(textposition='outside')
                fig_dist.update_layout(
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_title="District",
                    yaxis_title="Crime Count",
                    showlegend=False
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Coverage warning
                districts_with_crimes = len(district_crimes)
                if districts_with_crimes < 10:
                    st.warning(f"⚠️ Only {districts_with_crimes} districts have crimes. Geographic coverage is limited.")
                else:
                    st.success(f"✅ Good coverage: {districts_with_crimes} districts represented")
            
            with col2:
                st.markdown("#### Coordinate Spread")
                
                lat_range = df['latitude'].max() - df['latitude'].min()
                lon_range = df['longitude'].max() - df['longitude'].min()
                
                st.metric("Latitude Range", f"{lat_range:.4f}°")
                st.metric("Longitude Range", f"{lon_range:.4f}°")
                
                # Rough estimate of coverage area
                # 1 degree latitude ≈ 111 km
                # 1 degree longitude at Chicago ≈ 82 km
                coverage_km_lat = lat_range * 111
                coverage_km_lon = lon_range * 82
                
                st.metric("Coverage (N-S)", f"{coverage_km_lat:.1f} km")
                st.metric("Coverage (E-W)", f"{coverage_km_lon:.1f} km")
                
                # Full Chicago is roughly 40km x 25km
                if coverage_km_lat < 20 or coverage_km_lon < 15:
                    st.warning("⚠️ Limited geographic spread. Crimes clustered in small area.")
                    st.info("💡 Reload data to add geographic diversity: `python load_hybrid_data.py`")
                else:
                    st.success("✅ Good geographic distribution across city")
            
            # Prediction details
            if show_predictions and len(df) >= 20:
                preds = self.predict_hotspots(df)
                
                if not preds.empty:
                    st.markdown("---")
                    st.markdown("### 🎯 Predicted High-Risk Zones")
                    
                    # Risk level summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        critical_count = len(preds[preds['risk_level'] == 'Critical'])
                        st.metric("🔴 Critical Risk", critical_count)
                    with col2:
                        high_count = len(preds[preds['risk_level'] == 'High'])
                        st.metric("🟠 High Risk", high_count)
                    with col3:
                        medium_count = len(preds[preds['risk_level'] == 'Medium'])
                        st.metric("🟡 Medium Risk", medium_count)
                    with col4:
                        low_count = len(preds[preds['risk_level'] == 'Low'])
                        st.metric("🟢 Low Risk", low_count)
                    
                    # Top 5 highest risk zones
                    st.markdown("#### 🔥 Top 5 Highest Risk Zones")
                    
                    top_5 = preds.sort_values('risk_score', ascending=False).head(5)
                    
                    for idx, (_, hotspot) in enumerate(top_5.iterrows(), 1):
                        risk_color = {
                            'Critical': '#dc2626',
                            'High': '#f59e0b',
                            'Medium': '#3b82f6',
                            'Low': '#10b981'
                        }.get(hotspot['risk_level'], '#6b7280')
                        
                        st.markdown(f"""
                        <div class='glass-card' style='border-left: 4px solid {risk_color};'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <h4 style='margin: 0; color: #ffffff;'>#{idx} District {hotspot['district']}</h4>
                                    <p style='margin: 5px 0 0 0; color: #a0aec0; font-size: 0.9rem;'>
                                        {hotspot['crime_count']} crimes • Primary: {hotspot['primary_crime']} • 
                                        {hotspot['severe_count']} severe • Arrests: {hotspot['arrest_rate']:.0f}%
                                    </p>
                                </div>
                                <div style='text-align: right;'>
                                    <div style='font-size: 1.8rem; font-weight: bold; color: {risk_color};'>
                                        {hotspot['risk_score']:.0f}/100
                                    </div>
                                    <div style='font-size: 0.9rem; color: #cbd5e0;'>{hotspot['risk_level']} Risk</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Full details table
                    with st.expander("📋 View All Hotspot Details"):
                        display = preds.sort_values('risk_score', ascending=False).copy()
                        display['risk_display'] = display.apply(
                            lambda r: f"{r['risk_level']} ({r['risk_score']}/100)", 
                            axis=1
                        )
                        
                        display_cols = display[['district', 'primary_crime', 'crime_count', 
                                               'severe_count', 'arrest_rate', 'risk_display']]
                        display_cols.columns = ['District', 'Primary Crime', 'Total Crimes', 
                                               'Severe', 'Arrest %', 'Risk Level']
                        
                        st.dataframe(display_cols, use_container_width=True, hide_index=True, height=400)
            
            # Crime analytics
            st.markdown("---")
            
            with st.expander("📊 Crime Analytics Dashboard"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Top Crime Types")
                    type_counts = df['crime_type'].value_counts().head(10)
                    
                    fig_types = px.bar(
                        y=type_counts.index, 
                        x=type_counts.values, 
                        orientation='h',
                        color=type_counts.values, 
                        color_continuous_scale='Reds',
                        text=type_counts.values
                    )
                    
                    fig_types.update_traces(textposition='outside')
                    fig_types.update_layout(
                        showlegend=False, 
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#e2e8f0'),
                        xaxis_title="Number of Incidents",
                        yaxis_title="Crime Type"
                    )
                    st.plotly_chart(fig_types, use_container_width=True)
                
                with col2:
                    st.markdown("#### District Distribution")
                    district_counts = df['district'].value_counts().head(10)
                    
                    fig_districts = px.pie(
                        values=district_counts.values, 
                        names=district_counts.index, 
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Plasma
                    )
                    
                    fig_districts.update_traces(textinfo='label+percent')
                    fig_districts.update_layout(
                        height=400, 
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)', 
                        font=dict(color='#e2e8f0')
                    )
                    st.plotly_chart(fig_districts, use_container_width=True)
            
            # Data export
            with st.expander("💾 Export Crime Data"):
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Crime Data (CSV)",
                    data=csv,
                    file_name=f"chicago_crimes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.info(f"💡 Exporting {len(df)} crime records with geographic coordinates")
        
        else:
            # No data state
            st.warning("⚠️ No crime data found with location coordinates")
            st.info("""
            **Troubleshooting Steps:**
            
            1. **Load data:** Run `python load_hybrid_data.py`
            
            2. **Verify locations in Neo4j Browser:**
               ```cypher
               MATCH (l:Location) 
               WHERE l.latitude IS NOT NULL 
               RETURN count(l)
               ```
               Should return: 250-450 locations
            
            3. **Check crime-location relationships:**
               ```cypher
               MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location) 
               WHERE l.latitude IS NOT NULL
               RETURN count(c)
               ```
               Should return: 495 crimes
            
            4. **Try removing all filters** in the sidebar
            
            5. **Restart Neo4j:** `neo4j restart`
            """)


def render_geographic_page(db):
    """Main entry point for geographic mapping page"""
    try:
        mapper = CrimeGeographicMapper(db)
        mapper.render_map_interface()
    except Exception as e:
        st.error(f"Error rendering geographic page: {e}")
        st.exception(e)