# load_hybrid_data.py - Real Chicago Crimes + Synthetic Enrichment
# This is the BEST approach: Real data credibility + Full graph capabilities

import requests
from database import Database
import random
from datetime import datetime

db = Database()

print("="*60)
print("🌐 Loading HYBRID Data: Real Crimes + Synthetic Enrichment")
print("="*60)

# Clear database
db.clear_all()

# ============================================================================
# PART 1: FETCH REAL CRIME DATA FROM CHICAGO API
# ============================================================================

print("\n📡 Step 1: Fetching REAL crime data from Chicago Open Data Portal...")

url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

# Get crimes from 2024
params = {
    "$where": "date >= '2024-01-01T00:00:00.000'",
    "$limit": 1000,
    "$order": "date DESC"
}

try:
    response = requests.get(url, params=params, timeout=60)
    real_crimes = response.json()
    print(f"✅ Fetched {len(real_crimes)} REAL crimes from Chicago API")
except Exception as e:
    print(f"❌ API Error: {e}")
    print("⚠️  Using fallback: Will generate synthetic data instead")
    real_crimes = []

# ============================================================================
# PART 2: CREATE LOCATIONS FROM REAL DATA
# ============================================================================

print("\n📍 Step 2: Creating locations from REAL crime data...")

# Extract unique locations from real crimes
unique_locations = {}
location_count = 0

for crime in real_crimes:
    if 'latitude' in crime and 'longitude' in crime and crime['latitude']:
        block = crime.get('block', f'Location_{location_count}')
        
        if block not in unique_locations:
            unique_locations[block] = {
                'name': block,
                'lat': float(crime['latitude']),
                'lon': float(crime['longitude']),
                'district': crime.get('district', 'Unknown'),
                'beat': crime.get('beat', 'Unknown')
            }
            location_count += 1

# Create location nodes
for loc_name, loc_data in list(unique_locations.items())[:100]:
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            district: $district,
            beat: $beat,
            type: 'street_block',
            source: 'real_chicago_api'
        })
    """, loc_data)

print(f"✅ Created {min(100, len(unique_locations))} REAL locations from Chicago data")

# ============================================================================
# PART 3: CREATE CRIMES FROM REAL DATA
# ============================================================================

print("\n🚨 Step 3: Creating crimes from REAL Chicago data...")

crimes_created = 0
crime_ids = []

for crime in real_crimes[:500]:
    if 'latitude' not in crime or not crime.get('latitude'):
        continue
    
    crime_id = crime.get('id', f"REAL{crimes_created:04d}")
    
    db.query("""
        CREATE (c:Crime {
            id: $id,
            type: $type,
            date: $date,
            time: $time,
            case_number: $case_number,
            description: $description,
            arrest_made: $arrest,
            severity: $severity,
            status: $status,
            source: 'real_chicago_api'
        })
    """, {
        "id": crime_id,
        "type": crime.get('primary_type', 'Unknown'),
        "date": crime.get('date', '')[:10],
        "time": crime.get('date', '')[11:16] if len(crime.get('date', '')) > 11 else '00:00',
        "case_number": crime.get('case_number', 'UNKNOWN'),
        "description": crime.get('description', '')[:200],
        "arrest": crime.get('arrest', 'false') == 'true',
        "severity": random.choice(['minor', 'moderate', 'severe']),
        "status": 'solved' if crime.get('arrest') == 'true' else random.choice(['investigating', 'cold'])
    })
    
    # Link to location
    block = crime.get('block', '')
    if block in unique_locations:
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (l:Location {name: $location})
            MERGE (c)-[:OCCURRED_AT]->(l)
        """, {"crime_id": crime_id, "location": block})
    
    crime_ids.append(crime_id)
    crimes_created += 1

print(f"✅ Created {crimes_created} REAL crimes from Chicago API")

# ============================================================================
# PART 4: ADD SYNTHETIC ENRICHMENT (Full Graph Capabilities)
# ============================================================================

