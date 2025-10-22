from database import Database
import random
from datetime import datetime, timedelta

db = Database()

print("=" * 60)
print("🚀 Loading ENHANCED Chicago Crime Data with Rich Schema")
print("=" * 60)

# Clear database
db.clear_all()

# ============================================================================
# 1. CREATE LOCATIONS (Enhanced with more properties)
# ============================================================================
locations = [
    {"name": "Loop", "lat": 41.8781, "lon": -87.6298, "type": "commercial", "district": "Central"},
    {"name": "Near North", "lat": 41.8969, "lon": -87.6324, "type": "mixed", "district": "North"},
    {"name": "Lincoln Park", "lat": 41.9216, "lon": -87.6473, "type": "residential", "district": "North"},
    {"name": "Lakeview", "lat": 41.9403, "lon": -87.6538, "type": "residential", "district": "North"},
    {"name": "Hyde Park", "lat": 41.7943, "lon": -87.5907, "type": "residential", "district": "South"},
    {"name": "Pilsen", "lat": 41.8559, "lon": -87.6594, "type": "residential", "district": "West"},
    {"name": "Humboldt Park", "lat": 41.9003, "lon": -87.7012, "type": "public", "district": "West"},
    {"name": "Logan Square", "lat": 41.9297, "lon": -87.7019, "type": "residential", "district": "Northwest"},
    {"name": "Wicker Park", "lat": 41.9097, "lon": -87.6774, "type": "mixed", "district": "West"},
    {"name": "River North", "lat": 41.8919, "lon": -87.6342, "type": "commercial", "district": "Central"},
    {"name": "Gold Coast", "lat": 41.9015, "lon": -87.6269, "type": "residential", "district": "North"},
    {"name": "Chinatown", "lat": 41.8528, "lon": -87.6320, "type": "commercial", "district": "South"},
    {"name": "Bronzeville", "lat": 41.8120, "lon": -87.6165, "type": "residential", "district": "South"},
    {"name": "South Loop", "lat": 41.8669, "lon": -87.6275, "type": "mixed", "district": "Central"},
    {"name": "West Loop", "lat": 41.8825, "lon": -87.6472, "type": "commercial", "district": "Central"},
    {"name": "Old Town", "lat": 41.9105, "lon": -87.6376, "type": "residential", "district": "North"},
    {"name": "Bucktown", "lat": 41.9191, "lon": -87.6797, "type": "residential", "district": "Northwest"},
    {"name": "Wrigleyville", "lat": 41.9484, "lon": -87.6553, "type": "mixed", "district": "North"},
    {"name": "Little Village", "lat": 41.8452, "lon": -87.7128, "type": "residential", "district": "Southwest"},
    {"name": "Streeterville", "lat": 41.8928, "lon": -87.6166, "type": "commercial", "district": "North"},
]

