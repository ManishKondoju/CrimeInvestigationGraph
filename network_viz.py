from pyvis.network import Network
import networkx as nx
import streamlit.components.v1 as components

def create_3d_network(db, crime_type=None, limit=50):
    """
    Create interactive 3D network visualization of criminals and crimes
    """
    
    # Query for network data
    if crime_type:
        query = f"""
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime {{type: '{crime_type}'}})
        WITH p, c
        MATCH (p)-[r]-(connected)
        RETURN p.name as person, c.id as crime, type(r) as relationship, 
               labels(connected)[0] as connected_type, 
               connected.name as connected_name
        LIMIT {limit}
        """
    else:
        query = f"""
        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
        WITH p, c
        MATCH (p)-[r]-(connected)
        RETURN p.name as person, c.id as crime, type(r) as relationship,
               labels(connected)[0] as connected_type,
               connected.name as connected_name
        LIMIT {limit}
        """
    
    results = db.query(query)
    
    if not results:
        return None
    
    # Create network graph
    net = Network(
        height='600px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=False
    )
    
    # Configure physics
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -50000,
                "springLength": 200,
                "springConstant": 0.04
            }
        },
        "nodes": {
            "font": {"size": 16}
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            }
        }
    }
    """)
    
    # Add nodes and edges
    for record in results:
        person = record['person']
        crime = record['crime']
        connected = record.get('connected_name', '')
        rel_type = record['relationship']
        
        # Add person node (red)
        net.add_node(
            person,
            label=person,
            color='#ff4444',
            size=25,
            title=f"Person: {person}"
        )
        
        # Add crime node (blue)
        net.add_node(
            crime,
            label=f"Crime: {crime}",
            color='#4444ff',
            size=15,
            shape='box',
            title=f"Crime ID: {crime}"
        )
        
        # Connect person to crime
        net.add_edge(person, crime, title=rel_type, color='#999999')
        
        # Add connected nodes
        if connected:
            if record['connected_type'] == 'Person':
                net.add_node(connected, label=connected, color='#ff8844', size=20)
                net.add_edge(person, connected, title=rel_type, color='#ff8844', dashes=True)
            elif record['connected_type'] == 'Location':
                net.add_node(connected, label=connected, color='#44ff44', size=15, shape='triangle')
                net.add_edge(crime, connected, title='OCCURRED_AT', color='#44ff44')
    
    # Generate HTML
    net.save_graph('network.html')
    
    with open('network.html', 'r', encoding='utf-8') as f:
        html_string = f.read()
    
    return html_string
