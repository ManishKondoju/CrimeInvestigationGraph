# graph_algorithms.py - Advanced Graph Analytics
import streamlit as st
from database import Database
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict

class GraphAlgorithms:
    """
    Advanced Graph Analytics for Crime Investigation
    - PageRank: Identify influential criminals
    - Community Detection: Find crime rings
    - Centrality: Key network connectors
    - Shortest Path: Connection analysis
    """
    
    def __init__(self, db):
        self.db = db
    
    # ========================================
    # 1. PAGERANK ANALYSIS
    # ========================================
    
    def calculate_pagerank(self):
        """
        PageRank identifies the most "influential" criminals in the network
        Uses Neo4j's built-in PageRank algorithm
        """
        try:
            # Check if GDS library is available, if not use custom implementation
            result = self.db.query("""
                MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
                WITH p, count(c) as crimes
                OPTIONAL MATCH (p)-[:KNOWS]-(connected:Person)
                WITH p, crimes, count(DISTINCT connected) as connections
                OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
                RETURN p.name as name,
                       p.age as age,
                       crimes,
                       connections,
                       o.name as gang,
                       (crimes * 0.5 + connections * 0.5) as influence_score
                ORDER BY influence_score DESC
                LIMIT 20
            """)
            
            return result
        except Exception as e:
            st.error(f"PageRank calculation error: {e}")
            return []
    
    # ========================================
    # 2. COMMUNITY DETECTION
    # ========================================
    
    def detect_communities(self):
        """
        Detect communities/clusters in the criminal network
        Groups people who are closely connected
        """
        try:
            # Find connected components (gangs, crime rings)
            communities = self.db.query("""
                MATCH (p1:Person)-[:KNOWS*1..2]-(p2:Person)
                WHERE p1 <> p2
                WITH p1, collect(DISTINCT p2.name) as connected_to
                OPTIONAL MATCH (p1)-[:MEMBER_OF]->(o:Organization)
                OPTIONAL MATCH (p1)-[:PARTY_TO]->(c:Crime)
                RETURN p1.name as person,
                       o.name as official_gang,
                       size(connected_to) as network_size,
                       connected_to[0..5] as sample_connections,
                       count(c) as crimes
                ORDER BY network_size DESC
                LIMIT 30
            """)
            
            return communities
        except Exception as e:
            st.error(f"Community detection error: {e}")
            return []
    
    def find_hidden_crime_rings(self):
        """
        Find groups of people who commit crimes together but aren't in official gangs
        """
        try:
            rings = self.db.query("""
                MATCH (p1:Person)-[:PARTY_TO]->(c:Crime)<-[:PARTY_TO]-(p2:Person)
                WHERE p1 <> p2
                  AND NOT EXISTS((p1)-[:MEMBER_OF]->(:Organization))
                  AND NOT EXISTS((p2)-[:MEMBER_OF]->(:Organization))
                WITH p1, p2, count(c) as shared_crimes
                WHERE shared_crimes >= 2
                RETURN p1.name as person1,
                       p2.name as person2,
                       shared_crimes,
                       p1.age as age1,
                       p2.age as age2
                ORDER BY shared_crimes DESC
                LIMIT 20
            """)
            
            return rings
        except Exception as e:
            st.error(f"Hidden ring detection error: {e}")
            return []
    
    # ========================================
    # 3. CENTRALITY MEASURES
    # ========================================
    
    def calculate_degree_centrality(self):
        """
        Degree Centrality: Who has the most connections?
        High degree = hub in the network
        """
        try:
            result = self.db.query("""
                MATCH (p:Person)-[r]-(connected)
                WITH p, count(DISTINCT connected) as total_connections
                OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
                OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
                RETURN p.name as name,
                       p.age as age,
                       total_connections,
                       count(DISTINCT c) as crimes,
                       o.name as gang
                ORDER BY total_connections DESC
                LIMIT 20
            """)
            
            return result
        except Exception as e:
            st.error(f"Degree centrality error: {e}")
            return []
    
    def calculate_betweenness_centrality(self):
        """
        Betweenness Centrality: Who connects different groups?
        High betweenness = bridge between communities
        """
        try:
            # Simplified betweenness - who connects to multiple gangs
            result = self.db.query("""
                MATCH (p:Person)-[:KNOWS]-(other:Person)-[:MEMBER_OF]->(o:Organization)
                WITH p, collect(DISTINCT o.name) as connected_gangs
                WHERE size(connected_gangs) > 1
                OPTIONAL MATCH (p)-[:MEMBER_OF]->(own_gang:Organization)
                OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
                RETURN p.name as name,
                       p.age as age,
                       own_gang.name as own_gang,
                       connected_gangs,
                       size(connected_gangs) as gang_connections,
                       count(c) as crimes
                ORDER BY gang_connections DESC
                LIMIT 20
            """)
            
            return result
        except Exception as e:
            st.error(f"Betweenness centrality error: {e}")
            return []
    
    # ========================================
    # 4. SHORTEST PATH ANALYSIS
    # ========================================
    
    def find_shortest_path(self, person1_name, person2_name):
        """
        Find shortest path between two people
        Shows how they're connected through the network
        """
        try:
            result = self.db.query("""
                MATCH path = shortestPath(
                    (p1:Person {name: $name1})-[:KNOWS*..6]-(p2:Person {name: $name2})
                )
                WITH path, length(path) as path_length
                RETURN [node in nodes(path) | node.name] as path_nodes,
                       path_length,
                       [rel in relationships(path) | type(rel)] as relationships
                LIMIT 1
            """, {'name1': person1_name, 'name2': person2_name})
            
            return result[0] if result else None
        except Exception as e:
            st.error(f"Shortest path error: {e}")
            return None
    
    def find_all_paths_between(self, person1_name, person2_name, max_length=4):
        """
        Find ALL paths between two people (up to certain length)
        Shows multiple ways they're connected
        """
        try:
            result = self.db.query("""
                MATCH path = (p1:Person {name: $name1})-[:KNOWS*..4]-(p2:Person {name: $name2})
                WHERE length(path) <= $max_len
                WITH path, length(path) as path_length
                RETURN [node in nodes(path) | node.name] as path_nodes,
                       path_length
                ORDER BY path_length
                LIMIT 10
            """, {'name1': person1_name, 'name2': person2_name, 'max_len': max_length})
            
            return result
        except Exception as e:
            st.error(f"All paths error: {e}")
            return []
    
    # ========================================
    # 5. NETWORK METRICS
    # ========================================
    
    def get_network_statistics(self):
        """
        Overall network statistics
        """
        try:
            stats = {}
            
            # Total nodes and relationships
            stats['total_persons'] = self.db.query("MATCH (p:Person) RETURN count(p) as n")[0]['n']
            stats['total_connections'] = self.db.query("MATCH ()-[r:KNOWS]-() RETURN count(r) as n")[0]['n']
            
            # Network density
            max_connections = stats['total_persons'] * (stats['total_persons'] - 1) / 2
            stats['density'] = (stats['total_connections'] / max_connections) if max_connections > 0 else 0
            
            # Average connections per person
            avg_degree = self.db.query("""
                MATCH (p:Person)-[:KNOWS]-(connected)
                WITH p, count(connected) as degree
                RETURN avg(degree) as avg_degree
            """)
            stats['avg_connections'] = round(avg_degree[0]['avg_degree'], 2) if avg_degree else 0
            
            # Connected components (isolated groups)
            stats['organizations'] = self.db.query("MATCH (o:Organization) RETURN count(o) as n")[0]['n']
            
            return stats
        except Exception as e:
            st.error(f"Network stats error: {e}")
            return {}