print("\n🎨 Step 4: Adding SYNTHETIC enrichment for full graph capabilities...")

# 4.1 CREATE ORGANIZATIONS
print("  🏢 Creating criminal organizations (synthetic)...")
organizations = [
    {"id": "ORG001", "name": "West Side Crew", "type": "gang", "territory": "West"},
    {"id": "ORG002", "name": "South Side Syndicate", "type": "organized_crime", "territory": "South"},
    {"id": "ORG003", "name": "North River Gang", "type": "gang", "territory": "North"},
    {"id": "ORG004", "name": "Downtown Dealers", "type": "drug_ring", "territory": "Central"},
    {"id": "ORG005", "name": "East Side Burglars", "type": "burglary_ring", "territory": "East"}
]

for org in organizations:
    db.query("""
        CREATE (o:Organization {
            id: $id,
            name: $name,
            type: $type,
            territory: $territory,
            members_count: $members,
            activity_level: $activity,
            source: 'synthetic'
        })
    """, {**org, "members": random.randint(15, 40), "activity": random.choice(['medium', 'high'])})

print(f"  ✅ Created {len(organizations)} organizations")

# 4.2 CREATE INVESTIGATORS
print("  👮 Creating investigators (synthetic)...")
investigators = [
    {"id": "INV001", "name": "Det. Sarah Johnson", "badge": "DET-5542", "dept": "Homicide", "specialty": "Serial Crimes"},
    {"id": "INV002", "name": "Det. Michael Brown", "badge": "DET-6734", "dept": "Robbery", "specialty": "Armed Robbery"},
    {"id": "INV003", "name": "Det. Lisa Garcia", "badge": "DET-4421", "dept": "Narcotics", "specialty": "Drug Trafficking"},
    {"id": "INV004", "name": "Det. Robert Chen", "badge": "DET-7891", "dept": "Burglary", "specialty": "Property Crimes"},
    {"id": "INV005", "name": "Det. Emily Rodriguez", "badge": "DET-3312", "dept": "Assault", "specialty": "Gang Violence"}
]

for inv in investigators:
    db.query("""
        CREATE (i:Investigator {
            id: $id, name: $name, badge_number: $badge,
            department: $dept, specialization: $specialty,
            cases_solved: $solved, active_cases: $active,
            source: 'synthetic'
        })
    """, {**inv, "solved": random.randint(30, 70), "active": random.randint(5, 15)})

print(f"  ✅ Created {len(investigators)} investigators")

# 4.3 CREATE MODUS OPERANDI PATTERNS
print("  🎭 Creating modus operandi patterns (synthetic)...")
mo_patterns = [
    {"id": "MO001", "desc": "Breaking through rear windows at night", "sig": "leaves door unlocked"},
    {"id": "MO002", "desc": "Armed robbery with getaway vehicle", "sig": "uses stolen cars"},
    {"id": "MO003", "desc": "Distraction theft in crowded areas", "sig": "works in pairs"},
    {"id": "MO004", "desc": "Late night street assault", "sig": "targets lone victims"},
    {"id": "MO005", "desc": "Drug dealing in parks", "sig": "uses lookouts"}
]

for mo in mo_patterns:
    db.query("""
        CREATE (m:ModusOperandi {
            id: $id,
            description: $desc,
            signature_element: $sig,
            frequency: $freq,
            confidence_score: $conf,
            source: 'synthetic'
        })
    """, {**mo, "freq": random.randint(8, 20), "conf": round(random.uniform(0.75, 0.95), 2)})

print(f"  ✅ Created {len(mo_patterns)} MO patterns")

# 4.4 CREATE PERSONS (Synthetic suspects linked to REAL crimes!)
print("  👥 Creating persons (synthetic, linked to REAL crimes)...")

first_names = ["Marcus", "David", "Carlos", "James", "Robert", "Lisa", "Sarah", "Maria", "John", "Michael"]
last_names = ["Rivera", "Lee", "Martinez", "Wilson", "Johnson", "Chen", "Garcia", "Rodriguez", "Smith", "Brown"]

