# graph_rag_enhanced.py - KG-Aware Graph RAG
import config
from database import Database
import json
import re

class GraphRAG:
    def __init__(self):
        self.db = Database()
        self.model = config.MODEL_NAME
        
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
            self.use_llm = True
            print("✅ LLM initialized successfully")
        except Exception as e:
            print(f"⚠️ LLM unavailable: {e}")
            self.use_llm = False
    
    def ask(self, question):
        return self.ask_with_context(question, [])
    
    def ask_with_context(self, question, conversation_history):
        print(f"\n🔍 Processing question: {question}")
        
        # RETRIEVE with KG-awareness
        context, cypher_queries = self._kg_aware_retrieve(question, conversation_history)
        
        print(f"✅ Retrieved {len(context)} context keys")
        
        # GENERATE
        answer = ""
        
        if self.use_llm:
            try:
                answer = self._generate_with_llm(question, context, conversation_history)
                print(f"✅ LLM generated {len(answer)} chars")
                
                if not answer or len(answer.strip()) < 10:
                    answer = self._generate_fallback(question, context)
            except Exception as e:
                print(f"⚠️ LLM failed: {e}")
                answer = self._generate_fallback(question, context)
        else:
            answer = self._generate_fallback(question, context)
        
        # Final validation
        if not answer or len(answer.strip()) < 10:
            answer = self._generate_emergency_fallback(context)
        
        return {
            'answer': answer,
            'sources': list(context.keys()),
            'cypher_queries': cypher_queries,
            'context': context
        }
    
    def _kg_aware_retrieve(self, question, conversation_history):
        """ENHANCED: Knowledge Graph-aware retrieval"""
        context = {}
        cypher_queries = []
        q = question.lower()
        
        # Extract entities
        person_names = self._extract_person_names(question)
        
        # Always get basic stats
        try:
            query = "MATCH (c:Crime) RETURN count(c) as n"
            cypher_queries.append(("Database Stats", query))
            
            context['database_stats'] = {
                'total_crimes': self.db.query(query)[0]['n'],
                'total_persons': self.db.query("MATCH (p:Person) RETURN count(p) as n")[0]['n']
            }
        except Exception as e:
            print(f"❌ Stats error: {e}")
        
        # ========================================
        # KNOWLEDGE GRAPH SPECIFIC QUERIES
        # ========================================
        
        # 1. MULTI-HOP / N-DEGREE QUERIES
        if any(phrase in q for phrase in ['within', 'degrees of', 'degrees from', 'connections of', 'network of']):
            if person_names:
                name = person_names[0]
                
                # Check if person exists first
                check_query = f"MATCH (p:Person) WHERE p.name =~ '(?i).*{re.escape(name)}.*' RETURN p.name as name LIMIT 1"
                person_check = self.db.query(check_query)
                
                if person_check:
                    actual_name = person_check[0]['name']
                    
                    # 1-degree connections
                    degree1_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:KNOWS]-(connected:Person)
RETURN DISTINCT connected.name as name, connected.age as age
LIMIT 30"""
                    
                    cypher_queries.append(("1-Degree Connections", degree1_query))
                    degree1 = self.db.query(degree1_query)
                    context['degree_1_connections'] = degree1
                    
                    # 2-degree connections
                    degree2_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:KNOWS*2]-(connected:Person)
WHERE connected.name <> '{actual_name}'
RETURN DISTINCT connected.name as name, connected.age as age
LIMIT 50"""
                    
                    cypher_queries.append(("2-Degree Connections", degree2_query))
                    degree2 = self.db.query(degree2_query)
                    context['degree_2_connections'] = degree2
                    
                    # Get their gang memberships
                    gang_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:KNOWS*1..2]-(connected:Person)
OPTIONAL MATCH (connected)-[:MEMBER_OF]->(o:Organization)
RETURN DISTINCT connected.name as name, o.name as gang
LIMIT 50"""
                    
                    cypher_queries.append(("Network Gang Affiliations", gang_query))
                    context['network_gangs'] = self.db.query(gang_query)
                    
                    print(f"✅ Found {len(degree1)} 1-degree, {len(degree2)} 2-degree connections")
        
        # 2. PATTERN MATCHING - Working Together
        if any(phrase in q for phrase in ['together', 'same crime', 'collaborated', 'co-offender', 'shared crime']):
            
            # Crimes committed together
            collab_query = """MATCH (p1:Person)-[:PARTY_TO]->(c:Crime)<-[:PARTY_TO]-(p2:Person)
