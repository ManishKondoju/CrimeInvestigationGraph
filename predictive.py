from sklearn.cluster import DBSCAN
import pandas as pd
import numpy as np

def predict_crime_hotspots(crimes_data):
    """
    Use ML to predict future crime hotspots
    """
    
    if len(crimes_data) < 10:
        return None
    
    # Prepare data
    df = pd.DataFrame(crimes_data)
    
    # Extract coordinates
    coords = df[['lat', 'lon']].values
    
    # DBSCAN clustering
    db = DBSCAN(eps=0.01, min_samples=3)
    df['cluster'] = db.fit_predict(coords)
    
    # Find hotspot clusters
    hotspots = []
    
    for cluster_id in df['cluster'].unique():
        if cluster_id == -1:  # Skip noise
            continue
        
        cluster_data = df[df['cluster'] == cluster_id]
        
        hotspot = {
            'lat': cluster_data['lat'].mean(),
            'lon': cluster_data['lon'].mean(),
            'crime_count': len(cluster_data),
            'crime_types': cluster_data['crime_type'].value_counts().to_dict(),
            'risk_score': len(cluster_data) / len(df) * 100
        }
        
        hotspots.append(hotspot)
    
    # Sort by risk score
    hotspots = sorted(hotspots, key=lambda x: x['risk_score'], reverse=True)
    
    return hotspots[:10]  # Top 10 hotspots

def get_crime_statistics(db):
    """
    Advanced statistical analysis
    """
    
    stats = {}
    
    # Time-based patterns
    stats['hourly_pattern'] = db.query("""
        MATCH (c:Crime)
        WITH substring(c.time, 0, 2) as hour, count(*) as count
        RETURN hour, count
        ORDER BY hour
    """)
    
    # Day of week pattern (if we had that data)
    stats['type_correlation'] = db.query("""
        MATCH (p:Person)-[:PARTY_TO]->(c1:Crime)
        MATCH (p)-[:PARTY_TO]->(c2:Crime)
        WHERE c1 <> c2
        RETURN c1.type as type1, c2.type as type2, count(*) as correlation
        ORDER BY correlation DESC
        LIMIT 10
    """)
    
    return stats