print(f"📍 Creating {len(locations)} enhanced locations...")
for loc in locations:
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            type: $type,
            district: $district,
            crime_rate: $crime_rate
        })
    """, {**loc, "crime_rate": round(random.uniform(0.2, 0.9), 2)})
print(f"✅ Created {len(locations)} locations with enhanced properties")

# ============================================================================
# 2. CREATE ORGANIZATIONS (NEW!)
# ============================================================================
print("🏢 Creating criminal organizations...")
organizations = [
    {"id": "ORG001", "name": "West Side Crew", "type": "gang", "territory": "West", "members_count": 25, "activity_level": "high"},
    {"id": "ORG002", "name": "South Side Syndicate", "type": "organized_crime", "territory": "South", "members_count": 40, "activity_level": "high"},
    {"id": "ORG003", "name": "North River Gang", "type": "gang", "territory": "North", "members_count": 15, "activity_level": "medium"},
    {"id": "ORG004", "name": "Downtown Dealers", "type": "drug_ring", "territory": "Central", "members_count": 30, "activity_level": "high"},
    {"id": "ORG005", "name": "East Side Burglars", "type": "burglary_ring", "territory": "East", "members_count": 12, "activity_level": "medium"}
]

for org in organizations:
    db.query("""
        CREATE (o:Organization {
            id: $id,
            name: $name,
            type: $type,
            territory: $territory,
            members_count: $members_count,
            activity_level: $activity_level
        })
    """, org)
print(f"✅ Created {len(organizations)} organizations")

# ============================================================================
# 3. CREATE INVESTIGATORS (NEW!)
# ============================================================================
print("👮 Creating investigators...")
investigators = [
    {"id": "INV001", "name": "Det. Sarah Johnson", "badge": "DET-5542", "dept": "Homicide", "cases_solved": 47, "specialization": "Serial Crimes"},
    {"id": "INV002", "name": "Det. Michael Brown", "badge": "DET-6734", "dept": "Robbery", "cases_solved": 63, "specialization": "Armed Robbery"},
    {"id": "INV003", "name": "Det. Lisa Garcia", "badge": "DET-4421", "dept": "Narcotics", "cases_solved": 38, "specialization": "Drug Trafficking"},
    {"id": "INV004", "name": "Det. Robert Chen", "badge": "DET-7891", "dept": "Burglary", "cases_solved": 52, "specialization": "Property Crimes"},
    {"id": "INV005", "name": "Det. Emily Rodriguez", "badge": "DET-3312", "dept": "Assault", "cases_solved": 41, "specialization": "Gang Violence"}
]

for inv in investigators:
    db.query("""
        CREATE (i:Investigator {
            id: $id,
            name: $name,
            badge_number: $badge,
            department: $dept,
            cases_solved: $cases_solved,
            specialization: $specialization,
            active_cases: $active_cases
        })
    """, {**inv, "active_cases": random.randint(5, 15)})
print(f"✅ Created {len(investigators)} investigators")

# ============================================================================
# 4. CREATE MODUS OPERANDI PATTERNS (NEW!)
# ============================================================================
print("🎭 Creating modus operandi patterns...")
mo_patterns = [
    {"id": "MO001", "description": "Breaking through rear windows at night", "signature": "leaves door unlocked", "frequency": 12},
    {"id": "MO002", "description": "Armed robbery with getaway vehicle", "signature": "uses stolen cars", "frequency": 8},
    {"id": "MO003", "description": "Distraction theft in crowded areas", "signature": "works in pairs", "frequency": 15},
    {"id": "MO004", "description": "Late night street assault", "signature": "targets lone victims", "frequency": 10},
    {"id": "MO005", "description": "Drug dealing in parks", "signature": "uses lookouts", "frequency": 20}
]

for mo in mo_patterns:
    db.query("""
        CREATE (m:ModusOperandi {
            id: $id,
            description: $description,
            signature_element: $signature,
            frequency: $frequency,
            confidence_score: $confidence
        })
    """, {**mo, "confidence": round(random.uniform(0.7, 0.95), 2)})
print(f"✅ Created {len(mo_patterns)} MO patterns")

# ============================================================================
# 5. CREATE PERSONS (Enhanced with more properties)
# ============================================================================
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
              "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
              "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
              "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
              "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
              "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa"]

last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
             "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
             "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris"]

occupations = ["Unemployed", "Mechanic", "Cashier", "Cook", "Driver", "Warehouse Worker", 
               "Bartender", "Security Guard", "Construction Worker", "Retail Worker"]

print("👥 Creating 120 persons with enhanced properties...")
persons = []
for i in range(120):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    db.query("""
        CREATE (p:Person {
            id: $id,
            name: $name,
            age: $age,
            gender: $gender,
            occupation: $occupation,
            criminal_record: $criminal_record,
            risk_score: $risk_score,
            address: $address
        })
    """, {
        "id": f"P{i:03d}",
        "name": name,
        "age": random.randint(18, 65),
        "gender": random.choice(["Male", "Female"]),
        "occupation": random.choice(occupations),
        "criminal_record": random.choice([True, True, False]),  # 66% have records
        "risk_score": round(random.uniform(0.1, 0.9), 2),
        "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Main', 'Park', 'Lake'])} St"
    })
    persons.append((f"P{i:03d}", name))
print(f"✅ Created {len(persons)} persons with enhanced attributes")

# ============================================================================
# 6. CREATE VEHICLES (NEW!)
# ============================================================================
print("🚗 Creating vehicles...")
vehicle_makes = ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes", "Dodge"]
vehicle_models = ["Camry", "Civic", "F-150", "Malibu", "Altima", "X5", "C-Class", "Charger"]
colors = ["Black", "White", "Silver", "Red", "Blue", "Gray", "Green"]

vehicles = []
for i in range(50):
    vehicle_id = f"V{i:03d}"
    db.query("""
        CREATE (v:Vehicle {
            id: $id,
            make: $make,
            model: $model,
            year: $year,
            color: $color,
            license_plate: $plate,
            reported_stolen: $stolen
        })
    """, {
        "id": vehicle_id,
        "make": random.choice(vehicle_makes),
        "model": random.choice(vehicle_models),
        "year": random.randint(2010, 2024),
        "color": random.choice(colors),
        "plate": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}-{random.randint(1000,9999)}",
        "stolen": random.choice([True, False, False, False])  # 25% stolen
    })
    vehicles.append(vehicle_id)
print(f"✅ Created {len(vehicles)} vehicles")

# ============================================================================
# 7. CREATE WEAPONS (NEW!)
# ============================================================================
print("🔫 Creating weapons...")
weapon_types = [
    ("firearm", "Glock", "19"),
    ("firearm", "Smith & Wesson", "M&P"),
    ("firearm", "Sig Sauer", "P320"),
    ("knife", "Buck", "119"),
    ("knife", "Ka-Bar", "Combat"),
    ("blunt_object", "Baseball Bat", "Louisville"),
    ("firearm", "Colt", "1911"),
]

weapons = []
for i in range(30):
    weapon_id = f"W{i:03d}"
    wtype, make, model = random.choice(weapon_types)
    db.query("""
        CREATE (w:Weapon {
            id: $id,
            type: $type,
            make: $make,
            model: $model,
            serial_number: $serial,
            recovered: $recovered
        })
    """, {
        "id": weapon_id,
        "type": wtype,
        "make": make,
        "model": model,
        "serial": f"{make[:3].upper()}{random.randint(100000,999999)}",
        "recovered": random.choice([True, True, False])  # 66% recovered
    })
    weapons.append(weapon_id)
print(f"✅ Created {len(weapons)} weapons")

# ============================================================================
# 8. CREATE CRIMES (Enhanced with more properties)
# ============================================================================
crime_types = [
    "Theft", "Battery", "Criminal Damage", "Assault", "Burglary",
    "Motor Vehicle Theft", "Robbery", "Deceptive Practice",
    "Criminal Trespass", "Narcotics", "Weapons Violation",
    "Other Offense", "Offense Involving Children", "Public Peace Violation"
]

severities = ["minor", "moderate", "severe", "critical"]
statuses = ["reported", "investigating", "solved", "cold"]

print("🚨 Creating 350 crimes with enhanced metadata...")
start_date = datetime(2024, 1, 1)
crimes = []

for i in range(350):
    crime_type = random.choice(crime_types)
    location = random.choice(locations)
    date = start_date + timedelta(days=random.randint(0, 300))
    
    # Determine severity based on crime type
    if crime_type in ["Assault", "Robbery", "Weapons Violation"]:
        severity = random.choice(["severe", "critical"])
    elif crime_type in ["Theft", "Criminal Trespass"]:
        severity = random.choice(["minor", "moderate"])
    else:
        severity = random.choice(severities)
    
    crime_id = f"C{i:04d}"
    
    # Create crime
    db.query("""
        CREATE (c:Crime {
            id: $id,
            type: $type,
            date: $date,
            time: $time,
            case_number: $case,
            severity: $severity,
            status: $status,
            description: $description
        })
    """, {
        "id": crime_id,
        "type": crime_type,
        "date": date.strftime("%Y-%m-%d"),
        "time": f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
        "case": f"CHI{random.randint(100000,999999)}",
        "severity": severity,
        "status": random.choice(statuses),
        "description": f"{crime_type} incident at {location['name']}"
    })
    
    crimes.append((crime_id, crime_type, location['name']))

print(f"✅ Created {len(crimes)} crimes")

# ============================================================================
# 9. CREATE EVIDENCE (NEW!)
# ============================================================================
print("🔍 Creating evidence...")
evidence_types = ["physical", "digital", "testimonial", "forensic"]
evidence_descriptions = [
    "Fingerprint on door handle",
    "DNA sample from scene",
    "Security camera footage",
    "Witness statement",
    "Blood sample",
    "Tire tracks",
    "Cell phone records",
    "Fibers from clothing",
    "Shell casings",
    "Tool marks"
]

evidence_items = []
for i in range(100):
    evidence_id = f"E{i:03d}"
    db.query("""
        CREATE (e:Evidence {
            id: $id,
            type: $type,
            description: $description,
            collection_date: $date,
            verified: $verified,
            significance: $significance
        })
    """, {
        "id": evidence_id,
        "type": random.choice(evidence_types),
        "description": random.choice(evidence_descriptions),
        "date": (start_date + timedelta(days=random.randint(0, 300))).strftime("%Y-%m-%d"),
        "verified": random.choice([True, True, True, False]),  # 75% verified
        "significance": random.choice(["low", "medium", "high", "critical"])
    })
    evidence_items.append(evidence_id)
print(f"✅ Created {len(evidence_items)} evidence items")

# ============================================================================
# 10. CREATE RELATIONSHIPS - THE KEY PART!
# ============================================================================
print("🔗 Creating rich relationships...")

# Crime-Location relationships
print("  - Linking crimes to locations...")
for crime_id, crime_type, location_name in crimes:
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (l:Location {name: $location})
        MERGE (c)-[:OCCURRED_AT]->(l)
    """, {"crime_id": crime_id, "location": location_name})

