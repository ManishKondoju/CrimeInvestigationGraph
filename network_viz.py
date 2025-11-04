# network_viz.py - Clean D3.js Network Visualization
import streamlit as st
import streamlit.components.v1 as components
from database import Database
import json

class NetworkVisualization:
    def __init__(self, db: Database):
        self.db = db
        
        # Entity type color mapping
        self.color_map = {
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
    
    def get_all_entities_of_type(self, entity_type):
        """Get all entities of a specific type"""
        if entity_type == "Organization":
            query = """
            MATCH (n:Organization)
            RETURN n.id as id, n.name as name
            ORDER BY n.name
            """
        elif entity_type == "Person":
            query = """
            MATCH (n:Person)
            RETURN n.id as id, n.name as name
            ORDER BY n.name
            """
        elif entity_type == "Crime":
            query = """
            MATCH (n:Crime)
            RETURN n.id as id, n.type as name
            ORDER BY n.date DESC
            """
        elif entity_type == "Location":
            query = """
            MATCH (n:Location)
            RETURN n.name as id, n.name as name
            ORDER BY n.name
            """
        else:
            query = f"""
            MATCH (n:{entity_type})
            RETURN n.id as id, n.name as name
            ORDER BY n.name
            """
        
        return self.db.query(query)
    
    def get_network_data(self, entity_type, specific_id=None):
        """Get network data based on entity type and optional specific entity"""
        nodes = []
        edges = []
        node_ids = set()
        
        if specific_id:
            # SPECIFIC ENTITY SELECTED
            if entity_type == "Organization":
                # ONLY Organization + Members
                org_query = """
                MATCH (o:Organization {id: $id})
                RETURN o
                """
                org_result = self.db.query(org_query, {"id": specific_id})
                
                if org_result:
                    org = org_result[0]['o']
                    nodes.append({
                        'id': org.get('id'),
                        'label': org.get('name'),
                        'type': 'Organization'
                    })
                    node_ids.add(org.get('id'))
                    
                    # Get members
                    members_query = """
                    MATCH (o:Organization {id: $id})<-[:MEMBER_OF]-(p:Person)
                    RETURN p
                    """
                    members = self.db.query(members_query, {"id": specific_id})
                    
                    for m in members:
                        person = m['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': person.get('id'),
                            'target': org.get('id'),
                            'label': 'MEMBER_OF'
                        })
            
            elif entity_type == "Person":
                # Person + Organization + Crimes + Weapons
                person_query = """
                MATCH (p:Person {id: $id})
                RETURN p
                """
                person_result = self.db.query(person_query, {"id": specific_id})
                
                if person_result:
                    person = person_result[0]['p']
                    pid = person.get('id')
                    
                    nodes.append({
                        'id': pid,
                        'label': person.get('name'),
                        'type': 'Person'
                    })
                    node_ids.add(pid)
                    
                    # Get organization
                    org_query = """
                    MATCH (p:Person {id: $id})-[:MEMBER_OF]->(o:Organization)
                    RETURN o
                    """
                    orgs = self.db.query(org_query, {"id": specific_id})
                    
                    for o in orgs:
                        org = o['o']
                        nodes.append({
                            'id': org.get('id'),
                            'label': org.get('name'),
                            'type': 'Organization'
                        })
                        node_ids.add(org.get('id'))
                        
                        edges.append({
                            'source': pid,
                            'target': org.get('id'),
                            'label': 'MEMBER_OF'
                        })
                    
                    # Get crimes
                    crimes_query = """
                    MATCH (p:Person {id: $id})-[:PARTY_TO]->(c:Crime)
                    RETURN c
                    """
                    crimes = self.db.query(crimes_query, {"id": specific_id})
                    
                    for c in crimes:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': pid,
                            'target': crime.get('id'),
                            'label': 'PARTY_TO'
                        })
                    
                    # Get weapons
                    weapons_query = """
                    MATCH (p:Person {id: $id})-[:OWNS]->(w:Weapon)
                    RETURN w
                    """
                    weapons = self.db.query(weapons_query, {"id": specific_id})
                    
                    for w in weapons:
                        weapon = w['w']
                        weapon_label = f"{weapon.get('make', '')} {weapon.get('model', '')}".strip()
                        nodes.append({
                            'id': weapon.get('id'),
                            'label': weapon_label or weapon.get('type'),
                            'type': 'Weapon'
                        })
                        node_ids.add(weapon.get('id'))
                        
                        edges.append({
                            'source': pid,
                            'target': weapon.get('id'),
                            'label': 'OWNS'
                        })
                    
                    # Get associates
                    assoc_query = """
                    MATCH (p:Person {id: $id})-[:KNOWS]-(other:Person)
                    RETURN other
                    """
                    associates = self.db.query(assoc_query, {"id": specific_id})
                    
                    for a in associates:
                        assoc = a['other']
                        nodes.append({
                            'id': assoc.get('id'),
                            'label': assoc.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(assoc.get('id'))
                        
                        edges.append({
                            'source': pid,
                            'target': assoc.get('id'),
                            'label': 'KNOWS'
                        })
            
            elif entity_type == "Crime":
                # Crime + Suspects + Location + Evidence
                crime_query = """
                MATCH (c:Crime {id: $id})
                RETURN c
                """
                crime_result = self.db.query(crime_query, {"id": specific_id})
                
                if crime_result:
                    crime = crime_result[0]['c']
                    cid = crime.get('id')
                    
                    nodes.append({
                        'id': cid,
                        'label': crime.get('type'),
                        'type': 'Crime'
                    })
                    node_ids.add(cid)
                    
                    # Suspects
                    suspects_query = """
                    MATCH (c:Crime {id: $id})<-[:PARTY_TO]-(p:Person)
                    RETURN p
                    """
                    suspects = self.db.query(suspects_query, {"id": specific_id})
                    
                    for s in suspects:
                        person = s['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': person.get('id'),
                            'target': cid,
                            'label': 'PARTY_TO'
                        })
                    
                    # Location
                    location_query = """
                    MATCH (c:Crime {id: $id})-[:OCCURRED_AT]->(l:Location)
                    RETURN l
                    """
                    locations = self.db.query(location_query, {"id": specific_id})
                    
                    for l in locations:
                        location = l['l']
                        nodes.append({
                            'id': location.get('name'),
                            'label': location.get('name')[:20],
                            'type': 'Location'
                        })
                        node_ids.add(location.get('name'))
                        
                        edges.append({
                            'source': cid,
                            'target': location.get('name'),
                            'label': 'OCCURRED_AT'
                        })
                    
                    # Evidence
                    evidence_query = """
                    MATCH (c:Crime {id: $id})-[:HAS_EVIDENCE]->(e:Evidence)
                    RETURN e
                    """
                    evidence = self.db.query(evidence_query, {"id": specific_id})
                    
                    for e in evidence:
                        ev = e['e']
                        nodes.append({
                            'id': ev.get('id'),
                            'label': ev.get('description'),
                            'type': 'Evidence'
                        })
                        node_ids.add(ev.get('id'))
                        
                        edges.append({
                            'source': cid,
                            'target': ev.get('id'),
                            'label': 'HAS_EVIDENCE'
                        })
                    
                    # Investigator
                    inv_query = """
                    MATCH (c:Crime {id: $id})-[:INVESTIGATED_BY]->(i:Investigator)
                    RETURN i
                    """
                    investigators = self.db.query(inv_query, {"id": specific_id})
                    
                    for i in investigators:
                        inv = i['i']
                        nodes.append({
                            'id': inv.get('id'),
                            'label': inv.get('name'),
                            'type': 'Investigator'
                        })
                        node_ids.add(inv.get('id'))
                        
                        edges.append({
                            'source': cid,
                            'target': inv.get('id'),
                            'label': 'INVESTIGATED_BY'
                        })
            
            elif entity_type == "Location":
                # Location + Crimes + Suspects
                loc_query = """
                MATCH (l:Location {name: $id})
                RETURN l
                """
                loc_result = self.db.query(loc_query, {"id": specific_id})
                
                if loc_result:
                    location = loc_result[0]['l']
                    lid = location.get('name')
                    
                    nodes.append({
                        'id': lid,
                        'label': location.get('name')[:20],
                        'type': 'Location'
                    })
                    node_ids.add(lid)
                    
                    # Get ALL crimes at this location
                    crimes_query = """
                    MATCH (l:Location {name: $id})<-[:OCCURRED_AT]-(c:Crime)
                    RETURN c
                    """
                    crimes = self.db.query(crimes_query, {"id": specific_id})
                    
                    for c in crimes:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': crime.get('id'),
                            'target': lid,
                            'label': 'OCCURRED_AT'
                        })
                    
                    # Get suspects
                    suspects_query = """
                    MATCH (l:Location {name: $id})<-[:OCCURRED_AT]-(c:Crime)<-[:PARTY_TO]-(p:Person)
                    RETURN DISTINCT p, c.id as crime_id
                    """
                    suspects = self.db.query(suspects_query, {"id": specific_id})
                    
                    for s in suspects:
                        person = s['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': person.get('id'),
                            'target': s['crime_id'],
                            'label': 'PARTY_TO'
                        })
            
            elif entity_type == "Investigator":
                # Investigator + Cases they're investigating
                inv_query = """
                MATCH (i:Investigator {id: $id})
                RETURN i
                """
                inv_result = self.db.query(inv_query, {"id": specific_id})
                
                if inv_result:
                    inv = inv_result[0]['i']
                    nodes.append({
                        'id': inv.get('id'),
                        'label': inv.get('name'),
                        'type': 'Investigator'
                    })
                    node_ids.add(inv.get('id'))
                    
                    # Get cases
                    cases_query = """
                    MATCH (i:Investigator {id: $id})<-[:INVESTIGATED_BY]-(c:Crime)
                    RETURN c
                    """
                    cases = self.db.query(cases_query, {"id": specific_id})
                    
                    for c in cases:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': crime.get('id'),
                            'target': inv.get('id'),
                            'label': 'INVESTIGATED_BY'
                        })
            
            elif entity_type == "Evidence":
                # Evidence + Crimes + Linked Persons
                ev_query = """
                MATCH (e:Evidence {id: $id})
                RETURN e
                """
                ev_result = self.db.query(ev_query, {"id": specific_id})
                
                if ev_result:
                    evidence = ev_result[0]['e']
                    nodes.append({
                        'id': evidence.get('id'),
                        'label': evidence.get('description'),
                        'type': 'Evidence'
                    })
                    node_ids.add(evidence.get('id'))
                    
                    # Get crimes with this evidence
                    crimes_query = """
                    MATCH (e:Evidence {id: $id})<-[:HAS_EVIDENCE]-(c:Crime)
                    RETURN c
                    """
                    crimes = self.db.query(crimes_query, {"id": specific_id})
                    
                    for c in crimes:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': crime.get('id'),
                            'target': evidence.get('id'),
                            'label': 'HAS_EVIDENCE'
                        })
                    
                    # Get linked persons
                    persons_query = """
                    MATCH (e:Evidence {id: $id})-[:LINKS_TO]->(p:Person)
                    RETURN p
                    """
                    persons = self.db.query(persons_query, {"id": specific_id})
                    
                    for p in persons:
                        person = p['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': evidence.get('id'),
                            'target': person.get('id'),
                            'label': 'LINKS_TO'
                        })
            
            elif entity_type == "Weapon":
                # Weapon + Owner + Crimes
                weapon_query = """
                MATCH (w:Weapon {id: $id})
                RETURN w
                """
                weapon_result = self.db.query(weapon_query, {"id": specific_id})
                
                if weapon_result:
                    weapon = weapon_result[0]['w']
                    weapon_label = f"{weapon.get('make', '')} {weapon.get('model', '')}".strip()
                    nodes.append({
                        'id': weapon.get('id'),
                        'label': weapon_label or weapon.get('type'),
                        'type': 'Weapon'
                    })
                    node_ids.add(weapon.get('id'))
                    
                    # Get owner
                    owner_query = """
                    MATCH (w:Weapon {id: $id})<-[:OWNS]-(p:Person)
                    RETURN p
                    """
                    owners = self.db.query(owner_query, {"id": specific_id})
                    
                    for o in owners:
                        person = o['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': person.get('id'),
                            'target': weapon.get('id'),
                            'label': 'OWNS'
                        })
                    
                    # Get crimes using this weapon
                    crimes_query = """
                    MATCH (w:Weapon {id: $id})<-[:USED_WEAPON]-(c:Crime)
                    RETURN c
                    """
                    crimes = self.db.query(crimes_query, {"id": specific_id})
                    
                    for c in crimes:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': crime.get('id'),
                            'target': weapon.get('id'),
                            'label': 'USED_WEAPON'
                        })
            
            elif entity_type == "Vehicle":
                # Vehicle + Owner + Crimes
                vehicle_query = """
                MATCH (v:Vehicle {id: $id})
                RETURN v
                """
                vehicle_result = self.db.query(vehicle_query, {"id": specific_id})
                
                if vehicle_result:
                    vehicle = vehicle_result[0]['v']
                    vehicle_label = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip()
                    nodes.append({
                        'id': vehicle.get('id'),
                        'label': vehicle_label or vehicle.get('license_plate'),
                        'type': 'Vehicle'
                    })
                    node_ids.add(vehicle.get('id'))
                    
                    # Get owner
                    owner_query = """
                    MATCH (v:Vehicle {id: $id})<-[:OWNS]-(p:Person)
                    RETURN p
                    """
                    owners = self.db.query(owner_query, {"id": specific_id})
                    
                    for o in owners:
                        person = o['p']
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                        
                        edges.append({
                            'source': person.get('id'),
                            'target': vehicle.get('id'),
                            'label': 'OWNS'
                        })
                    
                    # Get crimes involving this vehicle
                    crimes_query = """
                    MATCH (v:Vehicle {id: $id})<-[:INVOLVED_VEHICLE]-(c:Crime)
                    RETURN c
                    """
                    crimes = self.db.query(crimes_query, {"id": specific_id})
                    
                    for c in crimes:
                        crime = c['c']
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                        
                        edges.append({
                            'source': crime.get('id'),
                            'target': vehicle.get('id'),
                            'label': 'INVOLVED_VEHICLE'
                        })
        
        else:
            # VIEW ALL - Show all of this type
            if entity_type == "Organization":
                # ALL Organizations + their members ONLY
                org_query = """
                MATCH (o:Organization)
                RETURN o
                """
                orgs = self.db.query(org_query)
                
                for record in orgs:
                    org = record['o']
                    nodes.append({
                        'id': org.get('id'),
                        'label': org.get('name'),
                        'type': 'Organization'
                    })
                    node_ids.add(org.get('id'))
                
                # Get members
                members_query = """
                MATCH (o:Organization)<-[:MEMBER_OF]-(p:Person)
                RETURN o.id as org_id, p
                """
                members = self.db.query(members_query)
                
                for m in members:
                    person = m['p']
                    if person.get('id') not in node_ids:
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                    
                    edges.append({
                        'source': person.get('id'),
                        'target': m['org_id'],
                        'label': 'MEMBER_OF'
                    })
            
            elif entity_type == "Person":
                # ALL Persons + Orgs + Crimes
                person_query = """
                MATCH (p:Person)
                RETURN p
                """
                persons = self.db.query(person_query)
                
                for record in persons:
                    person = record['p']
                    nodes.append({
                        'id': person.get('id'),
                        'label': person.get('name'),
                        'type': 'Person'
                    })
                    node_ids.add(person.get('id'))
                
                # Get their organizations
                org_query = """
                MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
                RETURN p.id as person_id, o
                """
                orgs = self.db.query(org_query)
                
                for o in orgs:
                    org = o['o']
                    if org.get('id') not in node_ids:
                        nodes.append({
                            'id': org.get('id'),
                            'label': org.get('name'),
                            'type': 'Organization'
                        })
                        node_ids.add(org.get('id'))
                    
                    edges.append({
                        'source': o['person_id'],
                        'target': org.get('id'),
                        'label': 'MEMBER_OF'
                    })
                
                # Get crimes
                crimes_query = """
                MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
                RETURN p.id as person_id, c
                """
                crimes = self.db.query(crimes_query)
                
                for c in crimes:
                    crime = c['c']
                    if crime.get('id') not in node_ids:
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                    
                    edges.append({
                        'source': c['person_id'],
                        'target': crime.get('id'),
                        'label': 'PARTY_TO'
                    })
            
            elif entity_type == "Crime":
                # ALL Crimes + Locations + Suspects
                crime_query = """
                MATCH (c:Crime)
                RETURN c
                """
                crimes = self.db.query(crime_query)
                
                for record in crimes:
                    crime = record['c']
                    nodes.append({
                        'id': crime.get('id'),
                        'label': crime.get('type'),
                        'type': 'Crime'
                    })
                    node_ids.add(crime.get('id'))
                
                # Get locations
                loc_query = """
                MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
                RETURN c.id as crime_id, l
                """
                locations = self.db.query(loc_query)
                
                for l in locations:
                    location = l['l']
                    if location.get('name') not in node_ids:
                        nodes.append({
                            'id': location.get('name'),
                            'label': location.get('name')[:20],
                            'type': 'Location'
                        })
                        node_ids.add(location.get('name'))
                    
                    edges.append({
                        'source': l['crime_id'],
                        'target': location.get('name'),
                        'label': 'OCCURRED_AT'
                    })
                
                # Get suspects
                suspects_query = """
                MATCH (c:Crime)<-[:PARTY_TO]-(p:Person)
                RETURN c.id as crime_id, p
                """
                suspects = self.db.query(suspects_query)
                
                for s in suspects:
                    person = s['p']
                    if person.get('id') not in node_ids:
                        nodes.append({
                            'id': person.get('id'),
                            'label': person.get('name'),
                            'type': 'Person'
                        })
                        node_ids.add(person.get('id'))
                    
                    edges.append({
                        'source': person.get('id'),
                        'target': s['crime_id'],
                        'label': 'PARTY_TO'
                    })
            
            elif entity_type == "Location":
                # ALL Locations + Crimes
                loc_query = """
                MATCH (l:Location)
                RETURN l
                """
                locations = self.db.query(loc_query)
                
                for record in locations:
                    location = record['l']
                    nodes.append({
                        'id': location.get('name'),
                        'label': location.get('name')[:20],
                        'type': 'Location'
                    })
                    node_ids.add(location.get('name'))
                
                # Get crimes
                crimes_query = """
                MATCH (l:Location)<-[:OCCURRED_AT]-(c:Crime)
                RETURN l.name as loc_id, c
                """
                crimes = self.db.query(crimes_query)
                
                for c in crimes:
                    crime = c['c']
                    if crime.get('id') not in node_ids:
                        nodes.append({
                            'id': crime.get('id'),
                            'label': crime.get('type'),
                            'type': 'Crime'
                        })
                        node_ids.add(crime.get('id'))
                    
                    edges.append({
                        'source': crime.get('id'),
                        'target': c['loc_id'],
                        'label': 'OCCURRED_AT'
                    })
        
        return {'nodes': nodes, 'edges': edges}
    
    def render(self):
        """Render the network visualization"""
        
        st.markdown("### 🕸️ Network Visualization")
        
        # Row 1: Main entity type selector
        col1, col2 = st.columns([2, 3])
        
        with col1:
            entity_type = st.selectbox(
                "Select Entity Type",
                ["Organization", "Person", "Crime", "Location", "Investigator", "Evidence", "Weapon", "Vehicle"],
                help="Choose which type of entity to visualize"
            )
        
        with col2:
            # Specific entity selector
            entities = self.get_all_entities_of_type(entity_type)
            
            if entities:
                entity_options = {"- View All -": None}
                entity_options.update({e['name']: e['id'] for e in entities})
                
                selected_entity_name = st.selectbox(
                    f"Select Specific {entity_type} (Optional)",
                    list(entity_options.keys()),
                    help=f"Choose a specific {entity_type} to focus on, or view all"
                )
                
                selected_entity_id = entity_options[selected_entity_name]
            else:
                selected_entity_id = None
        
        st.markdown("---")
        
        # Fetch network data
        with st.spinner("Loading network..."):
            network_data = self.get_network_data(entity_type, selected_entity_id)
        
        # Show what's displayed
        if selected_entity_id:
            st.info(f"📍 Showing: {selected_entity_name} and connected entities")
        else:
            st.info(f"📍 Showing: All {entity_type}s and their connections")
        
        # Stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nodes", len(network_data['nodes']))
        with col2:
            st.metric("Edges", len(network_data['edges']))
        
        # Render D3.js visualization
        if network_data['nodes']:
            self._render_d3_network(network_data)
        else:
            st.warning("No data to display")
    
    def _render_d3_network(self, network_data):
        """Render clean D3.js network with legend"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: #ffffff;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    overflow: hidden;
                }}
                #graph {{ width: 100%; height: 700px; }}
                .node {{
                    cursor: pointer;
                    stroke: #fff;
                    stroke-width: 3px;
                }}
                .node:hover {{ 
                    stroke: #000;
                    stroke-width: 4px;
                }}
                .link {{
                    stroke: #cbd5e1;
                    stroke-opacity: 0.6;
                    stroke-width: 2px;
                }}
                .link-label {{
                    fill: #64748b;
                    font-size: 11px;
                    pointer-events: none;
                    text-anchor: middle;
                }}
                .node-label {{
                    fill: #1e293b;
                    font-size: 12px;
                    font-weight: 600;
                    pointer-events: none;
                    text-anchor: middle;
                }}
                #tooltip {{
                    position: absolute;
                    background: rgba(30, 41, 59, 0.95);
                    border: 2px solid #475569;
                    border-radius: 8px;
                    padding: 12px;
                    color: #e2e8f0;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.2s;
                    font-size: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    z-index: 1000;
                }}
                #legend {{
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
                    border: 2px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 16px 20px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
                }}
                #legend h4 {{
                    margin: 0 0 12px 0;
                    font-size: 14px;
                    font-weight: 700;
                    color: #0f172a;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 8px;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    margin: 8px 0;
                    font-size: 13px;
                    color: #334155;
                }}
                .legend-color {{
                    width: 14px;
                    height: 14px;
                    border-radius: 50%;
                    margin-right: 10px;
                    border: 2px solid rgba(0,0,0,0.1);
                }}
                .legend-count {{
                    margin-left: auto;
                    padding-left: 12px;
                    color: #64748b;
                    font-weight: 600;
                }}
                #instructions {{
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    background: rgba(59, 130, 246, 0.95);
                    border-radius: 8px;
                    padding: 10px 16px;
                    color: white;
                    font-size: 12px;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                }}
            </style>
        </head>
        <body>
            <div id="graph"></div>
            <div id="tooltip"></div>
            <div id="legend">
                <h4>🎨 Entity Legend</h4>
            </div>
            <div id="instructions">
                💡 <b>Drag</b> nodes • <b>Scroll</b> to zoom • <b>Hover</b> for details
            </div>
            
            <script>
                const data = {json.dumps(network_data)};
                const colorMap = {json.dumps(self.color_map)};
                
                const width = window.innerWidth;
                const height = 700;
                
                const svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                const g = svg.append("g");
                
                const zoom = d3.zoom()
                    .scaleExtent([0.3, 3])
                    .on("zoom", (event) => g.attr("transform", event.transform));
                
                svg.call(zoom);
                
                const simulation = d3.forceSimulation(data.nodes)
                    .force("link", d3.forceLink(data.edges).id(d => d.id).distance(120))
                    .force("charge", d3.forceManyBody().strength(-400))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("collision", d3.forceCollide().radius(40));
                
                const link = g.append("g")
                    .selectAll("line")
                    .data(data.edges)
                    .join("line")
                    .attr("class", "link");
                
                const linkLabel = g.append("g")
                    .selectAll("text")
                    .data(data.edges)
                    .join("text")
                    .attr("class", "link-label")
                    .text(d => d.label);
                
                const node = g.append("g")
                    .selectAll("circle")
                    .data(data.nodes)
                    .join("circle")
                    .attr("class", "node")
                    .attr("r", d => {{
                        if (d.type === 'Organization') return 30;
                        if (d.type === 'Crime') return 15;
                        if (d.type === 'Location') return 18;
                        if (d.type === 'Person') return 12;
                        return 10;
                    }})
                    .attr("fill", d => colorMap[d.type] || "#64748b")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended))
                    .on("mouseover", showTooltip)
                    .on("mouseout", hideTooltip);
                
                const nodeLabel = g.append("g")
                    .selectAll("text")
                    .data(data.nodes)
                    .join("text")
                    .attr("class", "node-label")
                    .text(d => d.label.length > 15 ? d.label.substring(0, 15) + "..." : d.label)
                    .attr("dy", d => d.type === 'Organization' ? 38 : 20);
                
                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);
                    
                    linkLabel
                        .attr("x", d => (d.source.x + d.target.x) / 2)
                        .attr("y", d => (d.source.y + d.target.y) / 2);
                    
                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);
                    
                    nodeLabel
                        .attr("x", d => d.x)
                        .attr("y", d => d.y);
                }});
                
                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}
                
                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}
                
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}
                
                function showTooltip(event, d) {{
                    const tooltip = d3.select("#tooltip");
                    let html = `<strong style="font-size: 14px;">${{d.label}}</strong><br/>`;
                    html += `<span style="color: #94a3b8;">Type: ${{d.type}}</span><br/>`;
                    html += `<span style="color: #94a3b8;">ID: ${{d.id}}</span>`;
                    
                    tooltip.html(html)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px")
                        .style("opacity", 1);
                }}
                
                function hideTooltip() {{
                    d3.select("#tooltip").style("opacity", 0);
                }}
                
                // Build dynamic legend
                const legendDiv = d3.select("#legend");
                const entityTypes = [...new Set(data.nodes.map(n => n.type))];
                const typeCounts = {{}};
                
                data.nodes.forEach(node => {{
                    typeCounts[node.type] = (typeCounts[node.type] || 0) + 1;
                }});
                
                const sortedTypes = entityTypes.sort((a, b) => (typeCounts[b] || 0) - (typeCounts[a] || 0));
                
                sortedTypes.forEach(type => {{
                    const color = colorMap[type] || '#64748b';
                    const count = typeCounts[type] || 0;
                    
                    const item = legendDiv.append('div')
                        .attr('class', 'legend-item');
                    
                    item.append('div')
                        .attr('class', 'legend-color')
                        .style('background-color', color);
                    
                    item.append('span')
                        .text(type);
                    
                    item.append('span')
                        .attr('class', 'legend-count')
                        .text(count);
                }});
            </script>
        </body>
        </html>
        """
        
        components.html(html_content, height=750, scrolling=False)


if __name__ == "__main__":
    from database import Database
    st.set_page_config(layout="wide")
    db = Database()
    viz = NetworkVisualization(db)
    viz.render()