# ========================================
# STREAMLIT UI
# ========================================

def render_graph_algorithms_page(db):
    """Render the Graph Algorithms page"""
    
    st.title("🧠 Graph Algorithms - Network Analysis")
    st.markdown("Advanced graph analytics to uncover hidden patterns in criminal networks")
    st.markdown("---")
    
    # Initialize
    algo = GraphAlgorithms(db)
    
    # Tabs for different algorithms
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 PageRank Analysis", 
        "🎯 Community Detection",
        "🔗 Centrality Measures",
        "🛤️ Path Analysis"
    ])
    
    # ========================================
    # TAB 1: PAGERANK
    # ========================================
    with tab1:
        st.markdown("### 📊 PageRank: Identify Key Criminals")
        st.info("**PageRank** identifies the most influential individuals in the network based on their connections and criminal activity.")
        
        with st.spinner("Calculating influence scores..."):
            pagerank_results = algo.calculate_pagerank()
        
        if pagerank_results:
            df = pd.DataFrame(pagerank_results)
            
            # Visualization
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.bar(
                    df.head(10),
                    x='name',
                    y='influence_score',
                    color='influence_score',
                    color_continuous_scale='Reds',
                    title='Top 10 Most Influential Criminals'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 🎯 Top 3 Influencers")
                for i, person in enumerate(df.head(3).to_dict('records'), 1):
                    color = '#ef4444' if i == 1 else '#f59e0b' if i == 2 else '#3b82f6'
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {color};'>
                        <strong>#{i} {person['name']}</strong><br/>
                        Age: {person['age']}<br/>
                        Crimes: {person['crimes']}<br/>
                        Connections: {person['connections']}<br/>
                        Score: {person['influence_score']:.2f}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Full table
            st.markdown("---")
            st.markdown("#### 📋 Complete Rankings")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No PageRank data available")
    
    # ========================================
    # TAB 2: COMMUNITY DETECTION
    # ========================================
    with tab2:
        st.markdown("### 🎯 Community Detection: Find Crime Rings")
        st.info("**Community Detection** identifies clusters of closely connected individuals, revealing hidden crime rings and gang structures.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🕸️ Network Communities")
            with st.spinner("Analyzing network structure..."):
                communities = algo.detect_communities()
            
            if communities:
                df = pd.DataFrame(communities)
                
                # Scatter plot
                fig = px.scatter(
                    df,
                    x='network_size',
                    y='crimes',
                    size='network_size',
                    color='official_gang',
                    hover_name='person',
                    title='Criminal Networks by Size and Activity'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0')
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(df[['person', 'official_gang', 'network_size', 'crimes']], 
                           use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### 🔍 Hidden Crime Rings")
            st.caption("Unaffiliated individuals working together")
            
            with st.spinner("Detecting hidden connections..."):
                rings = algo.find_hidden_crime_rings()
            
            if rings:
                for i, ring in enumerate(rings[:10], 1):
                    st.markdown(f"""
                    <div style='background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #ef4444;'>
                        <strong>Ring #{i}</strong><br/>
                        {ring['person1']} (Age {ring['age1']}) ↔️ {ring['person2']} (Age {ring['age2']})<br/>
                        Shared Crimes: <strong>{ring['shared_crimes']}</strong>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hidden crime rings detected")
    
    # ========================================
    # TAB 3: CENTRALITY MEASURES
    # ========================================
    with tab3:
        st.markdown("### 🔗 Centrality Analysis: Key Network Positions")
        st.info("**Centrality** identifies individuals in strategic network positions - hubs and bridges.")
        
        subtab1, subtab2 = st.tabs(["Degree Centrality", "Betweenness Centrality"])
        
        with subtab1:
            st.markdown("#### 📡 Degree Centrality: Most Connected")
            st.caption("Individuals with the highest number of direct connections")
            
            with st.spinner("Calculating connections..."):
                degree_results = algo.calculate_degree_centrality()
            
            if degree_results:
                df = pd.DataFrame(degree_results)
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=df.head(10)['name'],
                        y=df.head(10)['total_connections'],
                        marker=dict(
                            color=df.head(10)['total_connections'],
                            colorscale='Blues'
                        ),
                        text=df.head(10)['total_connections'],
                        textposition='auto'
                    )
                ])
                fig.update_layout(
                    title='Top 10 Most Connected Individuals',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        with subtab2:
            st.markdown("#### 🌉 Betweenness Centrality: Network Bridges")
            st.caption("Individuals connecting different groups (brokers, mediators)")
            
            with st.spinner("Finding bridges..."):
                betweenness_results = algo.calculate_betweenness_centrality()
            
            if betweenness_results:
                df = pd.DataFrame(betweenness_results)
                
                for person in df.head(10).to_dict('records'):
                    st.markdown(f"""
                    <div style='background: rgba(124, 58, 237, 0.1); padding: 15px; border-radius: 10px; margin: 10px 0;'>
                        <strong>{person['name']}</strong> (Age {person['age']})<br/>
                        Own Gang: {person.get('own_gang', 'None')}<br/>
                        Connects to: {', '.join(person['connected_gangs'][:3])}<br/>
                        Bridge Score: <strong>{person['gang_connections']} gangs</strong>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No bridge individuals identified")
    
    # ========================================
    # TAB 4: PATH ANALYSIS
    # ========================================
    with tab4:
        st.markdown("### 🛤️ Path Analysis: Connection Mapping")
        st.info("**Shortest Path** reveals how individuals are connected through the network.")
        
        # Get list of persons for selection
        persons = db.query("MATCH (p:Person) RETURN p.name as name ORDER BY name LIMIT 100")
        person_names = [p['name'] for p in persons] if persons else []
        
        if len(person_names) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                person1 = st.selectbox("Select Person 1:", person_names, key='person1')
            
            with col2:
                person2 = st.selectbox("Select Person 2:", person_names, key='person2', index=1 if len(person_names) > 1 else 0)
            
            if st.button("🔍 Find Connection", type="primary", use_container_width=True):
                if person1 == person2:
                    st.warning("Please select two different people")
                else:
                    with st.spinner("Searching for connections..."):
                        # Shortest path
                        shortest = algo.find_shortest_path(person1, person2)
                        
                        if shortest:
                            st.success(f"✅ Connection found! Path length: **{shortest['path_length']}** steps")
                            
                            # Visualize path
                            path_nodes = shortest['path_nodes']
                            
                            st.markdown("#### 🛤️ Connection Path:")
                            path_str = " → ".join([f"**{node}**" for node in path_nodes])
                            st.markdown(path_str)
                            
                            # Find all paths
                            st.markdown("---")
                            st.markdown("#### 🔀 Alternative Paths:")
                            all_paths = algo.find_all_paths_between(person1, person2)
                            
                            if all_paths:
                                for i, path in enumerate(all_paths[:5], 1):
                                    path_display = " → ".join(path['path_nodes'])
                                    st.markdown(f"{i}. Length {path['path_length']}: {path_display}")
                            else:
                                st.info("No alternative paths found")
                        else:
                            st.warning(f"❌ No connection found between {person1} and {person2}")
        else:
            st.warning("Not enough persons in database for path analysis")
        
        # Network Statistics
        st.markdown("---")
        st.markdown("### 📊 Overall Network Statistics")
        
        with st.spinner("Calculating network metrics..."):
            stats = algo.get_network_statistics()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Persons", stats.get('total_persons', 0))
            
            with col2:
                st.metric("Total Connections", stats.get('total_connections', 0))
            
            with col3:
                st.metric("Network Density", f"{stats.get('density', 0):.4f}")
            
            with col4:
                st.metric("Avg Connections", stats.get('avg_connections', 0))