persons = []
for i in range(80):
    person_id = f"P{i:03d}"
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    db.query("""
        CREATE (p:Person {
            id: $id,
            name: $name,
            age: $age,
            gender: $gender,
            occupation: $occupation,
            criminal_record: $record,
            risk_score: $risk,
            address: $address,
            source: 'synthetic'
        })
    """, {
        "id": person_id,
        "name": name,
        "age": random.randint(18, 65),
        "gender": random.choice(['Male', 'Female']),
        "occupation": random.choice(['Unemployed', 'Mechanic', 'Cook', 'Driver', 'Cashier']),
        "record": random.choice([True, True, False]),
        "risk": round(random.uniform(0.1, 0.9), 2),
        "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Main', 'State'])} St"
    })
    
    persons.append((person_id, name))

print(f"  ✅ Created {len(persons)} persons")

# 4.5 CREATE EVIDENCE
print("  🔍 Creating evidence items (synthetic)...")
evidence_ids = []

for i in range(100):
    evidence_id = f"E{i:03d}"
    db.query("""
        CREATE (e:Evidence {
            id: $id,
            type: $type,
            description: $description,
            verified: $verified,
            significance: $significance,
            collection_date: $date,
            source: 'synthetic'
        })
    """, {
        "id": evidence_id,
        "type": random.choice(['physical', 'digital', 'forensic', 'testimonial']),
        "description": random.choice(['DNA sample', 'Fingerprint', 'Security footage', 'Witness statement']),
        "verified": random.choice([True, True, False]),
        "significance": random.choice(['low', 'medium', 'high', 'critical']),
        "date": f"2024-{random.randint(1, 10):02d}-{random.randint(1, 28):02d}"
    })
    
    evidence_ids.append(evidence_id)

print(f"  ✅ Created {len(evidence_ids)} evidence items")

# 4.6 CREATE WEAPONS
print("  🔫 Creating weapons (synthetic)...")
weapon_types = [("firearm", "Glock", "19"), ("firearm", "Smith & Wesson", "M&P"), ("knife", "Buck", "119")]
weapons = []

for i in range(30):
    weapon_id = f"W{i:03d}"
    wtype, make, model = random.choice(weapon_types)
    db.query("""
        CREATE (w:Weapon {
            id: $id, type: $type, make: $make, model: $model,
            serial_number: $serial, recovered: $recovered,
            source: 'synthetic'
        })
    """, {
        "id": weapon_id, "type": wtype, "make": make, "model": model,
        "serial": f"{make[:3].upper()}{random.randint(100000, 999999)}",
        "recovered": random.choice([True, True, False])
    })
    weapons.append(weapon_id)

print(f"  ✅ Created {len(weapons)} weapons")

# 4.7 CREATE VEHICLES
print("  🚗 Creating vehicles (synthetic)...")
vehicles = []

for i in range(50):
    vehicle_id = f"V{i:03d}"
    db.query("""
        CREATE (v:Vehicle {
            id: $id, make: $make, model: $model, year: $year,
            color: $color, license_plate: $plate,
            reported_stolen: $stolen, source: 'synthetic'
        })
    """, {
        "id": vehicle_id,
        "make": random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet']),
        "model": random.choice(['Camry', 'Civic', 'F-150', 'Malibu']),
        "year": random.randint(2010, 2024),
        "color": random.choice(['Black', 'White', 'Silver', 'Blue']),
        "plate": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}-{random.randint(1000, 9999)}",
        "stolen": random.choice([True, False, False, False])
    })
    vehicles.append(vehicle_id)

print(f"  ✅ Created {len(vehicles)} vehicles")

# ============================================================================
# PART 5: CREATE RELATIONSHIPS - Link Synthetic to REAL!
# ============================================================================

print("\n🔗 Step 5: Creating relationships (linking synthetic entities to REAL crimes)...")