# Person-Crime relationships (PARTY_TO)
print("  - Linking persons to crimes...")
for crime_id, crime_type, location_name in crimes:
    # 1-3 persons per crime
    num_persons = random.randint(1, 3)
    selected_persons = random.sample(persons, num_persons)
    
    for person_id, person_name in selected_persons:
        role = random.choice(["suspect", "accomplice", "witness", "victim"])
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (p:Person {id: $person_id})
            MERGE (p)-[:PARTY_TO {role: $role}]->(c)
        """, {"crime_id": crime_id, "person_id": person_id, "role": role})

# Person-Organization relationships (MEMBER_OF) - NEW!
print("  - Creating organization memberships...")
for _ in range(80):
    person_id, person_name = random.choice(persons)
    org = random.choice(organizations)
    rank = random.choice(["member", "lieutenant", "enforcer", "associate"])
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (o:Organization {id: $org_id})
        MERGE (p)-[:MEMBER_OF {rank: $rank, since: $since}]->(o)
    """, {
        "person_id": person_id,
        "org_id": org["id"],
        "rank": rank,
        "since": (start_date + timedelta(days=random.randint(-730, 0))).strftime("%Y-%m-%d")
    })

# Organization-Location relationships (OPERATES_IN) - NEW!
print("  - Linking organizations to territories...")
for org in organizations:
    # Each org operates in 3-5 locations in their territory
    relevant_locations = [l for l in locations if l["district"] == org["territory"] or org["territory"] == "Central"]
    selected_locs = random.sample(relevant_locations, min(random.randint(3, 5), len(relevant_locations)))
    
    for loc in selected_locs:
        db.query("""
            MATCH (o:Organization {id: $org_id})
            MATCH (l:Location {name: $location})
            MERGE (o)-[:OPERATES_IN {activity_level: $level}]->(l)
        """, {
            "org_id": org["id"],
            "location": loc["name"],
            "level": random.choice(["low", "medium", "high"])
        })