WHERE p1.name < p2.name
WITH p1, p2, count(DISTINCT c) as shared_crimes, collect(DISTINCT c.type) as crime_types
WHERE shared_crimes >= 1
OPTIONAL MATCH (p1)-[:MEMBER_OF]->(o1:Organization)
OPTIONAL MATCH (p2)-[:MEMBER_OF]->(o2:Organization)
RETURN p1.name as person1, 
       p2.name as person2,
       shared_crimes,
       crime_types,
       o1.name as gang1,
       o2.name as gang2,
       CASE WHEN o1.name = o2.name OR (o1 IS NULL AND o2 IS NULL) THEN 'same' ELSE 'different' END as gang_status
ORDER BY shared_crimes DESC
LIMIT 20"""
            
            cypher_queries.append(("Crime Collaboration Patterns", collab_query))
            context['collaborations'] = self.db.query(collab_query)
            
            # Filter for different gangs if specified
            if 'different gang' in q or "aren't in the same gang" in q or "not in same gang" in q:
                different_gang_query = """MATCH (p1:Person)-[:PARTY_TO]->(c:Crime)<-[:PARTY_TO]-(p2:Person)
WHERE p1.name < p2.name
MATCH (p1)-[:MEMBER_OF]->(o1:Organization)
MATCH (p2)-[:MEMBER_OF]->(o2:Organization)
WHERE o1.name <> o2.name
WITH p1, p2, o1, o2, count(DISTINCT c) as shared_crimes, collect(DISTINCT c.type) as crime_types
RETURN p1.name as person1,
       p2.name as person2,
       o1.name as gang1,
       o2.name as gang2,
       shared_crimes,
       crime_types
ORDER BY shared_crimes DESC
LIMIT 15"""
                
                cypher_queries.append(("Different Gangs - Same Crimes", different_gang_query))
                context['cross_gang_collaboration'] = self.db.query(different_gang_query)
        
        # 3. GRAPH ALGORITHM QUERIES
        if any(phrase in q for phrase in ['influential', 'most important', 'key criminal', 'pagerank', 'influence']):
            influence_query = """MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
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
LIMIT 15"""
            
            cypher_queries.append(("PageRank - Influence Analysis", influence_query))
            context['influential_criminals'] = self.db.query(influence_query)
        
        # Betweenness - Bridge between gangs
        if any(phrase in q for phrase in ['bridge', 'connection', 'multiple gang', 'different gang', 'cross-gang', 'connects']):
            bridge_query = """MATCH (p:Person)-[:KNOWS]-(other:Person)-[:MEMBER_OF]->(o:Organization)
WITH p, collect(DISTINCT o.name) as connected_gangs
WHERE size(connected_gangs) >= 2
OPTIONAL MATCH (p)-[:MEMBER_OF]->(own_gang:Organization)
OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
RETURN p.name as name,
       p.age as age,
       own_gang.name as own_gang,
       connected_gangs,
       size(connected_gangs) as gang_connections,
       count(c) as crimes
ORDER BY gang_connections DESC, crimes DESC
LIMIT 15"""
            
            cypher_queries.append(("Betweenness - Gang Bridges", bridge_query))
            context['gang_bridges'] = self.db.query(bridge_query)
        
        # Centrality - Most connected
        if any(phrase in q for phrase in ['most connected', 'hub', 'network hub', 'degree central']):
            hub_query = """MATCH (p:Person)-[r]-(connected)
WITH p, count(DISTINCT connected) as total_connections
OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
RETURN p.name as name,
       p.age as age,
       total_connections,
       count(DISTINCT c) as crimes,
       o.name as gang