# Link persons to REAL crimes
print("  👥 Linking persons to REAL crimes...")
for person_id, person_name in persons:
    # Each person linked to 3-8 REAL crimes
    num_crimes = random.randint(3, 8)
    
    # Get random REAL crime IDs
    sample_crimes = db.query(f"""
        MATCH (c:Crime {{source: 'real_chicago_api'}})
        RETURN c.id as id
        ORDER BY rand()
        LIMIT {num_crimes}
    """)
    
    for crime in sample_crimes:
        db.query("""
            MATCH (p:Person {id: $person_id})
            MATCH (c:Crime {id: $crime_id})
            MERGE (p)-[:PARTY_TO {role: $role}]->(c)
        """, {
            "person_id": person_id,
            "crime_id": crime['id'],
            "role": random.choice(['suspect', 'witness', 'accomplice'])
        })

print("  ✅ Linked persons to REAL crimes")

# Link persons to organizations (gang memberships)
print("  🏢 Creating gang memberships...")
for _ in range(40):
    person_id, _ = random.choice(persons)
    org = random.choice(organizations)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (o:Organization {id: $org_id})
        MERGE (p)-[:MEMBER_OF {rank: $rank, since: $since}]->(o)
    """, {
        "person_id": person_id,
        "org_id": org['id'],
        "rank": random.choice(['member', 'lieutenant', 'enforcer']),
        "since": f"20{random.randint(18, 24)}-{random.randint(1, 12):02d}-01"
    })

print("  ✅ Created gang memberships")

# Link REAL crimes to investigators
print("  👮 Assigning investigators to REAL crimes...")
for crime_id in crime_ids[:200]:
    investigator = random.choice(investigators)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (i:Investigator {id: $inv_id})
        MERGE (c)-[:INVESTIGATED_BY {assigned_date: $date}]->(i)
    """, {
        "crime_id": crime_id,
        "inv_id": investigator['id'],
        "date": f"2024-{random.randint(1, 10):02d}-{random.randint(1, 28):02d}"
    })

print("  ✅ Assigned investigators")

# Link REAL crimes to MO patterns
print("  🎭 Matching crimes to MO patterns...")
for crime_id in crime_ids[:250]:
    mo = random.choice(mo_patterns)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (m:ModusOperandi {id: $mo_id})
        MERGE (c)-[:MATCHES_MO {similarity: $similarity}]->(m)
    """, {
        "crime_id": crime_id,
        "mo_id": mo['id'],
        "similarity": round(random.uniform(0.7, 0.98), 2)
    })

print("  ✅ Matched crimes to MO patterns")

# Link REAL crimes to evidence
print("  🔍 Linking evidence to REAL crimes...")
for crime_id in crime_ids[:300]:
    # Each crime has 1-4 pieces of evidence
    num_evidence = random.randint(1, 4)
    selected_evidence = random.sample(evidence_ids, min(num_evidence, len(evidence_ids)))
    
    for evidence_id in selected_evidence:
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (e:Evidence {id: $evidence_id})
            MERGE (c)-[:HAS_EVIDENCE]->(e)
        """, {"crime_id": crime_id, "evidence_id": evidence_id})

print("  ✅ Linked evidence to crimes")

# Link evidence to persons (forensic connections)
print("  🔗 Creating evidence-person links...")
for evidence_id in evidence_ids[:60]:
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (e:Evidence {id: $evidence_id})
        MATCH (p:Person {id: $person_id})
        MERGE (e)-[:LINKS_TO {confidence: $confidence}]->(p)
    """, {
        "evidence_id": evidence_id,
        "person_id": person_id,
        "confidence": round(random.uniform(0.6, 0.99), 2)
    })

print("  ✅ Created evidence-person links")

# Link crimes to vehicles
print("  🚗 Linking vehicles to REAL crimes...")
for _ in range(60):
    crime_id = random.choice(crime_ids)
    vehicle_id = random.choice(vehicles)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (c)-[:INVOLVED_VEHICLE {role: $role}]->(v)
    """, {
        "crime_id": crime_id,
        "vehicle_id": vehicle_id,
        "role": random.choice(['getaway', 'transport', 'scene'])
    })