# Crime-MO relationships (MATCHES_MO) - NEW!
print("  - Linking crimes to modus operandi...")
for crime_id, crime_type, location_name in crimes[:200]:  # Link 200 crimes to MO patterns
    mo = random.choice(mo_patterns)
    similarity = round(random.uniform(0.7, 0.98), 2)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (m:ModusOperandi {id: $mo_id})
        MERGE (c)-[:MATCHES_MO {similarity: $similarity}]->(m)
    """, {"crime_id": crime_id, "mo_id": mo["id"], "similarity": similarity})

# Crime-Investigator relationships (INVESTIGATED_BY) - NEW!
print("  - Assigning investigators to crimes...")
for crime_id, crime_type, location_name in crimes:
    # Assign investigator based on crime type
    relevant_inv = [inv for inv in investigators if crime_type in inv["specialization"] or random.random() < 0.3]
    if relevant_inv:
        investigator = random.choice(relevant_inv)
    else:
        investigator = random.choice(investigators)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (i:Investigator {id: $inv_id})
        MERGE (c)-[:INVESTIGATED_BY {assigned_date: $date}]->(i)
    """, {
        "crime_id": crime_id,
        "inv_id": investigator["id"],
        "date": (start_date + timedelta(days=random.randint(0, 300))).strftime("%Y-%m-%d")
    })