ORDER BY total_connections DESC
LIMIT 15"""
            
            cypher_queries.append(("Degree Centrality - Network Hubs", hub_query))
            context['network_hubs'] = self.db.query(hub_query)
        
        # 4. PATHFINDING QUERIES
        if any(phrase in q for phrase in ['path between', 'connected to', 'link between', 'connection between']):
            if len(person_names) >= 2:
                name1, name2 = person_names[0], person_names[1]
                
                path_query = f"""MATCH path = shortestPath(
    (p1:Person {{name: '{name1}'}})-[:KNOWS*..6]-(p2:Person {{name: '{name2}'}})
)
RETURN [node in nodes(path) | node.name] as path_nodes,
       length(path) as path_length,
       [rel in relationships(path) | type(rel)] as relationship_types
LIMIT 1"""
                
                cypher_queries.append((f"Shortest Path - {name1} to {name2}", path_query))
                try:
                    path_result = self.db.query(path_query)
                    if path_result:
                        context['connection_path'] = path_result
                except:
                    pass
        
        # 5. COMMUNITY/PATTERN DETECTION
        if any(phrase in q for phrase in ['hidden', 'crime ring', 'working together', 'community', 'cluster']):
            hidden_ring_query = """MATCH (p1:Person)-[:PARTY_TO]->(c:Crime)<-[:PARTY_TO]-(p2:Person)
WHERE p1.name < p2.name
  AND NOT EXISTS((p1)-[:MEMBER_OF]->(:Organization))
  AND NOT EXISTS((p2)-[:MEMBER_OF]->(:Organization))
WITH p1, p2, count(c) as shared_crimes, collect(c.type) as crime_types
WHERE shared_crimes >= 2
RETURN p1.name as person1,
       p2.name as person2,
       p1.age as age1,
       p2.age as age2,
       shared_crimes,
       crime_types
ORDER BY shared_crimes DESC
LIMIT 15"""
            
            cypher_queries.append(("Hidden Crime Rings Detection", hidden_ring_query))
            context['hidden_rings'] = self.db.query(hidden_ring_query)
        
        # 6. TRIANGLES / CLIQUES
        if any(phrase in q for phrase in ['triangle', 'all know each other', 'mutual', 'clique']):
            triangle_query = """MATCH (p1:Person)-[:KNOWS]-(p2:Person)-[:KNOWS]-(p3:Person)-[:KNOWS]-(p1)
WHERE p1.name < p2.name AND p2.name < p3.name
RETURN p1.name as person1, p2.name as person2, p3.name as person3
LIMIT 20"""
            
            cypher_queries.append(("Triangle Patterns", triangle_query))
            context['triangles'] = self.db.query(triangle_query)
        
        # 7. EVIDENCE CHAINS
        if any(phrase in q for phrase in ['evidence chain', 'evidence link', 'evidence connect']):
            evidence_chain_query = """MATCH (c:Crime)-[:HAS_EVIDENCE]->(e:Evidence)-[:LINKS_TO]->(p:Person)
RETURN c.type as crime_type,
       c.id as crime_id,
       e.description as evidence,
       e.significance as significance,
       p.name as suspect
ORDER BY e.significance
LIMIT 20"""
            
            cypher_queries.append(("Evidence Chain Analysis", evidence_chain_query))
            context['evidence_chains'] = self.db.query(evidence_chain_query)
        
        # 8. STANDARD ENTITY QUERIES (Fallback)
        if any(w in q for w in ['organization', 'gang', 'crew']) or not cypher_queries:
            try:
                org_query = """MATCH (o:Organization)
RETURN o.name as name, o.type as type, o.territory as territory, o.members_count as members
ORDER BY o.members_count DESC"""
                
                cypher_queries.append(("All Organizations", org_query))
                context['all_organizations'] = self.db.query(org_query)
                
                members_query = """MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
