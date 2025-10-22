import folium
from folium import plugins
import pandas as pd

def create_advanced_crime_map(crimes_data, show_heatmap=False, show_connections=False, show_clusters=False):
    """
    Create an advanced crime map with multiple visualization layers
    """
    
    # Base map - Light mode
    m = folium.Map(
        location=[41.8781, -87.6298],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Crime color mapping
    crime_colors = {
        "Theft": "#3388ff",
        "Battery": "#ff3333",
        "Criminal Damage": "#ff9933",
        "Assault": "#cc0000",
        "Burglary": "#9933ff",
        "Motor Vehicle Theft": "#0066cc",
        "Robbery": "#990000",
        "Deceptive Practice": "#66ccff",
        "Criminal Trespass": "#999999",
        "Narcotics": "#339933",
        "Weapons Violation": "#000000",
        "Other Offense": "#666666",
        "Offense Involving Children": "#ff66cc",
        "Public Peace Violation": "#ffcc99"
    }
    
    # Feature Group for regular markers
    marker_group = folium.FeatureGroup(name='Crime Markers')
    
    # Add markers with custom icons
    for crime in crimes_data:
        color = crime_colors.get(crime['crime_type'], '#666666')
        
        # Detailed popup
        popup_html = f"""
        <div style='width: 280px; font-family: Arial; background: white; padding: 15px; border-radius: 8px;'>
            <h3 style='color: {color}; margin: 0 0 10px 0; border-bottom: 2px solid {color}; padding-bottom: 5px;'>
                🚨 {crime['crime_type']}
            </h3>
            <table style='width: 100%; font-size: 13px;'>
                <tr><td style='padding: 3px 0;'><b>📍 Location:</b></td><td>{crime['location']}</td></tr>
                <tr><td style='padding: 3px 0;'><b>📅 Date:</b></td><td>{crime['date']}</td></tr>
                <tr><td style='padding: 3px 0;'><b>🕐 Time:</b></td><td>{crime['time']}</td></tr>
                <tr><td style='padding: 3px 0;'><b>🔖 Case #:</b></td><td>{crime['case_number']}</td></tr>
                <tr><td style='padding: 3px 0;'><b>🆔 ID:</b></td><td>{crime['crime_id']}</td></tr>
            </table>
        </div>
        """
        
        # Pulsing circle marker with animation
        folium.CircleMarker(
            location=[crime['lat'], crime['lon']],
            radius=10,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{crime['crime_type']}</b><br>{crime['location']}<br>{crime['date']}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=3,
            className='pulsing-marker'
        ).add_to(marker_group)
        
        # Add icon marker
        folium.Marker(
            location=[crime['lat'], crime['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{crime['crime_type']} - Click for details",
            icon=folium.Icon(
                color='red' if 'Assault' in crime['crime_type'] or 'Battery' in crime['crime_type'] else 'blue',
                icon='exclamation-sign',
                prefix='glyphicon'
            )
        ).add_to(marker_group)
    
    marker_group.add_to(m)
    
    # HEATMAP LAYER
    if show_heatmap:
        heat_data = [[crime['lat'], crime['lon']] for crime in crimes_data]
        plugins.HeatMap(
            heat_data,
            name='Crime Heatmap',
            min_opacity=0.3,
            max_zoom=18,
            radius=25,
            blur=35,
            gradient={
                0.0: 'blue',
                0.3: 'lime',
                0.5: 'yellow',
                0.7: 'orange',
                1.0: 'red'
            }
        ).add_to(m)
    
    # CLUSTER LAYER
    if show_clusters:
        from folium.plugins import MarkerCluster
        
        marker_cluster = MarkerCluster(name='Crime Clusters').add_to(m)
        
        for crime in crimes_data:
            color = crime_colors.get(crime['crime_type'], '#666666')
            
            folium.Marker(
                location=[crime['lat'], crime['lon']],
                popup=f"<b>{crime['crime_type']}</b><br>{crime['location']}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
    
    # CONNECTION LINES
    if show_connections and len(crimes_data) > 1:
        # Group crimes by type and location
        crime_groups = {}
        
        for crime in crimes_data:
            key = (crime['crime_type'], round(crime['lat'], 3), round(crime['lon'], 3))
            if key not in crime_groups:
                crime_groups[key] = []
            crime_groups[key].append(crime)
        
        # Find patterns
        connection_group = folium.FeatureGroup(name='Crime Connections')
        
        crime_list = list(crimes_data)
        connected_count = 0
        
        for i, crime1 in enumerate(crime_list):
            for crime2 in crime_list[i+1:]:
                # Same type crimes within 1km
                if crime1['crime_type'] == crime2['crime_type']:
                    lat_diff = abs(crime1['lat'] - crime2['lat'])
                    lon_diff = abs(crime1['lon'] - crime2['lon'])
                    distance = (lat_diff**2 + lon_diff**2)**0.5
                    
                    if distance < 0.01 and connected_count < 100:  # Limit connections
                        color = crime_colors.get(crime1['crime_type'], '#666666')
                        
                        # Animated polyline
                        folium.PolyLine(
                            locations=[
                                [crime1['lat'], crime1['lon']],
                                [crime2['lat'], crime2['lon']]
                            ],
                            color=color,
                            weight=3,
                            opacity=0.6,
                            popup=f"<b>Pattern Detected:</b><br>{crime1['crime_type']}<br>Distance: ~{distance*100:.1f}km",
                            tooltip=f"Connected: {crime1['crime_type']}",
                            dash_array='10, 5'
                        ).add_to(connection_group)
                        
                        connected_count += 1
        
        connection_group.add_to(m)
    
    # Add CSS for pulsing animation
    pulse_css = """
    <style>
    @keyframes pulse {
        0% {
            stroke-width: 3;
            opacity: 0.8;
        }
        50% {
            stroke-width: 6;
            opacity: 1;
        }
        100% {
            stroke-width: 3;
            opacity: 0.8;
        }
    }
    
    .pulsing-marker {
        animation: pulse 2s infinite;
    }
    
    .leaflet-interactive {
        transition: all 0.3s ease;
    }
    
    .leaflet-interactive:hover {
        stroke-width: 5 !important;
        opacity: 1 !important;
        transform: scale(1.1);
    }
    </style>
    """
    
    m.get_root().html.add_child(folium.Element(pulse_css))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit Fullscreen',
        force_separate_button=True
    ).add_to(m)
    
    # Add measure control
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    return m