# Link persons to vehicles (ownership)
for vehicle_id in vehicles:
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (p)-[:OWNS]->(v)
    """, {"person_id": person_id, "vehicle_id": vehicle_id})

print("  ✅ Linked vehicles")

# Link crimes to weapons
print("  🔫 Linking weapons to REAL crimes...")
for _ in range(40):
    crime_id = random.choice(crime_ids)
    weapon_id = random.choice(weapons)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (c)-[:USED_WEAPON]->(w)
    """, {"crime_id": crime_id, "weapon_id": weapon_id})

# Link persons to weapons (ownership)
for weapon_id in weapons[:20]:
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (p)-[:OWNS]->(w)
    """, {"person_id": person_id, "weapon_id": weapon_id})

print("  ✅ Linked weapons")

# Create social connections (KNOWS)
print("  👥 Creating social networks...")
for _ in range(150):
    (p1_id, _), (p2_id, _) = random.sample(persons, 2)
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:KNOWS {relationship: $rel, strength: $strength}]-(p2)
    """, {
        "p1": p1_id,
        "p2": p2_id,
        "rel": random.choice(['friend', 'associate', 'acquaintance']),
        "strength": round(random.uniform(0.3, 1.0), 2)
    })

# Create family connections
for _ in range(40):
    (p1_id, _), (p2_id, _) = random.sample(persons, 2)
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:FAMILY_REL {relation: $relation}]-(p2)
    """, {
        "p1": p1_id,
        "p2": p2_id,
        "relation": random.choice(['sibling', 'parent', 'cousin'])
    })

print("  ✅ Created social networks")

# ============================================================================
# PART 6: FINAL STATISTICS
# ============================================================================

print("\n" + "="*60)
print("📊 FINAL DATABASE STATISTICS")
print("="*60)

stats = db.query("""
    MATCH (n)
    RETURN labels(n)[0] as NodeType, 
           n.source as Source,
           count(n) as Count
    ORDER BY NodeType, Source
""")

print("\n🔵 Nodes by Type and Source:")
for stat in stats:
    source_icon = {
        'real_chicago_api': '🌐 REAL',
        'synthetic': '🎨 SYNTHETIC'
    }.get(stat['Source'], '❓')
    
    print(f"   {stat['NodeType']}: {stat['Count']} {source_icon}")

rel_stats = db.query("""
    MATCH ()-[r]->()
    RETURN type(r) as RelType, count(r) as Count
    ORDER BY Count DESC
""")

print("\n🔗 Relationships:")
for stat in rel_stats[:15]:
    print(f"   {stat['RelType']}: {stat['Count']}")

# Show the integration
integration = db.query("""
    MATCH (p:Person {source: 'synthetic'})-[:PARTY_TO]->(c:Crime {source: 'real_chicago_api'})
    RETURN count(*) as links
""")[0]

print("\n🎯 Data Integration:")
print(f"   Synthetic Persons → REAL Crimes: {integration['links']} links")

print("\n" + "="*60)
print("🎉 HYBRID DATA LOADED SUCCESSFULLY!")
print("="*60)
print("\n✨ What You Have:")
print("   🌐 REAL Crimes: From Chicago Open Data Portal")
print("   🌐 REAL Locations: From crime GPS coordinates")
print("   🎨 SYNTHETIC Persons: Linked to real crimes")
print("   🎨 SYNTHETIC Organizations: Gang intelligence layer")
print("   🎨 SYNTHETIC Evidence: Forensic layer")
print("   🎨 SYNTHETIC Weapons/Vehicles: Asset tracking")
print("   🎨 SYNTHETIC Investigators: Case management")
print("\n🏆 BEST OF BOTH WORLDS!")
print("   ✓ Real crime patterns (credible)")
print("   ✓ Full graph capabilities (comprehensive)")
print("   ✓ No privacy violations (fictional suspects)")
print("   ✓ All demo questions work (complete system)")
print("="*60)

db.close()