RETURN o.name as organization, p.name as member, p.age as age
ORDER BY o.name
LIMIT 50"""
                
                cypher_queries.append(("Organization Members", members_query))
                context['organization_members'] = self.db.query(members_query)
            except Exception as e:
                print(f"❌ Org error: {e}")
        
        # PERSON-SPECIFIC (when name mentioned)
        if person_names:
            for name in person_names[:2]:
                try:
                    escaped = re.escape(name)
                    
                    # Check if person exists
                    check_query = f"MATCH (p:Person) WHERE p.name =~ '(?i).*{escaped}.*' RETURN p.name as name LIMIT 1"
                    person_exists = self.db.query(check_query)
                    
                    if person_exists:
                        actual_name = person_exists[0]['name']
                        
                        # Basic info
                        info_query = f"MATCH (p:Person {{name: '{actual_name}'}}) RETURN p.name as name, p.age as age, p.occupation as occupation"
                        cypher_queries.append((f"{actual_name} - Info", info_query))
                        context[f'{name}_info'] = self.db.query(info_query)
                        
                        # Crimes
                        crimes_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:PARTY_TO]->(c:Crime)
RETURN c.type as crime_type, c.date as date, c.severity as severity
ORDER BY c.date DESC
LIMIT 20"""
                        
                        cypher_queries.append((f"{actual_name} - Crimes", crimes_query))
                        context[f'{name}_crimes'] = self.db.query(crimes_query)
                        
                        # Connections (always include for graph analysis)
                        conn_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:KNOWS]-(other:Person)
OPTIONAL MATCH (other)-[:MEMBER_OF]->(o:Organization)
RETURN DISTINCT other.name as name, other.age as age, o.name as gang
LIMIT 30"""
                        
                        cypher_queries.append((f"{actual_name} - Connections", conn_query))
                        context[f'{name}_connections'] = self.db.query(conn_query)
                        
                        # Gang membership
                        gang_query = f"""MATCH (p:Person {{name: '{actual_name}'}})-[:MEMBER_OF]->(o:Organization)
RETURN o.name as organization"""
                        
                        result = self.db.query(gang_query)
                        if result:
                            context[f'{name}_gang'] = result
                except Exception as e:
                    print(f"❌ Error for {name}: {e}")
        
        # COMMON QUERIES
        if any(w in q for w in ['hotspot', 'most crime']):
            query = """MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
RETURN l.name as location, count(c) as crimes
ORDER BY crimes DESC
LIMIT 10"""
            cypher_queries.append(("Crime Hotspots", query))
            context['hotspots'] = self.db.query(query)
        
        if any(w in q for w in ['repeat', 'offender']):
            query = """MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
WITH p, count(c) as crimes
WHERE crimes >= 2
OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
RETURN p.name as name, p.age as age, crimes, o.name as gang
ORDER BY crimes DESC
LIMIT 15"""
            cypher_queries.append(("Repeat Offenders", query))
            context['repeat_offenders'] = self.db.query(query)
        
        # WEAPON QUERIES
        if any(w in q for w in ['weapon', 'gun', 'firearm', 'armed', 'weapons']):
            try:
                print("🔫 Fetching weapons...")
                
                # All weapons
                weapons_query = """MATCH (w:Weapon)
RETURN w.id as id, 
       w.type as type, 
       w.make as make, 
       w.model as model,
       w.recovered as recovered
ORDER BY w.type"""
                
                cypher_queries.append(("All Weapons", weapons_query))
                context['all_weapons'] = self.db.query(weapons_query)
                
                # Weapon ownership
                ownership_query = """MATCH (p:Person)-[:OWNS]->(w:Weapon)
OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
RETURN p.name as owner,
       p.age as age,
       o.name as gang,
       w.type as weapon_type,
       w.make as make,
       w.model as model
ORDER BY o.name, p.name"""
                
                cypher_queries.append(("Weapon Ownership", ownership_query))
                context['weapon_ownership'] = self.db.query(ownership_query)
                
                # Weapons used in crimes
                usage_query = """MATCH (c:Crime)-[:USED_WEAPON]->(w:Weapon)
RETURN c.type as crime_type,
       c.id as crime_id,
       c.severity as severity,
       w.type as weapon_type,
       w.make as make,
       w.model as model
ORDER BY c.severity, c.date DESC"""
                
                cypher_queries.append(("Weapons Used in Crimes", usage_query))
                context['weapon_usage'] = self.db.query(usage_query)
                
                print(f"✅ Found {len(context['all_weapons'])} weapons")
            except Exception as e:
                print(f"❌ Weapon error: {e}")
        
        # VEHICLE QUERIES
        if any(w in q for w in ['vehicle', 'car', 'truck', 'van', 'getaway']):
            try:
                print("🚗 Fetching vehicles...")
                
                # All vehicles
                vehicles_query = """MATCH (v:Vehicle)
