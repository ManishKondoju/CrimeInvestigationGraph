import config
from database import Database
import json
import re

class GraphRAG:
    def __init__(self):
        self.db = Database()
        self.model = config.MODEL_NAME
        
        # Try to initialize OpenAI (works with OpenRouter)
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
        """Original ask method for backward compatibility"""
        return self.ask_with_context(question, [])
    
    def ask_with_context(self, question, conversation_history):
        """
        ENHANCED: Ask with conversation context for follow-up questions
        
        Args:
            question: Current user question
            conversation_history: List of previous {role, content} messages
        """
        print(f"\n🔍 Processing question: {question}")
        
        # Step 1: RETRIEVE - Get ALL relevant data
        context, cypher_queries = self._smart_retrieve(question, conversation_history)
        
        print(f"✅ Retrieved {len(context)} context keys")
        for key in context.keys():
            if context[key]:
                data_len = len(context[key]) if isinstance(context[key], list) else 'stats'
                print(f"  ✓ {key}: {data_len}")
        
        # Step 2: GENERATE answer with conversation awareness
        if self.use_llm:
            try:
                answer = self._generate_with_llm_conversational(
                    question, 
                    context, 
                    conversation_history
                )
                print("✅ LLM generated response")
            except Exception as e:
                print(f"⚠️ LLM failed: {e}")
                answer = self._generate_fallback(question, context)
        else:
            answer = self._generate_fallback(question, context)
        
        return {
            'answer': answer,
            'sources': list(context.keys()),
            'cypher_queries': cypher_queries,  # NEW: Return Cypher queries
            'context': context  # NEW: Return full context for inspection
        }
    
    def _smart_retrieve(self, question, conversation_history):
        """ENHANCED retrieval with conversation awareness"""
        context = {}
        cypher_queries = []  # Track all executed queries
        q = question.lower()
        
        print(f"📋 Analyzing question: '{question}'")
        
        # Check conversation history for entity references
        entities_from_history = self._extract_entities_from_history(conversation_history)
        
        # Extract entities from question
        locations = self._extract_locations(question)
        crime_types = self._extract_crime_types(question)
        person_names = self._extract_person_names(question)
        organizations = self._extract_organizations(question)
        
        print(f"🔎 Found entities - Locations: {locations}, Persons: {person_names}, Orgs: {organizations}")
        
        # Merge with historical entities for follow-up questions
        if entities_from_history:
            locations.extend(entities_from_history.get('locations', []))
            person_names.extend(entities_from_history.get('persons', []))
            organizations.extend(entities_from_history.get('organizations', []))
        
        # Remove duplicates
        locations = list(set(locations))
        person_names = list(set(person_names))
        organizations = list(set(organizations))
        
        # ALWAYS get basic stats
        try:
            query = "MATCH (c:Crime) RETURN count(c) as n"
            cypher_queries.append(("Database Stats - Crimes", query))
            
            context['database_stats'] = {
                'total_crimes': self.db.query(query)[0]['n'],
                'total_persons': self.db.query("MATCH (p:Person) RETURN count(p) as n")[0]['n'],
                'total_locations': self.db.query("MATCH (l:Location) RETURN count(l) as n")[0]['n'],
                'total_organizations': self.db.query("MATCH (o:Organization) RETURN count(o) as n")[0]['n'],
                'total_evidence': self.db.query("MATCH (e:Evidence) RETURN count(e) as n")[0]['n']
            }
            
            cypher_queries.append(("Database Stats - All Counts", """
MATCH (c:Crime) WITH count(c) as crimes
MATCH (p:Person) WITH crimes, count(p) as persons
MATCH (l:Location) WITH crimes, persons, count(l) as locations
MATCH (o:Organization) WITH crimes, persons, locations, count(o) as orgs
MATCH (e:Evidence)
RETURN crimes, persons, locations, orgs, count(e) as evidence
            """.strip()))
            
            print(f"📊 Stats: {context['database_stats']}")
        except Exception as e:
            print(f"❌ Error fetching stats: {e}")
            context['database_stats'] = {'error': 'Could not fetch stats'}
        
        # ========== ORGANIZATION QUERIES ==========
        if any(w in q for w in ['organization', 'organisations', 'gang', 'crew', 'syndicate', 'cartel', 'ring', 'operate', 'operating']) or organizations:
            print("🏢 Fetching organizations...")
            try:
                org_query = """
MATCH (o:Organization)
RETURN o.name as name, o.type as type, 
       o.territory as territory, o.members_count as members,
       o.activity_level as activity
ORDER BY o.members_count DESC
                """.strip()
                
                cypher_queries.append(("Organizations", org_query))
                orgs = self.db.query(org_query)
                context['all_organizations'] = orgs
                print(f"✅ Found {len(orgs)} organizations")
                
                members_query = """
MATCH (p:Person)-[r:MEMBER_OF]->(o:Organization)
RETURN o.name as organization, p.name as member,
       p.age as age, r.rank as rank
ORDER BY o.name, r.rank
LIMIT 50
                """.strip()
                
                cypher_queries.append(("Organization Members", members_query))
                members = self.db.query(members_query)
                context['organization_members'] = members
                print(f"✅ Found {len(members)} organization members")
                
            except Exception as e:
                print(f"❌ Error fetching organizations: {e}")
        
        # Specific organization query
        if organizations:
            for org in organizations[:3]:
                try:
                    # Escape special characters for regex
                    escaped_org = re.escape(org)
                    
                    print(f"🔍 Fetching crimes for organization: {org}")
                    org_crimes = self.db.query(f"""
                        MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
                        WHERE o.name =~ '(?i).*{escaped_org}.*'
                        MATCH (p)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                        RETURN c.type as crime_type, c.date as date,
                               l.name as location, p.name as member
                        ORDER BY c.date DESC
                        LIMIT 30
                    """)
                    
                    if org_crimes:
                        context[f'org_{org}_crimes'] = org_crimes
                        print(f"✅ Found {len(org_crimes)} crimes for {org}")
                except Exception as e:
                    print(f"❌ Error fetching {org} crimes: {e}")
        
        # ========== EVIDENCE QUERIES ==========
        if any(w in q for w in ['evidence', 'proof', 'forensic', 'dna', 'fingerprint']):
            try:
                print("🔬 Fetching evidence...")
                context['all_evidence'] = self.db.query("""
                    MATCH (e:Evidence)
                    RETURN e.id as id, e.type as type, e.description as description,
                           e.significance as significance, e.verified as verified
                    ORDER BY 
                        CASE e.significance 
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            ELSE 4
                        END
                    LIMIT 30
                """)
                
                context['evidence_person_links'] = self.db.query("""
                    MATCH (e:Evidence)-[r:LINKS_TO]->(p:Person)
                    RETURN e.id as evidence_id, e.description as evidence,
                           p.name as suspect, r.confidence as confidence
                    ORDER BY r.confidence DESC
                    LIMIT 30
                """)
                print("✅ Evidence fetched")
            except Exception as e:
                print(f"❌ Error fetching evidence: {e}")
        
        # ========== INVESTIGATOR QUERIES ==========
        if any(w in q for w in ['investigator', 'detective', 'officer', 'assigned']):
            try:
                print("👮 Fetching investigators...")
                context['all_investigators'] = self.db.query("""
                    MATCH (i:Investigator)
                    RETURN i.name as name, i.badge_number as badge,
                           i.department as department, i.specialization as specialization,
                           i.cases_solved as solved, i.active_cases as active
                    ORDER BY i.cases_solved DESC
                """)
                print("✅ Investigators fetched")
            except Exception as e:
                print(f"❌ Error fetching investigators: {e}")
        
        # ========== MO PATTERNS ==========
        if any(w in q for w in ['modus operandi', 'mo', 'pattern', 'method', 'signature', 'similar']):
            try:
                print("🎯 Fetching MO patterns...")
                context['all_mo_patterns'] = self.db.query("""
                    MATCH (m:ModusOperandi)
                    RETURN m.id as id, m.description as description,
                           m.signature_element as signature, m.frequency as frequency
                    ORDER BY m.frequency DESC
                """)
                
                context['crimes_by_mo'] = self.db.query("""
                    MATCH (c:Crime)-[r:MATCHES_MO]->(m:ModusOperandi)
                    RETURN m.description as mo, c.id as crime_id, 
                           c.type as crime_type, r.similarity as similarity
                    ORDER BY r.similarity DESC
                    LIMIT 40
                """)
                print("✅ MO patterns fetched")
            except Exception as e:
                print(f"❌ Error fetching MO patterns: {e}")
        
        # ========== VEHICLES ==========
        if any(w in q for w in ['vehicle', 'car', 'truck', 'getaway', 'stolen']):
            try:
                print("🚗 Fetching vehicles...")
                context['all_vehicles'] = self.db.query("""
                    MATCH (v:Vehicle)
                    RETURN v.id as id, v.make as make, v.model as model,
                           v.year as year, v.color as color, 
                           v.license_plate as plate, v.reported_stolen as stolen
                    ORDER BY v.reported_stolen DESC
                    LIMIT 30
                """)
                print("✅ Vehicles fetched")
            except Exception as e:
                print(f"❌ Error fetching vehicles: {e}")
        
        # ========== WEAPONS ==========
        if any(w in q for w in ['weapon', 'gun', 'firearm', 'knife', 'armed']):
            try:
                print("🔫 Fetching weapons...")
                context['all_weapons'] = self.db.query("""
                    MATCH (w:Weapon)
                    RETURN w.id as id, w.type as type, w.make as make,
                           w.model as model, w.recovered as recovered
                    LIMIT 30
                """)
                
                # Also fetch armed gang members
                context['armed_gang_members'] = self.db.query("""
                    MATCH (p:Person)-[:MEMBER_OF]->(o:Organization)
                    MATCH (p)-[:OWNS]->(w:Weapon)
                    RETURN p.name as member, o.name as gang, 
                           w.type as weapon_type, w.id as weapon_id
                    ORDER BY o.name
                    LIMIT 30
                """)
                print("✅ Weapons fetched")
            except Exception as e:
                print(f"❌ Error fetching weapons: {e}")
        
        # ========== LOCATION-SPECIFIC ==========
        if locations:
            for location in locations[:3]:
                try:
                    print(f"📍 Fetching data for location: {location}")
                    context[f'crimes_in_{location}'] = self.db.query(f"""
                        MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
                        WHERE l.name =~ '(?i).*{location}.*'
                        RETURN c.id as crime_id, c.type as crime_type, 
                               c.date as date, c.severity as severity
                        ORDER BY c.date DESC
                        LIMIT 30
                    """)
                    
                    context[f'suspects_in_{location}'] = self.db.query(f"""
                        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                        WHERE l.name =~ '(?i).*{location}.*'
                        WITH p, count(DISTINCT c) as crime_count
                        RETURN p.name as name, p.age as age, p.risk_score as risk_score,
                               crime_count
                        ORDER BY crime_count DESC
                        LIMIT 20
                    """)
                    print(f"✅ Location data fetched for {location}")
                except Exception as e:
                    print(f"❌ Error fetching {location} data: {e}")
        
        # ========== PERSON-SPECIFIC ==========
        if person_names:
            for name in person_names[:3]:
                try:
                    # Escape special regex characters
                    escaped_name = re.escape(name)
                    
                    print(f"👤 Fetching data for person: {name}")
                    
                    # Get person's basic info
                    person_info = self.db.query(f"""
                        MATCH (p:Person)
                        WHERE p.name =~ '(?i).*{escaped_name}.*'
                        RETURN p.name as name, p.age as age, p.risk_score as risk_score,
                               p.occupation as occupation, p.criminal_record as has_record
                    """)
                    
                    if person_info:
                        context[f'{name}_info'] = person_info
                    
                    # Get person's organizations
                    person_orgs = self.db.query(f"""
                        MATCH (p:Person)-[r:MEMBER_OF]->(o:Organization)
                        WHERE p.name =~ '(?i).*{escaped_name}.*'
                        RETURN o.name as organization, r.rank as rank, r.since as since
                    """)
                    
                    if person_orgs:
                        context[f'{name}_organizations'] = person_orgs
                    
                    # Get person's crimes
                    person_crimes = self.db.query(f"""
                        MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
                        WHERE p.name =~ '(?i).*{escaped_name}.*'
                        RETURN c.type as crime_type, c.date as date, c.id as crime_id
                        ORDER BY c.date DESC
                        LIMIT 20
                    """)
                    
                    if person_crimes:
                        context[f'{name}_crimes'] = person_crimes
                    
                    # Get connections
                    context[f'{name}_connections'] = self.db.query(f"""
                        MATCH (p:Person)-[:KNOWS*1..2]-(connected:Person)
                        WHERE p.name =~ '(?i).*{escaped_name}.*'
                        RETURN DISTINCT connected.name as name, 
                               connected.age as age,
                               connected.criminal_record as has_record
                        LIMIT 30
                    """)
                    print(f"✅ Person data fetched for {name}")
                except Exception as e:
                    print(f"❌ Error fetching {name} data: {e}")
        
        # ========== PATTERNS ==========
        if any(w in q for w in ['hotspot', 'dangerous', 'where', 'most crime']):
            try:
                print("🔥 Fetching crime hotspots...")
                hotspot_query = """
MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
RETURN l.name as location, l.district as district,
       count(c) as crimes
ORDER BY crimes DESC
LIMIT 15
                """.strip()
                
                cypher_queries.append(("Crime Hotspots", hotspot_query))
                context['hotspots'] = self.db.query(hotspot_query)
                print("✅ Hotspots fetched")
            except Exception as e:
                print(f"❌ Error fetching hotspots: {e}")
        
        if any(w in q for w in ['repeat', 'offender', 'criminal', 'suspect']):
            try:
                print("🔁 Fetching repeat offenders...")
                repeat_query = """
MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
WITH p, count(c) as crimes
WHERE crimes >= 2
OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
RETURN p.name as name, p.age as age, crimes,
       o.name as organization
ORDER BY crimes DESC
LIMIT 20
                """.strip()
                
                cypher_queries.append(("Repeat Offenders", repeat_query))
                context['repeat_offenders'] = self.db.query(repeat_query)
                print("✅ Repeat offenders fetched")
            except Exception as e:
                print(f"❌ Error fetching repeat offenders: {e}")
        
        if any(w in q for w in ['network', 'connected', 'know', 'associate']):
            try:
                print("🕸️ Fetching criminal networks...")
                network_query = """
MATCH (p1:Person)-[:KNOWS]-(p2:Person)
WHERE EXISTS((p1)-[:PARTY_TO]->(:Crime))
  AND EXISTS((p2)-[:PARTY_TO]->(:Crime))
RETURN p1.name as person1, p2.name as person2
LIMIT 30
                """.strip()
                
                cypher_queries.append(("Criminal Networks", network_query))
                context['criminal_networks'] = self.db.query(network_query)
                print("✅ Networks fetched")
            except Exception as e:
                print(f"❌ Error fetching networks: {e}")
        
        # ========== GRAPH ALGORITHMS ==========
        # PageRank / Influence / Key criminals
        if any(w in q for w in ['influential', 'important', 'key', 'pagerank', 'influence', 'priority', 'target']):
            try:
                print("📊 Calculating influence scores (PageRank)...")
                pagerank_query = """
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
                """.strip()
                
                cypher_queries.append(("PageRank - Influential Criminals", pagerank_query))
                context['influential_criminals'] = self.db.query(pagerank_query)
                print(f"✅ Found {len(context['influential_criminals'])} influential criminals")
            except Exception as e:
                print(f"❌ Error calculating influence: {e}")
        
        # Community Detection / Hidden rings
        if any(w in q for w in ['community', 'hidden', 'ring', 'group', 'cluster', 'working together']):
            try:
                print("🎯 Detecting hidden crime rings...")
                hidden_rings_query = """
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
                """.strip()
                
                cypher_queries.append(("Community Detection - Hidden Rings", hidden_rings_query))
                context['hidden_crime_rings'] = self.db.query(hidden_rings_query)
                print(f"✅ Found {len(context['hidden_crime_rings'])} hidden rings")
            except Exception as e:
                print(f"❌ Error detecting communities: {e}")
        
        # Centrality / Most connected / Hubs
        if any(w in q for w in ['centrality', 'hub', 'connector', 'bridge', 'most connected']):
            try:
                print("🔗 Calculating centrality measures...")
                centrality_query = """
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
                """.strip()
                
                cypher_queries.append(("Degree Centrality - Network Hubs", centrality_query))
                context['network_hubs'] = self.db.query(centrality_query)
                print(f"✅ Found {len(context['network_hubs'])} network hubs")
                
                # Betweenness - bridges between gangs
                betweenness_query = """
MATCH (p:Person)-[:KNOWS]-(other:Person)-[:MEMBER_OF]->(o:Organization)
WITH p, collect(DISTINCT o.name) as connected_gangs
WHERE size(connected_gangs) > 1
OPTIONAL MATCH (p)-[:MEMBER_OF]->(own_gang:Organization)
RETURN p.name as name,
       own_gang.name as own_gang,
       connected_gangs,
       size(connected_gangs) as gang_connections
ORDER BY gang_connections DESC
LIMIT 15
                """.strip()
                
                cypher_queries.append(("Betweenness Centrality - Gang Bridges", betweenness_query))
                context['gang_bridges'] = self.db.query(betweenness_query)
                print(f"✅ Found {len(context['gang_bridges'])} gang bridges")
            except Exception as e:
                print(f"❌ Error calculating centrality: {e}")
        
        # Shortest path between two people
        if any(w in q for w in ['path', 'connection between', 'how is', 'connected to', 'related to']):
            # Try to extract two person names for path query
            if len(person_names) >= 2:
                try:
                    print(f"🛤️ Finding path between {person_names[0]} and {person_names[1]}...")
                    path_query = f"""
MATCH path = shortestPath(
    (p1:Person {{name: '{person_names[0]}'}})-[:KNOWS*..6]-(p2:Person {{name: '{person_names[1]}'}})
)
RETURN [node in nodes(path) | node.name] as path_nodes,
       length(path) as path_length
LIMIT 1
                    """.strip()
                    
                    cypher_queries.append((f"Shortest Path - {person_names[0]} to {person_names[1]}", path_query))
                    path_result = self.db.query(path_query)
                    if path_result:
                        context['connection_path'] = path_result
                        print(f"✅ Found path of length {path_result[0]['path_length']}")
                except Exception as e:
                    print(f"❌ Error finding path: {e}")
        
        return context, cypher_queries  # Return both context and queries
    
    def _extract_entities_from_history(self, conversation_history):
        """Extract entities mentioned in previous conversation"""
        entities = {
            'locations': [],
            'persons': [],
            'organizations': []
        }
        
        if not conversation_history:
            return entities
        
        # Look at last 2-3 exchanges
        recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        
        for msg in recent_history:
            content = msg.get('content', '')
            
            # Extract locations
            entities['locations'].extend(self._extract_locations(content))
            
            # Extract person names
            entities['persons'].extend(self._extract_person_names(content))
            
            # Extract organizations
            entities['organizations'].extend(self._extract_organizations(content))
        
        return entities
    
    def _extract_locations(self, question):
        """Extract location names from question"""
        try:
            all_locations = self.db.query("MATCH (l:Location) RETURN l.name as name")
            locations_found = []
            q_lower = question.lower()
            
            for loc in all_locations:
                if loc['name'].lower() in q_lower:
                    locations_found.append(loc['name'])
            
            return locations_found
        except:
            return []
    
    def _extract_crime_types(self, question):
        """Extract crime types from question"""
        crime_types_known = [
            "Theft", "Battery", "Criminal Damage", "Assault", "Burglary",
            "Motor Vehicle Theft", "Robbery", "Deceptive Practice",
            "Criminal Trespass", "Narcotics", "Weapons Violation"
        ]
        
        found_types = []
        q_lower = question.lower()
        
        for ctype in crime_types_known:
            if ctype.lower() in q_lower:
                found_types.append(ctype)
        
        return found_types
    
    def _extract_person_names(self, question):
        """Extract potential person names from question - IMPROVED"""
        # Common words to exclude
        exclude_words = [
            'i', 'chicago', 'det', 'detective', 'side', 'west', 'east', 'north', 
            'south', 'river', 'downtown', 'gang', 'crew', 'burglars', 'dealers',
            'syndicate', 'street', 'the', 'a', 'an'
        ]
        
        words = question.split()
        potential_names = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Skip if not capitalized or is excluded
            if len(word) == 0 or not word[0].isupper() or word.lower() in exclude_words:
                i += 1
                continue
            
            # Check if next word is also capitalized (likely a full name)
            if i + 1 < len(words) and len(words[i+1]) > 0 and words[i+1][0].isupper():
                next_word = words[i+1]
                
                # Skip if next word is excluded (like "Side" in "East Side")
                if next_word.lower() not in exclude_words:
                    full_name = f"{word} {next_word}"
                    
                    # Remove punctuation
                    full_name = full_name.rstrip('.,!?*')
                    
                    potential_names.append(full_name)
                    i += 2  # Skip both words
                    continue
            
            i += 1
        
        print(f"  📝 Extracted person names: {potential_names}")
        return potential_names
    
    def _extract_organizations(self, question):
        """Extract organization names from question"""
        try:
            all_orgs = self.db.query("MATCH (o:Organization) RETURN o.name as name")
            orgs_found = []
            q_lower = question.lower()
            
            for org in all_orgs:
                if org['name'].lower() in q_lower:
                    orgs_found.append(org['name'])
            
            return orgs_found
        except:
            return []
    
    def _generate_with_llm_conversational(self, question, context, conversation_history):
        """Generate answer using LLM with conversation awareness"""
        
        system_prompt = """You are a crime investigation AI assistant analyzing data from a Neo4j knowledge graph.

CRITICAL ANTI-HALLUCINATION RULES:
1. ONLY use data explicitly provided in the context below
2. NEVER make up names, numbers, or details not in the data
3. If you see "all_weapons" with 13 items, say "13 weapons" NOT "30 weapons"
4. If specific names aren't in the data, say "the data shows X organizations" instead of making up organization names
5. Count items in the data - don't use round numbers unless they're exact
6. If asked for details not in the data, say "I don't have that information in the current data"

RESPONSE STYLE:
- Write 2-4 natural paragraphs (NOT bullet lists or tables)
- Bold **important facts** with double asterisks
- Be conversational but FACTUAL
- End with a relevant follow-up question

WHAT TO BOLD:
- **Actual names** from the data (persons, organizations, locations)
- **Exact numbers** from the data (not estimates)
- **Crime types** when mentioned
- **Key findings** that are in the data

VERIFICATION CHECKLIST:
Before writing each fact, ask yourself:
✓ Is this EXACT information in the context data?
✓ Am I using the ACTUAL count from the data?
✓ Am I using REAL names from the results?
✓ Or am I inferring/estimating/making it up?

If you can't verify it's in the data → DON'T SAY IT

Example CORRECT response:
"I found **5 organizations** in the database. The largest is **South Side Syndicate** with **40 members**, followed by **West Side Crew** with **25 members**. Based on the member data, I can see **40 gang members** across these organizations."

Example INCORRECT response (HALLUCINATION):
"I found 5 organizations. Carlos Rodriguez and Michael Brown are key members..." ← WRONG if these names aren't in the org_members data!

REMEMBER: You are showing WHAT IS IN THE DATABASE, not what MIGHT be there."""
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        for msg in recent_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Format context - SHOW EXACT DATA
        context_str = "\n=== EXACT DATA FROM DATABASE ===\n\n"
        for key, value in context.items():
            if value:
                context_str += f"\n{key.replace('_', ' ').upper()}:\n"
                
                # Show full data for critical fields
                if isinstance(value, list):
                    context_str += f"COUNT: {len(value)} items\n"
                    context_str += f"DATA: {json.dumps(value, indent=2, default=str)[:2000]}\n"
                else:
                    context_str += f"{json.dumps(value, indent=2, default=str)}\n"
        
        context_str += "\n=== END OF DATABASE DATA ===\n"
        context_str += "\nCRITICAL: Use ONLY the data above. If you say '30 weapons' but the data shows 13, you are HALLUCINATING."
        
        # Add current question
        messages.append({
            "role": "user",
            "content": f"{question}\n\n{context_str}"
        })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,  # LOWERED from 0.7 - less creativity = less hallucination
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    def _generate_fallback(self, question, context):
        """Generate detailed answer without LLM"""
        answer = ""
        
        # Organizations
        if 'all_organizations' in context and context['all_organizations']:
            answer += "**🏢 Criminal Organizations:**\n\n"
            for org in context['all_organizations']:
                answer += f"- **{org['name']}** ({org['type']})\n"
                answer += f"  Territory: {org['territory']} | Members: {org['members']}\n"
            answer += "\n"
        
        if 'organization_members' in context and context['organization_members']:
            answer += "**👥 Key Members:**\n\n"
            for member in context['organization_members'][:10]:
                answer += f"- {member['member']} ({member['rank']}) - {member['organization']}\n"
            answer += "\n"
        
        # Evidence
        if 'all_evidence' in context and context['all_evidence']:
            answer += "**🔍 Evidence:**\n\n"
            for ev in context['all_evidence'][:10]:
                answer += f"- **{ev['id']}**: {ev['description']} ({ev['significance']})\n"
            answer += "\n"
        
        # Locations
        location_keys = [k for k in context.keys() if 'suspects_in_' in k]
        for key in location_keys:
            location = key.replace('suspects_in_', '')
            suspects = context[key]
            if suspects:
                answer += f"**🔍 Suspects in {location}:**\n\n"
                for s in suspects[:10]:
                    answer += f"- {s['name']} (Age: {s['age']}, Crimes: {s['crime_count']})\n"
                answer += "\n"
        
        # Hotspots
        if 'hotspots' in context and context['hotspots']:
            answer += "**🔥 Crime Hotspots:**\n\n"
            for h in context['hotspots'][:10]:
                answer += f"- {h['location']}: {h['crimes']} crimes\n"
            answer += "\n"
        
        # Default
        if not answer or len(answer) < 50:
            stats = context.get('database_stats', {})
            answer = "**📊 Database Overview:**\n\n"
            answer += f"- Crimes: {stats.get('total_crimes', 0)}\n"
            answer += f"- Suspects: {stats.get('total_persons', 0)}\n"
            answer += f"- Organizations: {stats.get('total_organizations', 0)}\n"
        
        return answer

# Test
if __name__ == "__main__":
    print("Testing Conversational Graph RAG")
    print("="*60)
    
    rag = GraphRAG()
    
    # Simulate conversation
    conversation = []
    
    questions = [
        "Which criminal organizations operate in Chicago?",
        "Tell me more about West Side Crew",
        "Who are their leaders?",
        "What crimes have they committed?"
    ]
    
    for q in questions:
        print(f"\nQ: {q}")
        result = rag.ask_with_context(q, conversation)
        print(f"A: {result['answer'][:200]}...")
        
        # Add to conversation
        conversation.append({"role": "user", "content": q})
        conversation.append({"role": "assistant", "content": result['answer']})