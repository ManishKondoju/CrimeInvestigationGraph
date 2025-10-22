import streamlit as st
from database import Database
from graph_rag import GraphRAG
import plotly.express as px
import pandas as pd
from datetime import datetime
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(
    page_title="🔍 CrimeGraphRAG",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stMetric label, .stMetric [data-testid="stMetricValue"] {
        color: white !important;
    }
    
    .crime-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 5px 18px;
        margin: 10px 0 10px 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: white;
        color: #333;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 5px;
        margin: 10px 20% 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin: 20px 0;
    }
    
    .timestamp {
        font-size: 0.75rem;
        color: #999;
        margin-top: 5px;
    }
    
    .source-badge {
        background: #e3f2fd;
        color: #1976d2;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'rag' not in st.session_state:
    st.session_state.rag = GraphRAG()

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = []

# Sidebar
with st.sidebar:
    st.markdown("# 🔍 CrimeGraphRAG")
    st.markdown("### AI Investigation System")
    st.markdown("---")
    
    page = st.radio("Navigation", [
        "🏠 Dashboard",
        "💬 Ask AI Assistant",
        "🕸️ Network Visualization"
    ])
    
    st.markdown("---")
    
    try:
        stats = st.session_state.db.query("""
            MATCH (c:Crime) WITH count(c) as crimes
            MATCH (p:Person) WITH crimes, count(p) as persons
            MATCH (l:Location) WITH crimes, persons, count(l) as locations
            MATCH (o:Organization)
            RETURN crimes, persons, locations, count(o) as organizations
        """)[0]
        
        st.markdown("### 📊 Database")
        st.metric("🚨 Crimes", stats['crimes'])
        st.metric("👥 Persons", stats['persons'])
        st.metric("📍 Locations", stats['locations'])
        st.metric("🏢 Orgs", stats['organizations'])
        
        st.markdown("---")
        st.success("✅ Connected")
        
    except Exception as e:
        st.error("⚠️ Database Error")

# ========== DASHBOARD ==========
if page == "🏠 Dashboard":
    st.title("🏠 Crime Investigation Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        stats = st.session_state.db.query("""
            MATCH (c:Crime) WITH count(c) as crimes
            MATCH (p:Person) WITH crimes, count(p) as persons
            MATCH (l:Location) WITH crimes, persons, count(l) as locations
            MATCH ()-[r:PARTY_TO]->()
            RETURN crimes, persons, locations, count(r) as connections
        """)[0]
        
        col1.metric("📊 Total Crimes", stats['crimes'])
        col2.metric("👥 Total Suspects", stats['persons'])
        col3.metric("📍 Locations", stats['locations'])
        col4.metric("🔗 Connections", stats['connections'])
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🔥 Crime Hotspots")
        hotspots = st.session_state.db.query("""
            MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
            RETURN l.name as location, count(c) as crimes
            ORDER BY crimes DESC
            LIMIT 10
        """)
        
        if hotspots:
            df = pd.DataFrame(hotspots)
            fig = px.bar(df, x='location', y='crimes', 
                        color='crimes',
                        color_continuous_scale='Reds')
            fig.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.subheader("📊 Crime Types")
        types = st.session_state.db.query("""
            MATCH (c:Crime)
            RETURN c.type as type, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        if types:
            df2 = pd.DataFrame(types)
            fig2 = px.pie(df2, names='type', values='count', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📰 Recent Activity")
    
    recent = st.session_state.db.query("""
        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
        RETURN c.type as type, c.date as date, c.time as time, l.name as location
        ORDER BY c.date DESC, c.time DESC
        LIMIT 5
    """)
    
    if recent:
        for crime in recent:
            st.markdown(f"""
                <div class='crime-card'>
                    <b>🚨 {crime['type']}</b> at <b>{crime['location']}</b><br>
                    <small>📅 {crime['date']} • 🕐 {crime['time']}</small>
                </div>
            """, unsafe_allow_html=True)

# ========== CHATBOT ==========
elif page == "💬 Ask AI Assistant":
    
    col_title, col_btn1, col_btn2 = st.columns([3, 1, 1])
    
    with col_title:
        st.title("💬 AI Assistant")
        st.caption("🤖 Powered by Graph RAG")
    
    with col_btn1:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_btn"):
            st.session_state.chat_messages = []
            st.session_state.conversation_context = []
            st.rerun()
    
    with col_btn2:
        if st.button("✨ New", use_container_width=True, type="primary", key="new_btn"):
            st.session_state.chat_messages = []
            st.session_state.conversation_context = []
            st.rerun()
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Welcome message
        if len(st.session_state.chat_messages) == 0:
            st.markdown("""
                <div class='welcome-card'>
                    <h2>👋 Welcome Detective!</h2>
                    <p style='font-size: 1.1rem; margin: 20px 0;'>
                        Ask me anything about crimes, suspects, gangs, or evidence.
                    </p>
                    <p style='font-size: 0.9rem;'>
                        💡 Try: "Which gangs operate in Chicago?" or click an example below!
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        # Display messages
        for i, message in enumerate(st.session_state.chat_messages):
            timestamp = message.get('timestamp', datetime.now().strftime("%H:%M"))
            
            if message["role"] == "user":
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <div class='user-message'>
                            <strong>🕵️ You</strong><br>
                            {message['content']}
                            <div class='timestamp'>{timestamp}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='text-align: left;'>
                        <div class='assistant-message'>
                            <strong>🤖 Assistant</strong><br>
                            {message['content']}
                            <div class='timestamp'>{timestamp}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if 'sources' in message and message['sources']:
                    sources_html = "".join([
                        f"<span class='source-badge'>{s.replace('_', ' ').title()}</span>"
                        for s in message['sources'][:4]
                    ])
                    st.markdown(f"<div style='margin: 5px 0 10px 20px;'>{sources_html}</div>", 
                              unsafe_allow_html=True)
    
    # Example buttons
    st.markdown("---")
    st.markdown("### 💡 Quick Examples")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏢 Gangs", use_container_width=True, key="ex1"):
            st.session_state.pending_question = "Which criminal organizations operate in Chicago?"
    
    with col2:
        if st.button("🔍 Network", use_container_width=True, key="ex2"):
            st.session_state.pending_question = "Show me everyone connected to Marcus Rivera"
    
    with col3:
        if st.button("🔗 Evidence", use_container_width=True, key="ex3"):
            st.session_state.pending_question = "What evidence do we have?"
    
    with col4:
        if st.button("⚠️ Armed", use_container_width=True, key="ex4"):
            st.session_state.pending_question = "Which gang members own weapons?"
    
    st.markdown("---")
    
    # Handle pending question from buttons
    if 'pending_question' in st.session_state:
        user_input = st.session_state.pending_question
        del st.session_state.pending_question
        
        # Add to messages
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        st.session_state.conversation_context.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response
        with st.spinner("🔍 Analyzing..."):
            try:
                result = st.session_state.rag.ask_with_context(
                    user_input, 
                    st.session_state.conversation_context[-10:]
                )
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result['answer'],
                    "sources": result.get('sources', []),
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                st.session_state.conversation_context.append({
                    "role": "assistant",
                    "content": result['answer']
                })
            except Exception as e:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Error: {str(e)}\n\nPlease try another question.",
                    "sources": [],
                    "timestamp": datetime.now().strftime("%H:%M")
                })
        
        st.rerun()
    
    # Chat input
    user_input = st.chat_input("💭 Type your question here...", key="chat_input")
    
    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        st.session_state.conversation_context.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response
        with st.spinner("🔍 Analyzing..."):
            try:
                result = st.session_state.rag.ask_with_context(
                    user_input, 
                    st.session_state.conversation_context[-10:]
                )
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result['answer'],
                    "sources": result.get('sources', []),
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                st.session_state.conversation_context.append({
                    "role": "assistant",
                    "content": result['answer']
                })
                
            except Exception as e:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Error: {str(e)}\n\nPlease try rephrasing your question.",
                    "sources": [],
                    "timestamp": datetime.now().strftime("%H:%M")
                })
        
        st.rerun()

# ========== NEO4J-STYLE NETWORK ==========
elif page == "🕸️ Network Visualization":
    st.title("🕸️ Network Visualization")
    st.markdown("### Interactive Graph Explorer")
    
    # Simple controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        network_size = st.slider("Network Size", 20, 100, 50)
    
    with col2:
        focus = st.selectbox("Focus", ["All", "Gang Networks", "Specific Person"])
    
    with col3:
        st.write("")
        st.write("")
        generate = st.button("🔄 Generate", type="primary", use_container_width=True)
    
    # Person selector for focused view
    if focus == "Specific Person":
        persons = st.session_state.db.query("""
            MATCH (p:Person)
            RETURN DISTINCT p.name as name
            ORDER BY name
        """)
        if persons:
            person_list = [p['name'] for p in persons]
            st.info(f"📊 Found {len(person_list)} persons in database")
            selected_person = st.selectbox("Select Person", person_list)
    
    st.markdown("---")
    
    if generate:
        with st.spinner("🎨 Generating network..."):
            try:
                # Build query
                if focus == "Specific Person":
                    query = f"""
                    MATCH (p:Person {{name: '{selected_person}'}})-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                    OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
                    OPTIONAL MATCH (p)-[:KNOWS]-(p2:Person)
                    RETURN p.name as person, c.id as crime_id, c.type as crime_type,
                           l.name as location, o.name as organization,
                           collect(DISTINCT p2.name)[0..10] as connections
                    LIMIT {network_size}
                    """
                elif focus == "Gang Networks":
                    query = f"""
                    MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
                    MATCH (p)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                    RETURN p.name as person, o.name as organization,
                           c.id as crime_id, c.type as crime_type, l.name as location
                    LIMIT {network_size}
                    """
                else:
                    query = f"""
                    MATCH (p:Person)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                    OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
                    RETURN p.name as person, c.id as crime_id, c.type as crime_type,
                           l.name as location, o.name as organization
                    LIMIT {network_size}
                    """
                
                data = st.session_state.db.query(query)
                
                if data:
                    # Create network with Neo4j styling
                    net = Network(height='700px', width='100%', 
                                bgcolor='#ffffff', font_color='black')
                    
                    # Neo4j-style physics
                    net.set_options("""
                    {
                        "nodes": {
                            "borderWidth": 2,
                            "font": {"size": 14, "face": "Arial"},
                            "shadow": true
                        },
                        "edges": {
                            "smooth": {"type": "continuous"},
                            "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
                            "color": {"inherit": false}
                        },
                        "physics": {
                            "barnesHut": {
                                "gravitationalConstant": -30000,
                                "centralGravity": 0.3,
                                "springLength": 150,
                                "damping": 0.09
                            },
                            "stabilization": {"iterations": 200}
                        },
                        "interaction": {
                            "hover": true,
                            "tooltipDelay": 100,
                            "navigationButtons": true
                        }
                    }
                    """)
                    
                    # Neo4j color palette
                    COLORS = {
                        'Person': '#FFA07A',
                        'Crime': '#9FC5E8',
                        'Location': '#B4D7A8',
                        'Organization': '#E69138'
                    }
                    
                    nodes_added = set()
                    
                    # Add nodes
                    for record in data:
                        person = record.get('person')
                        crime_id = record.get('crime_id')
                        crime_type = record.get('crime_type')
                        location = record.get('location')
                        org = record.get('organization')
                        
                        # Person
                        if person and person not in nodes_added:
                            net.add_node(person, label=person, 
                                       color=COLORS['Person'], size=30,
                                       title=f"Person: {person}")
                            nodes_added.add(person)
                        
                        # Crime
                        if crime_id and crime_id not in nodes_added:
                            net.add_node(crime_id, label=crime_type,
                                       color=COLORS['Crime'], size=25,
                                       title=f"Crime: {crime_type}")
                            nodes_added.add(crime_id)
                        
                        # Location
                        if location and location not in nodes_added:
                            net.add_node(location, label=location,
                                       color=COLORS['Location'], size=25,
                                       title=f"Location: {location}")
                            nodes_added.add(location)
                        
                        # Organization
                        if org and org not in nodes_added:
                            net.add_node(org, label=org,
                                       color=COLORS['Organization'], size=35,
                                       title=f"Organization: {org}")
                            nodes_added.add(org)
                        
                        # Edges
                        if person and crime_id:
                            net.add_edge(person, crime_id, color='#848484', width=2)
                        
                        if crime_id and location:
                            net.add_edge(crime_id, location, color='#848484', width=2)
                        
                        if person and org:
                            net.add_edge(person, org, color='#E69138', width=3)
                    
                    # Add social connections
                    knows = st.session_state.db.query("""
                        MATCH (p1:Person)-[:KNOWS]-(p2:Person)
                        WHERE EXISTS((p1)-[:PARTY_TO]->(:Crime))
                        RETURN p1.name as p1, p2.name as p2
                        LIMIT 30
                    """)
                    
                    for k in knows:
                        if k['p1'] in nodes_added and k['p2'] in nodes_added:
                            net.add_edge(k['p1'], k['p2'], 
                                       color='#D3D3D3', width=1.5, dashes=True)
                    
                    # Save
                    net.save_graph('network.html')
                    
                    with open('network.html', 'r') as f:
                        st.session_state.network_html = f.read()
                    
                    st.success(f"✅ Generated {len(nodes_added)} nodes")
                    
            except Exception as e:
                st.error(f"⚠️ Error generating network: {str(e)}")
    
    # Display
    if 'network_html' in st.session_state:
        st.markdown("---")
        components.html(st.session_state.network_html, height=700)
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown("🟠 **Person**")
        col2.markdown("🔵 **Crime**")
        col3.markdown("🟢 **Location**")
        col4.markdown("🟡 **Organization**")
    else:
        st.info("👆 Click 'Generate' to visualize the network")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <b>🔍 CrimeGraphRAG</b> | Neo4j + GPT + ML
    </div>
""", unsafe_allow_html=True)