RETURN v.id as id,
       v.make as make,
       v.model as model,
       v.year as year,
       v.color as color,
       v.license_plate as plate,
       v.reported_stolen as stolen
ORDER BY v.reported_stolen DESC, v.make"""
                
                cypher_queries.append(("All Vehicles", vehicles_query))
                context['all_vehicles'] = self.db.query(vehicles_query)
                
                # Vehicle ownership
                ownership_query = """MATCH (p:Person)-[:OWNS]->(v:Vehicle)
RETURN p.name as owner,
       v.make as make,
       v.model as model,
       v.license_plate as plate
ORDER BY p.name"""
                
                cypher_queries.append(("Vehicle Ownership", ownership_query))
                context['vehicle_ownership'] = self.db.query(ownership_query)
                
                # Vehicles in crimes
                usage_query = """MATCH (c:Crime)-[:INVOLVED_VEHICLE]->(v:Vehicle)
RETURN c.type as crime_type,
       c.id as crime_id,
       v.make as make,
       v.model as model,
       v.license_plate as plate
ORDER BY c.date DESC"""
                
                cypher_queries.append(("Vehicles in Crimes", usage_query))
                context['vehicle_usage'] = self.db.query(usage_query)
                
                print(f"✅ Found {len(context['all_vehicles'])} vehicles")
            except Exception as e:
                print(f"❌ Vehicle error: {e}")
        
        # EVIDENCE QUERIES
        if any(w in q for w in ['evidence', 'proof', 'forensic', 'clue']):
            try:
                print("🔬 Fetching evidence...")
                
                # All evidence
                evidence_query = """MATCH (e:Evidence)
RETURN e.id as id,
       e.type as type,
       e.description as description,
       e.significance as significance,
       e.verified as verified
ORDER BY 
    CASE e.significance
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    e.id"""
                
                cypher_queries.append(("All Evidence", evidence_query))
                context['all_evidence'] = self.db.query(evidence_query)
                
                # Evidence linking suspects
                links_query = """MATCH (e:Evidence)-[:LINKS_TO]->(p:Person)
RETURN e.id as evidence_id,
       e.description as evidence,
       e.significance as significance,
       p.name as suspect
ORDER BY e.significance, p.name"""
                
                cypher_queries.append(("Evidence-Suspect Links", links_query))
                context['evidence_links'] = self.db.query(links_query)
                
                # Evidence by crime
                crime_evidence_query = """MATCH (c:Crime)-[:HAS_EVIDENCE]->(e:Evidence)
RETURN c.id as crime_id,
       c.type as crime_type,
       e.description as evidence,
       e.significance as significance
ORDER BY c.date DESC"""
                
                cypher_queries.append(("Crime Evidence", crime_evidence_query))
                context['crime_evidence'] = self.db.query(crime_evidence_query)
                
                print(f"✅ Found {len(context['all_evidence'])} evidence items")
            except Exception as e:
                print(f"❌ Evidence error: {e}")
        
        # INVESTIGATOR QUERIES
        if any(w in q for w in ['investigator', 'detective', 'officer', 'assigned']):
            try:
                print("👮 Fetching investigators...")
                
                investigators_query = """MATCH (i:Investigator)
RETURN i.id as id,
       i.name as name,
       i.badge_number as badge,
       i.department as department,
       i.specialization as specialization,
       i.cases_solved as solved,
       i.active_cases as active
ORDER BY i.cases_solved DESC"""
                
                cypher_queries.append(("All Investigators", investigators_query))
                context['all_investigators'] = self.db.query(investigators_query)
                
                # Case assignments
                assignments_query = """MATCH (c:Crime)-[:INVESTIGATED_BY]->(i:Investigator)
RETURN i.name as investigator,
       c.id as crime_id,
       c.type as crime_type,
       c.status as status
