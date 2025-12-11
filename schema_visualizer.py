# schema_visualizer.py - Knowledge Graph Schema Visualization
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import math

class SchemaVisualizer:
    """Visualize the knowledge graph schema/data model"""
    
    def __init__(self, db):
        self.db = db
        
        # Entity colors matching your theme
        self.entity_colors = {
            'Person': '#F97316',
            'Crime': '#3B82F6',
            'Organization': '#EAB308',
            'Location': '#10B981',
            'Evidence': '#EC4899',
            'Vehicle': '#06B6D4',
            'Weapon': '#DC2626',
            'Investigator': '#8B5CF6',
            'ModusOperandi': '#F59E0B'
        }
    
    def get_schema_data(self):
        """Extract complete schema from the graph database"""
        
        # Get all node types and counts
        node_query = """
        MATCH (n)
        WITH DISTINCT labels(n)[0] as node_type, count(n) as count
        RETURN node_type, count
        ORDER BY count DESC
        """
        node_types = self.db.query(node_query)
        
        # Get all relationship types with source and target
        rel_query = """
        MATCH (a)-[r]->(b)
        WITH DISTINCT 
            labels(a)[0] as source_type,
            type(r) as relationship_type,
            labels(b)[0] as target_type,
            count(r) as count
        RETURN source_type, relationship_type, target_type, count
        ORDER BY count DESC
        """
        relationships = self.db.query(rel_query)
        
        # Get sample properties for each node type
        properties = {}
        for node in node_types:
            node_type = node['node_type']
            prop_query = f"""
            MATCH (n:{node_type})
            WITH n LIMIT 1
            RETURN keys(n) as properties
            """
            try:
                result = self.db.query(prop_query)
                if result:
                    properties[node_type] = result[0]['properties']
            except:
                properties[node_type] = []
        
        return {
            'nodes': node_types,
            'relationships': relationships,
            'properties': properties
        }
    
    def render_schema_page(self):
        """Render the complete schema visualization page"""
        
        st.markdown("## 📐 Knowledge Graph Schema")
        st.markdown("Visual representation of the graph data model - entities, relationships, and structure")
        st.markdown("---")
        
        # Get schema data
        with st.spinner("🔍 Analyzing graph schema..."):
            schema = self.get_schema_data()
        
        # ========================================
        # OVERVIEW METRICS
        # ========================================
        st.markdown("### 📊 Schema Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Entity Types", len(schema['nodes']))
        
        with col2:
            st.metric("🔗 Relationship Types", len(set(r['relationship_type'] for r in schema['relationships'])))
        
        with col3:
            total_nodes = sum(n['count'] for n in schema['nodes'])
            st.metric("🔵 Total Nodes", f"{total_nodes:,}")
        
        with col4:
            total_rels = sum(r['count'] for r in schema['relationships'])
            st.metric("➡️ Total Relationships", f"{total_rels:,}")
        
        st.markdown("---")
        
        # ========================================
        # INTERACTIVE SCHEMA DIAGRAM
        # ========================================
        st.markdown("### 🗺️ Interactive Schema Diagram")
        st.info("💡 Hover over entities to see properties • Click relationships to see details")
        
        self._render_interactive_schema(schema)
        
        st.markdown("---")
        
        # ========================================
        # ENTITY TYPES TABLE
        # ========================================
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📦 Entity Types")
            
            df_entities = pd.DataFrame(schema['nodes'])
            
            # Add properties column
            df_entities['properties'] = df_entities['node_type'].apply(
                lambda x: ', '.join(schema['properties'].get(x, [])[:5])
            )
            
            df_entities.columns = ['Entity Type', 'Count', 'Sample Properties']
            
            # Color code by count
            def color_by_count(row):
                count = row['Count']
                if count > 100:
                    return ['background-color: rgba(239, 68, 68, 0.2)'] * len(row)
                elif count > 50:
                    return ['background-color: rgba(245, 158, 11, 0.2)'] * len(row)
                else:
                    return ['background-color: rgba(59, 130, 246, 0.2)'] * len(row)
            
            styled = df_entities.style.apply(color_by_count, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True, height=400)
        
        with col2:
            st.markdown("### 🔗 Relationship Types")
            
            # Group relationships
            rel_summary = {}
            for rel in schema['relationships']:
                rel_type = rel['relationship_type']
                if rel_type not in rel_summary:
                    rel_summary[rel_type] = {
                        'type': rel_type,
                        'count': 0,
                        'patterns': []
                    }
                rel_summary[rel_type]['count'] += rel['count']
                rel_summary[rel_type]['patterns'].append(
                    f"{rel['source_type']}→{rel['target_type']}"
                )
            
            # Create dataframe
            rel_data = []
            for rel_type, data in rel_summary.items():
                rel_data.append({
                    'Relationship': rel_type,
                    'Count': data['count'],
                    'Pattern': ', '.join(set(data['patterns']))[:50]
                })
            
            df_rels = pd.DataFrame(rel_data).sort_values('Count', ascending=False)
            
            st.dataframe(df_rels, use_container_width=True, hide_index=True, height=400)
        
        st.markdown("---")
        
        # ========================================
        # DETAILED PROPERTY VIEW
        # ========================================
        st.markdown("### 🔍 Entity Properties Detail")
        
        selected_entity = st.selectbox(
            "Select entity type to view properties:",
            [n['node_type'] for n in schema['nodes']]
        )
        
        if selected_entity:
            props = schema['properties'].get(selected_entity, [])
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"#### {selected_entity} Properties")
                
                for prop in props:
                    st.markdown(f"- `{prop}`")
                
                if not props:
                    st.info("No properties found")
            
            with col2:
                st.markdown(f"#### Sample {selected_entity} Data")
                
                # Get sample data
                sample_query = f"""
                MATCH (n:{selected_entity})
                RETURN n
                LIMIT 3
                """
                
                try:
                    samples = self.db.query(sample_query)
                    if samples:
                        for i, sample in enumerate(samples, 1):
                            node_data = sample['n']
                            st.markdown(f"**Sample {i}:**")
                            st.json(dict(node_data), expanded=False)
                except Exception as e:
                    st.error(f"Error fetching samples: {e}")
        
        st.markdown("---")
        
        # ========================================
        # RELATIONSHIP MATRIX
        # ========================================
        st.markdown("### 🔄 Relationship Cardinality Matrix")
        st.caption("Shows how different entity types connect")
        
        # Create adjacency matrix
        entity_types = [n['node_type'] for n in schema['nodes']]
        matrix_data = {et: {et2: 0 for et2 in entity_types} for et in entity_types}
        
        for rel in schema['relationships']:
            source = rel['source_type']
            target = rel['target_type']
            if source in matrix_data and target in matrix_data[source]:
                matrix_data[source][target] += rel['count']
        
        # Create heatmap
        matrix_df = pd.DataFrame(matrix_data).fillna(0)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix_df.values,
            x=matrix_df.columns,
            y=matrix_df.index,
            colorscale='Reds',
            text=matrix_df.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='%{y} → %{x}<br>Count: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Entity Relationship Matrix (Source → Target)',
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            xaxis_title="Target Entity",
            yaxis_title="Source Entity"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ========================================
        # SCHEMA STATISTICS
        # ========================================
        st.markdown("### 📈 Schema Quality Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Entity Distribution")
            
            # Pie chart of entity types
            fig = go.Figure(data=[go.Pie(
                labels=[n['node_type'] for n in schema['nodes']],
                values=[n['count'] for n in schema['nodes']],
                marker=dict(
                    colors=[self.entity_colors.get(n['node_type'], '#6b7280') for n in schema['nodes']]
                ),
                hole=0.4
            )])
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Relationship Distribution")
            
            # Get top relationship types
            rel_counts = {}
            for rel in schema['relationships']:
                rel_type = rel['relationship_type']
                rel_counts[rel_type] = rel_counts.get(rel_type, 0) + rel['count']
            
            top_rels = sorted(rel_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            
            fig = go.Figure(data=[go.Bar(
                x=[r[0] for r in top_rels],
                y=[r[1] for r in top_rels],
                marker=dict(
                    color=[r[1] for r in top_rels],
                    colorscale='Viridis'
                ),
                text=[r[1] for r in top_rels],
                textposition='outside'
            )])
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                xaxis_tickangle=-45,
                showlegend=False,
                yaxis_title="Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            st.markdown("#### Schema Complexity")
            
            # Calculate metrics
            avg_props_per_entity = sum(len(props) for props in schema['properties'].values()) / len(schema['properties'])
            avg_rels_per_entity = len(schema['relationships']) / len(schema['nodes'])
            
            st.metric("Avg Properties/Entity", f"{avg_props_per_entity:.1f}")
            st.metric("Avg Relationships/Entity", f"{avg_rels_per_entity:.1f}")
            
            # Most connected entity
            entity_rel_counts = {}
            for rel in schema['relationships']:
                source = rel['source_type']
                target = rel['target_type']
                entity_rel_counts[source] = entity_rel_counts.get(source, 0) + 1
                entity_rel_counts[target] = entity_rel_counts.get(target, 0) + 1
            
            if entity_rel_counts:
                most_connected = max(entity_rel_counts.items(), key=lambda x: x[1])
                st.metric("Most Connected Entity", most_connected[0], 
                         delta=f"{most_connected[1]} rel types")
    
    def _render_interactive_schema(self, schema):
        """Render interactive schema diagram using Plotly"""
        
        # Define layout positions for entities (circular layout)
        entity_types = [n['node_type'] for n in schema['nodes']]
        n_entities = len(entity_types)
        
        positions = {}
        radius = 3
        
        for i, entity in enumerate(entity_types):
            angle = (2 * math.pi * i) / n_entities
            positions[entity] = {
                'x': radius * math.cos(angle),
                'y': radius * math.sin(angle)
            }
        
        # Create figure
        fig = go.Figure()
        
        # Add relationship arrows
        for rel in schema['relationships']:
            source = rel['source_type']
            target = rel['target_type']
            
            if source in positions and target in positions:
                source_pos = positions[source]
                target_pos = positions[target]
                
                # Calculate arrow position (don't overlap with nodes)
                dx = target_pos['x'] - source_pos['x']
                dy = target_pos['y'] - source_pos['y']
                length = math.sqrt(dx**2 + dy**2)
                
                # Skip if nodes are at same position (avoid division by zero)
                if length == 0:
                    continue
                
                # Shorten line to not overlap with circles
                offset = 0.4
                start_x = source_pos['x'] + (dx / length) * offset
                start_y = source_pos['y'] + (dy / length) * offset
                end_x = target_pos['x'] - (dx / length) * offset
                end_y = target_pos['y'] - (dy / length) * offset
                
                # Add arrow line
                fig.add_trace(go.Scatter(
                    x=[start_x, end_x],
                    y=[start_y, end_y],
                    mode='lines',
                    line=dict(
                        color='rgba(156, 163, 175, 0.4)',
                        width=max(1, min(5, rel['count'] / 50))  # Width based on count
                    ),
                    hovertemplate=(
                        f"<b>{rel['relationship_type']}</b><br>"
                        f"{source} → {target}<br>"
                        f"Count: {rel['count']}<br>"
                        f"<extra></extra>"
                    ),
                    showlegend=False,
                    name=rel['relationship_type']
                ))
                
                # Add arrow annotation
                fig.add_annotation(
                    x=end_x,
                    y=end_y,
                    ax=start_x,
                    ay=start_y,
                    xref='x',
                    yref='y',
                    axref='x',
                    ayref='y',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=max(1, min(3, rel['count'] / 100)),
                    arrowcolor='rgba(156, 163, 175, 0.6)',
                    text=rel['relationship_type'] if rel['count'] > 50 else '',
                    font=dict(size=9, color='#94a3b8'),
                    bgcolor='rgba(26, 31, 58, 0.8)',
                    borderpad=2
                )
        
        # Add entity nodes
        for node in schema['nodes']:
            entity_type = node['node_type']
            pos = positions[entity_type]
            count = node['count']
            props = schema['properties'].get(entity_type, [])
            
            # Node size based on count
            size = max(40, min(100, 40 + (count / 10)))
            
            color = self.entity_colors.get(entity_type, '#6b7280')
            
            # Create hover text
            hover_text = (
                f"<b>{entity_type}</b><br>"
                f"━━━━━━━━━━━━━━━━<br>"
                f"<b>Count:</b> {count} nodes<br>"
                f"<b>Properties:</b><br>"
                f"{', '.join(props[:8])}<br>"
                f"<extra></extra>"
            )
            
            # Add node
            fig.add_trace(go.Scatter(
                x=[pos['x']],
                y=[pos['y']],
                mode='markers+text',
                marker=dict(
                    size=size,
                    color=color,
                    line=dict(color='white', width=3)
                ),
                text=f"{entity_type}<br>({count})",
                textposition='middle center',
                textfont=dict(color='white', size=11, family='Inter, sans-serif'),
                hovertemplate=hover_text,
                showlegend=False,
                name=entity_type
            ))
        
        # Layout
        fig.update_layout(
            height=700,
            plot_bgcolor='rgba(15, 20, 25, 0.5)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                range=[-4, 4]
            ),
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                range=[-4, 4]
            ),
            hovermode='closest',
            margin=dict(l=0, r=0, t=40, b=0),
            title=dict(
                text='Knowledge Graph Schema - Entity-Relationship Model',
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#ffffff')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ========================================
        # RELATIONSHIP DETAILS
        # ========================================
        st.markdown("### 🔗 Relationship Type Details")
        
        # Create detailed relationship view
        rel_details = []
        for rel in schema['relationships']:
            # Determine cardinality
            source_count = next((n['count'] for n in schema['nodes'] if n['node_type'] == rel['source_type']), 0)
            target_count = next((n['count'] for n in schema['nodes'] if n['node_type'] == rel['target_type']), 0)
            
            if rel['count'] <= source_count and rel['count'] <= target_count:
                cardinality = "1:1 or 1:many"
            elif rel['count'] > source_count and rel['count'] > target_count:
                cardinality = "many:many"
            else:
                cardinality = "1:many"
            
            rel_details.append({
                'Relationship Type': rel['relationship_type'],
                'Pattern': f"{rel['source_type']} → {rel['target_type']}",
                'Count': rel['count'],
                'Cardinality': cardinality
            })
        
        df_rel_details = pd.DataFrame(rel_details).sort_values('Count', ascending=False)
        
        # Show with filtering
        with st.expander("📋 View All Relationship Details", expanded=True):
            st.dataframe(df_rel_details, use_container_width=True, hide_index=True, height=400)
        
        st.markdown("---")
        
        # ========================================
        # SCHEMA EXPORT
        # ========================================
        st.markdown("### 💾 Export Schema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export as JSON
            schema_json = json.dumps(schema, indent=2, default=str)
            st.download_button(
                label="📥 Download Schema (JSON)",
                data=schema_json,
                file_name="graph_schema.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Export as Cypher
            cypher_schema = self._generate_cypher_schema(schema)
            st.download_button(
                label="📥 Download Schema (Cypher)",
                data=cypher_schema,
                file_name="graph_schema.cypher",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            # Export as Markdown
            md_schema = self._generate_markdown_schema(schema)
            st.download_button(
                label="📥 Download Schema (Markdown)",
                data=md_schema,
                file_name="graph_schema.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    def _generate_cypher_schema(self, schema):
        """Generate Cypher CREATE statements for schema"""
        cypher = "// CrimeGraphRAG Knowledge Graph Schema\n"
        cypher += "// Generated Schema Documentation\n\n"
        
        cypher += "// ========================================\n"
        cypher += "// ENTITY TYPES\n"
        cypher += "// ========================================\n\n"
        
        for node in schema['nodes']:
            entity = node['node_type']
            props = schema['properties'].get(entity, [])
            
            cypher += f"// {entity} ({node['count']} nodes)\n"
            cypher += f"CREATE (:{entity} {{\n"
            
            for i, prop in enumerate(props):
                comma = "," if i < len(props) - 1 else ""
                cypher += f"  {prop}: <value>{comma}\n"
            
            cypher += "})\n\n"
        
        cypher += "// ========================================\n"
        cypher += "// RELATIONSHIPS\n"
        cypher += "// ========================================\n\n"
        
        for rel in schema['relationships']:
            cypher += f"// {rel['relationship_type']}: {rel['source_type']} → {rel['target_type']} ({rel['count']} relationships)\n"
            cypher += f"MATCH (a:{rel['source_type']}), (b:{rel['target_type']})\n"
            cypher += f"CREATE (a)-[:{rel['relationship_type']}]->(b)\n\n"
        
        return cypher
    
    def _generate_markdown_schema(self, schema):
        """Generate Markdown documentation for schema"""
        md = "# CrimeGraphRAG Knowledge Graph Schema\n\n"
        md += "## Overview\n\n"
        
        total_nodes = sum(n['count'] for n in schema['nodes'])
        total_rels = sum(r['count'] for r in schema['relationships'])
        unique_rel_types = len(set(r['relationship_type'] for r in schema['relationships']))
        
        md += f"- **Entity Types:** {len(schema['nodes'])}\n"
        md += f"- **Relationship Types:** {unique_rel_types}\n"
        md += f"- **Total Nodes:** {total_nodes:,}\n"
        md += f"- **Total Relationships:** {total_rels:,}\n\n"
        
        md += "## Entity Types\n\n"
        
        for node in schema['nodes']:
            entity = node['node_type']
            props = schema['properties'].get(entity, [])
            
            md += f"### {entity}\n\n"
            md += f"**Count:** {node['count']} nodes\n\n"
            md += f"**Properties:**\n"
            
            for prop in props:
                md += f"- `{prop}`\n"
            
            md += "\n"
        
        md += "## Relationship Types\n\n"
        md += "| Relationship | Pattern | Count | Cardinality |\n"
        md += "|-------------|---------|-------|-------------|\n"
        
        rel_summary = {}
        for rel in schema['relationships']:
            rel_type = rel['relationship_type']
            if rel_type not in rel_summary:
                rel_summary[rel_type] = {
                    'count': 0,
                    'patterns': []
                }
            rel_summary[rel_type]['count'] += rel['count']
            rel_summary[rel_type]['patterns'].append(f"{rel['source_type']}→{rel['target_type']}")
        
        for rel_type, data in sorted(rel_summary.items(), key=lambda x: x[1]['count'], reverse=True):
            pattern = ', '.join(set(data['patterns']))
            md += f"| {rel_type} | {pattern} | {data['count']} | - |\n"
        
        return md


def render_schema_page(db):
    """Main entry point for schema visualization page"""
    visualizer = SchemaVisualizer(db)
    visualizer.render_schema_page()


# For testing
if __name__ == "__main__":
    from database import Database
    
    st.set_page_config(page_title="Schema Visualizer", layout="wide")
    db = Database()
    render_schema_page(db)