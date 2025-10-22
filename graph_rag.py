import config
from database import Database
import json
import re

class GraphRAG:
    def __init__(self):
        self.db = Database()
        self.model = config.MODEL_NAME
        
        # Try to initialize OpenAI
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
            self.use_llm = True
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
        # Step 1: RETRIEVE - Get ALL relevant data
        context = self._smart_retrieve(question, conversation_history)
        
        # Step 2: GENERATE answer with conversation awareness
        if self.use_llm:
            try:
                answer = self._generate_with_llm_conversational(
                    question, 
                    context, 
                    conversation_history
                )
            except Exception as e:
                print(f"⚠️ LLM failed: {e}")
                answer = self._generate_fallback(question, context)
        else:
            answer = self._generate_fallback(question, context)
        
        return {
            'answer': answer,
            'sources': list(context.keys())
        }
    
    def _smart_retrieve(self, question, conversation_history):
        """ENHANCED retrieval with conversation awareness"""
        context = {}
        q = question.lower()
        
        # Check conversation history for entity references
        entities_from_history = self._extract_entities_from_history(conversation_history)
        
        # Extract entities from question
        locations = self._extract_locations(question)
        crime_types = self._extract_crime_types(question)
        person_names = self._extract_person_names(question)
        organizations = self._extract_organizations(question)
        
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
            context['database_stats'] = {
                'total_crimes': self.db.query("MATCH (c:Crime) RETURN count(c) as n")[0]['n'],
                'total_persons': self.db.query("MATCH (p:Person) RETURN count(p) as n")[0]['n'],
                'total_locations': self.db.query("MATCH (l:Location) RETURN count(l) as n")[0]['n'],
                'total_organizations': self.db.query("MATCH (o:Organization) RETURN count(o) as n")[0]['n'],
                'total_evidence': self.db.query("MATCH (e:Evidence) RETURN count(e) as n")[0]['n']
            }
        except:
            context['database_stats'] = {'error': 'Could not fetch stats'}
        
        # ========== ORGANIZATION QUERIES ==========
        if any(w in q for w in ['organization', 'gang', 'crew', 'syndicate', 'cartel', 'ring']) or organizations:
            try:
                context['all_organizations'] = self.db.query("""
                    MATCH (o:Organization)
                    RETURN o.name as name, o.type as type, 
                           o.territory as territory, o.members_count as members,
                           o.activity_level as activity
                    ORDER BY o.members_count DESC
                """)
                
                context['organization_members'] = self.db.query("""
                    MATCH (p:Person)-[r:MEMBER_OF]->(o:Organization)
                    RETURN o.name as organization, p.name as member,
                           p.age as age, r.rank as rank
                    ORDER BY o.name, r.rank
                    LIMIT 50
                """)
            except Exception as e:
                print(f"Error fetching organizations: {e}")
        
        # Specific organization query
        if organizations:
            for org in organizations[:3]:
                try:
                    org_crimes = self.db.query(f"""
                        MATCH (p:Person)-[:MEMBER_OF]->(o:Organization {{name: '{org}'}})
                        MATCH (p)-[:PARTY_TO]->(c:Crime)-[:OCCURRED_AT]->(l:Location)
                        RETURN c.type as crime_type, c.date as date,
                               l.name as location, p.name as member
                        ORDER BY c.date DESC
                        LIMIT 30
                    """)
                    
                    if org_crimes:
                        context[f'org_{org}_crimes'] = org_crimes
                except Exception as e:
                    print(f"Error fetching {org} crimes: {e}")
        
        # ========== EVIDENCE QUERIES ==========
        if any(w in q for w in ['evidence', 'proof', 'forensic', 'dna', 'fingerprint']):
            try:
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
            except Exception as e:
                print(f"Error fetching evidence: {e}")
        
        # ========== INVESTIGATOR QUERIES ==========
        if any(w in q for w in ['investigator', 'detective', 'officer', 'assigned']):
            try:
                context['all_investigators'] = self.db.query("""
                    MATCH (i:Investigator)
                    RETURN i.name as name, i.badge_number as badge,
                           i.department as department, i.specialization as specialization,
                           i.cases_solved as solved, i.active_cases as active
                    ORDER BY i.cases_solved DESC
                """)
            except Exception as e:
                print(f"Error fetching investigators: {e}")
        
        # ========== MO PATTERNS ==========
        if any(w in q for w in ['modus operandi', 'mo', 'pattern', 'method', 'signature', 'similar']):
            try:
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
            except Exception as e:
                print(f"Error fetching MO patterns: {e}")
        
        # ========== VEHICLES ==========
        if any(w in q for w in ['vehicle', 'car', 'truck', 'getaway', 'stolen']):
            try:
                context['all_vehicles'] = self.db.query("""
                    MATCH (v:Vehicle)
                    RETURN v.id as id, v.make as make, v.model as model,
                           v.year as year, v.color as color, 
                           v.license_plate as plate, v.reported_stolen as stolen
                    ORDER BY v.reported_stolen DESC
                    LIMIT 30
                """)
            except Exception as e:
                print(f"Error fetching vehicles: {e}")
        
        # ========== WEAPONS ==========
        if any(w in q for w in ['weapon', 'gun', 'firearm', 'knife', 'armed']):
            try:
                context['all_weapons'] = self.db.query("""
                    MATCH (w:Weapon)
                    RETURN w.id as id, w.type as type, w.make as make,
                           w.model as model, w.recovered as recovered
                    LIMIT 30
                """)
            except Exception as e:
                print(f"Error fetching weapons: {e}")
        
        # ========== LOCATION-SPECIFIC ==========
        if locations:
            for location in locations[:3]:
                try:
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
                except Exception as e:
                    print(f"Error fetching {location} data: {e}")
        
        # ========== PERSON-SPECIFIC ==========
        if person_names:
            for name in person_names[:3]:
                try:
                    context[f'{name}_connections'] = self.db.query(f"""
                        MATCH (p:Person)-[:KNOWS*1..2]-(connected:Person)
                        WHERE p.name =~ '(?i).*{name}.*'
                        RETURN DISTINCT connected.name as name, 
                               connected.age as age,
                               connected.criminal_record as has_record
                        LIMIT 30
                    """)
                except Exception as e:
                    print(f"Error fetching {name} connections: {e}")
        
        # ========== PATTERNS ==========
        if any(w in q for w in ['hotspot', 'dangerous', 'where', 'most crime']):
            try:
                context['hotspots'] = self.db.query("""
                    MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
                    RETURN l.name as location, l.district as district,
                           count(c) as crimes
                    ORDER BY crimes DESC
                    LIMIT 15
                """)
            except Exception as e:
                print(f"Error fetching hotspots: {e}")
        
        if any(w in q for w in ['repeat', 'offender', 'criminal', 'suspect']):
            try:
                context['repeat_offenders'] = self.db.query("""
                    MATCH (p:Person)-[:PARTY_TO]->(c:Crime)
                    WITH p, count(c) as crimes
                    WHERE crimes >= 2
                    OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
                    RETURN p.name as name, p.age as age, crimes,
                           o.name as organization
                    ORDER BY crimes DESC
                    LIMIT 20
                """)
            except Exception as e:
                print(f"Error fetching repeat offenders: {e}")
        
        if any(w in q for w in ['network', 'connected', 'know', 'associate']):
            try:
                context['criminal_networks'] = self.db.query("""
                    MATCH (p1:Person)-[:KNOWS]-(p2:Person)
                    WHERE EXISTS((p1)-[:PARTY_TO]->(:Crime))
                      AND EXISTS((p2)-[:PARTY_TO]->(:Crime))
                    RETURN p1.name as person1, p2.name as person2
                    LIMIT 30
                """)
            except Exception as e:
                print(f"Error fetching networks: {e}")
        
        return context
    
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
        """Extract potential person names from question"""
        words = question.split()
        potential_names = []
        
        for i, word in enumerate(words):
            if len(word) > 0 and word[0].isupper() and word.lower() not in ['i', 'chicago', 'det', 'detective']:
                if i + 1 < len(words) and len(words[i+1]) > 0 and words[i+1][0].isupper():
                    potential_names.append(f"{word} {words[i+1]}")
        
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
        
        system_prompt = """You are a conversational crime investigation AI assistant. You're having a natural dialogue with a detective.

CRITICAL RESPONSE STYLE:
- Write in natural, flowing paragraphs - NOT tables, NOT bullet points
- Be conversational like you're talking to a colleague over coffee
- Use contractions (I've, there's, that's) to sound natural
- After answering, ask a relevant follow-up question to continue the conversation
- Keep responses concise but informative (3-4 short paragraphs max)

FORMATTING RULES:
❌ NO markdown tables
❌ NO bullet point lists
❌ NO structured reports
❌ NO headers like "Key Takeaways" or "Quick Summary"
✅ YES natural paragraphs
✅ YES conversational tone
✅ YES follow-up questions at the end
✅ YES bold **important names, numbers, and key facts** using **double asterisks**

WHAT TO BOLD:
- **Names** of persons, organizations, locations
- **Numbers** (crime counts, ages, percentages, scores)
- **Crime types** when first mentioned
- **Key findings** or important insights
- **Risk levels** or severity indicators

RESPONSE PATTERN:
1. Direct answer (1-2 sentences with **bolded key info**)
2. Key details in natural prose (2-3 sentences with **bolded numbers and names**)
3. Relevant insight or connection (1-2 sentences)
4. Ask a follow-up question to continue investigation

Example Response Style:
"I found **5 criminal organizations** operating in Chicago. The most active is **West Side Crew** with **25 members** operating in the West district, followed by **South Side Syndicate** with **40 members** in the South. West Side Crew has been particularly aggressive lately with **47 crimes** in the last 6 months.

What's interesting is that West Side Crew members have been spotted in **Loop** recently, which is South Side Syndicate territory. This could indicate a territory expansion or upcoming conflict.

Would you like me to show you the specific members of West Side Crew, or should we look at their recent crime patterns?"

CONVERSATION MEMORY:
- Remember what was discussed in previous messages
- Use context naturally without explicitly stating "based on our previous conversation"
- Handle pronouns (they, them, it, those) by resolving to entities from context"""
        
        # Build conversation history for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 5 exchanges)
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        for msg in recent_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Format context
        context_str = "\n**Retrieved Data from Knowledge Graph:**\n\n"
        for key, value in context.items():
            if value:
                context_str += f"\n**{key.replace('_', ' ').title()}:**\n"
                context_str += f"{json.dumps(value, indent=2, default=str)[:1500]}\n"
        
        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"{question}\n\n{context_str}\n\nIMPORTANT: Respond in natural conversational paragraphs, NOT tables or lists. End with a follow-up question."
        })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
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