ORDER BY i.name, c.date DESC"""
                
                cypher_queries.append(("Case Assignments", assignments_query))
                context['case_assignments'] = self.db.query(assignments_query)
                
                print(f"✅ Found {len(context['all_investigators'])} investigators")
            except Exception as e:
                print(f"❌ Investigator error: {e}")
        
        return context, cypher_queries
    
    def _extract_person_names(self, question):
        """Extract person names from question"""
        exclude = ['i', 'chicago', 'detective', 'side', 'gang', 'crew', 'street', 'show', 'his', 'her', 'their']
        
        words = question.split()
        names = []
        
        i = 0
        while i < len(words):
            word = words[i].strip('.,!?*')
            
            if len(word) > 0 and word[0].isupper() and word.lower() not in exclude:
                # Check for full name
                if i + 1 < len(words):
                    next_word = words[i+1].strip('.,!?*')
                    if len(next_word) > 0 and next_word[0].isupper() and next_word.lower() not in exclude:
                        names.append(f"{word} {next_word}")
                        i += 2
                        continue
            i += 1
        
        return names
    
    def _generate_with_llm(self, question, context, conversation_history):
        """Generate with LLM"""
        
        system_prompt = """You are a crime investigation AI assistant. Answer using ONLY the provided database results.

CRITICAL FORMATTING RULES:
1. Write in NATURAL PARAGRAPHS - NO bullet points, NO lists, NO numbered items
2. Use **bold** for important names, numbers, and key facts
3. Write 2-4 flowing paragraphs that read naturally
4. Connect ideas smoothly between sentences
5. End with ONE follow-up question

WHAT TO BOLD:
- **Suspect names** (exact from data)
- **Organization names** (gangs, crews)
- **Exact numbers** (crime counts, connections, scores)
- **Crime types** when mentioned
- **Key findings** (influence scores, rankings)

ANTI-HALLUCINATION:
- Use ONLY data from the context
- Count items accurately - no rounding
- Real names only - never invent

Example CORRECT format:
"Based on the network analysis, **David Rodriguez** is connected to **8 people** in his immediate network. His first-degree connections include **Sarah Chen**, **Lisa Rivera**, and **Maria Brown**, all of whom are gang members. Moving to second-degree connections, the network expands to include **34 additional individuals**, bringing the total network size to **42 people**. This demonstrates how quickly criminal networks can spread through just two relationship hops.

Would you like to see the specific crimes these network members have committed?"

Example WRONG format (DO NOT DO THIS):
"Here are the connections:
- Direct connections: 8 people
- Second degree: 34 people
- Total network: 42 people"