# Crime-Evidence relationships (HAS_EVIDENCE) - NEW!
print("  - Linking evidence to crimes...")
for crime_id, crime_type, location_name in crimes:
    # Each crime has 1-4 pieces of evidence
    num_evidence = random.randint(1, 4)
    selected_evidence = random.sample(evidence_items, num_evidence)
    
    for evidence_id in selected_evidence:
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (e:Evidence {id: $evidence_id})
            MERGE (c)-[:HAS_EVIDENCE]->(e)
        """, {"crime_id": crime_id, "evidence_id": evidence_id})

# Evidence-Person relationships (LINKS_TO) - NEW!
print("  - Linking evidence to suspects...")
for evidence_id in evidence_items[:60]:  # 60 pieces link to persons
    person_id, person_name = random.choice(persons)
    confidence = round(random.uniform(0.6, 0.99), 2)
    
    db.query("""
        MATCH (e:Evidence {id: $evidence_id})
        MATCH (p:Person {id: $person_id})
        MERGE (e)-[:LINKS_TO {confidence: $confidence}]->(p)
    """, {"evidence_id": evidence_id, "person_id": person_id, "confidence": confidence})

# Crime-Vehicle relationships (INVOLVED_VEHICLE) - NEW!
print("  - Linking vehicles to crimes...")
for _ in range(80):
    crime_id, crime_type, location_name = random.choice(crimes)
    vehicle_id = random.choice(vehicles)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (c)-[:INVOLVED_VEHICLE {role: $role}]->(v)
    """, {
        "crime_id": crime_id,
        "vehicle_id": vehicle_id,
        "role": random.choice(["getaway", "transport", "scene"])
    })

# Person-Vehicle relationships (OWNS) - NEW!
print("  - Linking vehicles to owners...")
for vehicle_id in vehicles:
    person_id, person_name = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (p)-[:OWNS]->(v)
    """, {"person_id": person_id, "vehicle_id": vehicle_id})

# Crime-Weapon relationships (USED_WEAPON) - NEW!
print("  - Linking weapons to crimes...")
for _ in range(50):
    crime_id, crime_type, location_name = random.choice(crimes)
    weapon_id = random.choice(weapons)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (c)-[:USED_WEAPON]->(w)
    """, {"crime_id": crime_id, "weapon_id": weapon_id})