REMEMBER: Flowing paragraphs, not lists!"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Recent history
        for msg in conversation_history[-8:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Format context
        context_str = "\n=== DATABASE RESULTS ===\n\n"
        for key, value in context.items():
            if value:
                context_str += f"{key.upper()}:\n"
                if isinstance(value, list) and len(value) > 0:
                    context_str += f"Count: {len(value)}\n"
                    for item in value[:10]:
                        context_str += f"  • {json.dumps(item, default=str)}\n"
                elif isinstance(value, dict):
                    context_str += f"{json.dumps(value, indent=2, default=str)}\n"
                context_str += "\n"
        
        messages.append({"role": "user", "content": f"{question}\n\n{context_str}"})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=600
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback(self, question, context):
        """Smart fallback generator"""
        
        parts = []
        
        # Database stats
        if 'database_stats' in context:
            stats = context['database_stats']
            parts.append(f"The database contains **{stats.get('total_crimes', 0)} crimes** and **{stats.get('total_persons', 0)} suspects**.")
        
        # Degree connections
        if 'degree_1_connections' in context:
            deg1 = context['degree_1_connections']
            deg2 = context.get('degree_2_connections', [])
            
            if deg1 and deg2:
                names_sample = ', '.join([f"**{d['name']}**" for d in deg1[:5]])
                more_text = f" and **{len(deg1)-5}** others" if len(deg1) > 5 else ""
                
                parts.append(
                    f"Starting with first-degree connections, I found **{len(deg1)} direct associates** including {names_sample}{more_text}. "
                    f"Expanding to second-degree connections brings **{len(deg2)} additional people** into the network, "
                    f"for a total network size of **{len(deg1) + len(deg2)} individuals**. This demonstrates how quickly "
                    f"criminal networks expand through just two relationship hops."
                )
            elif deg1:
                names_list = ', '.join([f"**{d['name']}**" for d in deg1[:8]])
                parts.append(
                    f"The direct network includes **{len(deg1)} people**: {names_list}. "
                    f"These are all first-degree connections through KNOWS relationships in the graph."
                )
        
        # Collaborations
        if 'collaborations' in context:
            collabs = context['collaborations']
            if collabs:
                same_gang = [c for c in collabs if c.get('gang_status') == 'same']
                diff_gang = [c for c in collabs if c.get('gang_status') == 'different']
                
                if diff_gang:
                    example = diff_gang[0]
                    parts.append(
                        f"Pattern matching analysis identified **{len(collabs)} pairs of suspects** who committed crimes together. "
                        f"Notably, **{len(diff_gang)} pairs** are from different gangs. For instance, **{example['person1']}** "
                        f"from **{example.get('gang1', 'Independent')}** and **{example['person2']}** from **{example.get('gang2', 'Independent')}** "
                        f"collaborated on **{example['shared_crimes']} crimes**, suggesting cross-organizational criminal activity."
                    )
                else:
                    parts.append(
                        f"Analysis shows **{len(collabs)} pairs** who committed crimes together, primarily within their own organizations."
                    )
        
        # Cross-gang collaboration
        if 'cross_gang_collaboration' in context:
            cross = context['cross_gang_collaboration']
            if cross:
                top = cross[0]
                crime_list = ', '.join(top.get('crime_types', [])[:3])
                
                parts.append(
                    f"Cross-gang collaboration analysis reveals **{len(cross)} suspect pairs** from different organizations working together. "
                    f"The most active pairing is **{top['person1']}** from **{top['gang1']}** and **{top['person2']}** from **{top['gang2']}**, "
                    f"who collaborated on **{top['shared_crimes']} crimes** including {crime_list}. This suggests strategic gang alliances "
                    f"or independent actors bridging multiple organizations."
                )
        
        # Influential
        if 'influential_criminals' in context:
            influential = context['influential_criminals']
            if influential:
                top = influential[0]
                
                para = f"Network influence analysis identifies **{top['name']}** (Age {top['age']}) as the most influential criminal with an influence score of **{top['influence_score']:.1f}**. "
                para += f"This ranking is based on **{top['crimes']} crimes** committed and **{top['connections']} network connections**"
                if top.get('gang'):
                    para += f", operating within **{top['gang']}**"
                para += ". "
                
                if len(influential) >= 2:
                    top2 = influential[1]
                    para += f"The second-ranked individual is **{top2['name']}** with a score of **{top2['influence_score']:.1f}**. "
                
                para += "These influence scores combine criminal activity and network position using a weighted formula to identify key targets for investigation."
                parts.append(para)
        
        # Gang bridges
        if 'gang_bridges' in context:
            bridges = context['gang_bridges']
            if bridges:
                top_bridge = bridges[0]
                gangs_list = ', '.join([f"**{g}**" for g in top_bridge['connected_gangs'][:3]])
                
                parts.append(
                    f"Betweenness centrality analysis reveals **{len(bridges)} individuals** who act as bridges between different gangs. "
                    f"The most significant bridge is **{top_bridge['name']}**, who connects **{top_bridge['gang_connections']} different organizations** "
                    f"including {gangs_list}. Such individuals are often informants, brokers, or strategic targets for disrupting criminal networks."
                )
        
        # Organizations
        if 'all_organizations' in context and not parts:
            orgs = context['all_organizations']
            if orgs:
                org_names = ', '.join([f"**{o['name']}**" for o in orgs[:5]])
                more = f" and **{len(orgs)-5}** others" if len(orgs) > 5 else ""
                
                parts.append(
                    f"The knowledge graph tracks **{len(orgs)} criminal organizations** operating across Chicago, including {org_names}{more}. "
                    f"The largest organization is **{orgs[0]['name']}** with **{orgs[0].get('members', 0)} members** "
                    f"controlling the **{orgs[0].get('territory', 'unknown')}** territory."
                )
        
        # WEAPONS
        if 'all_weapons' in context:
            weapons = context['all_weapons']
            if weapons:
                weapon_types = {}
                for w in weapons:
                    wtype = w.get('type', 'Unknown')
                    weapon_types[wtype] = weapon_types.get(wtype, 0) + 1
                
                top_types = sorted(weapon_types.items(), key=lambda x: x[1], reverse=True)[:3]
                type_summary = ', '.join([f"**{t[0]}** ({t[1]})" for t in top_types])
                
                parts.append(
                    f"The database contains **{len(weapons)} weapons** in the system. The most common types are {type_summary}. "
                )
                
                # Add ownership info if available
                if 'weapon_ownership' in context and context['weapon_ownership']:
                    ownership = context['weapon_ownership']
                    parts.append(
                        f"**{len(ownership)} weapons** are linked to known owners, with some suspects possessing multiple firearms. "
                    )
                
                # Add usage info if available
                if 'weapon_usage' in context and context['weapon_usage']:
                    usage = context['weapon_usage']
                    parts.append(
                        f"**{len(usage)} weapons** have been used in documented crimes, with severity levels ranging from low to critical. "
                    )
        
        # VEHICLES
        if 'all_vehicles' in context:
            vehicles = context['all_vehicles']
            if vehicles:
                stolen = [v for v in vehicles if v.get('stolen')]
                
                parts.append(
                    f"The system tracks **{len(vehicles)} vehicles** involved in criminal activity. "
                    f"Of these, **{len(stolen)} are reported stolen**. "
                )
                
                if vehicles[0].get('make'):
                    top_vehicle = vehicles[0]
                    parts.append(
                        f"The most notable is a **{top_vehicle.get('make')} {top_vehicle.get('model')}** "
                        f"with plate **{top_vehicle.get('license_plate')}**. "
                    )
        
        # EVIDENCE
        if 'all_evidence' in context:
            evidence = context['all_evidence']
            if evidence:
                critical = [e for e in evidence if e.get('significance') == 'critical']
                verified = [e for e in evidence if e.get('verified')]
                
                parts.append(
                    f"The evidence database contains **{len(evidence)} items**, of which **{len(critical)} are classified as critical significance** "
                    f"and **{len(verified)} have been forensically verified**. "
                )
                
                if 'evidence_links' in context and context['evidence_links']:
                    links = context['evidence_links']
                    parts.append(
                        f"**{len(links)} evidence items** are directly linked to suspects through forensic analysis. "
                    )
        
        # INVESTIGATORS
        if 'all_investigators' in context:
            investigators = context['all_investigators']
            if investigators:
                total_solved = sum(i.get('cases_solved', 0) for i in investigators)
                total_active = sum(i.get('active_cases', 0) for i in investigators)
                
                parts.append(
                    f"The investigation team includes **{len(investigators)} detectives** who have collectively solved **{total_solved} cases** "
                    f"with **{total_active} currently active investigations**. "
                )
                
                if investigators[0].get('cases_solved'):
                    top_inv = investigators[0]
                    parts.append(
                        f"The lead investigator is **{top_inv['name']}** with **{top_inv['cases_solved']} solved cases**. "
                    )
        
        # Combine
        if parts:
            return " ".join(parts) + "\n\nWould you like more details?"
        else:
            return self._generate_emergency_fallback(context)
    
    def _generate_emergency_fallback(self, context):
        """Always returns something in paragraph format"""
        stats = context.get('database_stats', {})
        
        if stats and stats.get('total_crimes'):
            return (
                f"I've retrieved data from the knowledge graph database. The system currently contains "
                f"**{stats.get('total_crimes', 0)} crime incidents** involving **{stats.get('total_persons', 0)} suspects**. "
                f"The graph structure enables complex queries about relationships, patterns, and network analysis. "
                f"Try asking about influential criminals, gang connections, or multi-hop relationship networks."
            )
        else:
            return (
                "I've connected to the graph database and retrieved information. Please try specific questions like: "
                "'Show me everyone within 2 degrees of David Rodriguez', 'Which suspects connect to multiple gangs?', "
                "or 'Who is the most influential criminal?' These questions showcase the knowledge graph's capabilities."
            )

# Test
if __name__ == "__main__":
    rag = GraphRAG()
    
    questions = [
        "Show me everyone within 2 degrees of David Rodriguez",
        "Which suspects share connections with multiple gangs?",
        "Find suspects who committed crimes together but aren't in the same gang"
    ]
    
    for q in questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = rag.ask(q)
        print(f"A: {result['answer']}")
        print(f"\nCypher Queries: {len(result['cypher_queries'])}")