# Person-Weapon relationships (OWNS) - NEW!
print("  - Linking weapons to owners...")
for weapon_id in weapons[:20]:  # 20 weapons have known owners
    person_id, person_name = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (p)-[:OWNS]->(w)
    """, {"person_id": person_id, "weapon_id": weapon_id})

# Person-Person relationships (KNOWS)
print("  - Creating social networks...")
for _ in range(250):
    (p1_id, p1_name), (p2_id, p2_name) = random.sample(persons, 2)
    relationship_type = random.choice(["friend", "acquaintance", "associate", "rival"])
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:KNOWS {relationship: $rel, strength: $strength}]-(p2)
    """, {
        "p1": p1_id,
        "p2": p2_id,
        "rel": relationship_type,
        "strength": round(random.uniform(0.3, 1.0), 2)
    })

# Person-Person relationships (FAMILY_REL)
print("  - Creating family connections...")
for _ in range(90):
    (p1_id, p1_name), (p2_id, p2_name) = random.sample(persons, 2)
    relation = random.choice(["sibling", "parent", "cousin", "spouse"])
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:FAMILY_REL {relation: $relation}]-(p2)
    """, {"p1": p1_id, "p2": p2_id, "relation": relation})

# Crime-Crime relationships (SIMILAR_TO, FOLLOWED_BY) - NEW!
print("  - Creating crime series patterns...")
for _ in range(60):
    (c1_id, c1_type, c1_loc), (c2_id, c2_type, c2_loc) = random.sample(crimes, 2)
    
    # If same type, create similarity
    if c1_type == c2_type:
        similarity = round(random.uniform(0.7, 0.95), 2)
        db.query("""
            MATCH (c1:Crime {id: $c1})
            MATCH (c2:Crime {id: $c2})
            MERGE (c1)-[:SIMILAR_TO {similarity_score: $sim}]->(c2)
        """, {"c1": c1_id, "c2": c2_id, "sim": similarity})

# Person-Location relationships (FREQUENTS) - NEW!
print("  - Tracking location frequencies...")
for person_id, person_name in persons[:60]:  # 60 persons have known frequented locations
    # Each person frequents 2-4 locations
    num_locs = random.randint(2, 4)
    selected_locs = random.sample(locations, num_locs)
    
    for loc in selected_locs:
        frequency = random.randint(5, 30)
        db.query("""
            MATCH (p:Person {id: $person_id})
            MATCH (l:Location {name: $location})
            MERGE (p)-[:FREQUENTS {frequency: $freq}]->(l)
        """, {"person_id": person_id, "location": loc["name"], "freq": frequency})

print("✅ Created rich relationship network")

# ============================================================================
# 11. FINAL STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("📊 FINAL DATABASE STATISTICS")
print("=" * 60)

stats = db.query("""
    MATCH (n)
    WITH labels(n)[0] as label, count(n) as count
    RETURN label, count
    ORDER BY count DESC
""")

for stat in stats:
    print(f"   {stat['label']}: {stat['count']}")

rel_stats = db.query("""
    MATCH ()-[r]->()
    WITH type(r) as rel_type, count(r) as count
    RETURN rel_type, count
    ORDER BY count DESC
""")

print("\n📍 RELATIONSHIP STATISTICS")
print("=" * 60)
for rel in rel_stats:
    print(f"   {rel['rel_type']}: {rel['count']}")

print("\n" + "=" * 60)
print("🎉 ENHANCED DATABASE LOADED SUCCESSFULLY!")
print("=" * 60)
print("✨ Your graph now supports 40+ meaningful questions!")
print("=" * 60)

db.close()