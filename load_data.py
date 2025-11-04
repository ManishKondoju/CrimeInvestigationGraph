# load_synthetic_data.py - Enhanced Realistic Synthetic Crime Dataset
from database import Database
import random
from datetime import datetime, timedelta

db = Database()

print("="*60)
print("🎨 Loading ENHANCED SYNTHETIC Crime Investigation Data")
print("="*60)

# Clear database
db.clear_all()

# ============================================================================
# PART 1: CREATE LOCATIONS (Expanded to 40 realistic Chicago locations)
# ============================================================================

print("\n📍 Step 1: Creating Chicago locations...")

chicago_locations = [
    # Downtown
    {"name": "001XX N STATE ST", "district": "18", "lat": 41.8857, "lon": -87.6278, "area": "Loop"},
    {"name": "100XX S MICHIGAN AVE", "district": "1", "lat": 41.8918, "lon": -87.6244, "area": "Loop"},
    {"name": "300XX S WABASH AVE", "district": "1", "lat": 41.8777, "lon": -87.6264, "area": "Loop"},
    
    # West Side
    {"name": "002XX W CHICAGO AVE", "district": "12", "lat": 41.8966, "lon": -87.6336, "area": "West"},
    {"name": "1500XX W MADISON ST", "district": "11", "lat": 41.8819, "lon": -87.6389, "area": "West"},
    {"name": "2300XX W DIVISION ST", "district": "12", "lat": 41.9032, "lon": -87.6724, "area": "West"},
    {"name": "3100XX W GRAND AVE", "district": "25", "lat": 41.8915, "lon": -87.6751, "area": "West"},
    {"name": "4200XX W NORTH AVE", "district": "14", "lat": 41.9104, "lon": -87.6798, "area": "West"},
    
    # South Side
    {"name": "007XX S HALSTED ST", "district": "12", "lat": 41.8721, "lon": -87.6474, "area": "South"},
    {"name": "1100XX W 63RD ST", "district": "7", "lat": 41.7796, "lon": -87.6590, "area": "South"},
    {"name": "1200XX S STATE ST", "district": "2", "lat": 41.8677, "lon": -87.6270, "area": "South"},
    {"name": "5500XX S STONY ISLAND AVE", "district": "3", "lat": 41.7897, "lon": -87.5859, "area": "South"},
    {"name": "7800XX S COTTAGE GROVE AVE", "district": "6", "lat": 41.7523, "lon": -87.6058, "area": "South"},
    
    # North Side
    {"name": "008XX W BELMONT AVE", "district": "19", "lat": 41.9394, "lon": -87.6531, "area": "North"},
    {"name": "1300XX W FULLERTON AVE", "district": "14", "lat": 41.9247, "lon": -87.6653, "area": "North"},
    {"name": "1700XX N DAMEN AVE", "district": "14", "lat": 41.9125, "lon": -87.6776, "area": "North"},
    {"name": "2400XX N CLARK ST", "district": "18", "lat": 41.9308, "lon": -87.6313, "area": "North"},
    {"name": "3200XX N BROADWAY", "district": "19", "lat": 41.9419, "lon": -87.6453, "area": "North"},
    
    # East Side
    {"name": "009XX N CLARK ST", "district": "18", "lat": 41.9008, "lon": -87.6313, "area": "East"},
    {"name": "1900XX S CICERO AVE", "district": "8", "lat": 41.8575, "lon": -87.7457, "area": "East"},
    
    # Central
    {"name": "006XX W JACKSON BLVD", "district": "1", "lat": 41.8777, "lon": -87.6420, "area": "Central"},
    {"name": "010XX S WESTERN AVE", "district": "9", "lat": 41.8692, "lon": -87.6848, "area": "Central"},
    {"name": "014XX N ASHLAND AVE", "district": "12", "lat": 41.9089, "lon": -87.6688, "area": "Central"}
]

for loc in chicago_locations:
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            district: $district,
            area: $area,
            type: 'street_block',
            source: 'synthetic'
        })
    """, loc)

print(f"✅ Created {len(chicago_locations)} locations")

# ============================================================================
# PART 2: CREATE ORGANIZATIONS (More detailed)
# ============================================================================

print("\n🏢 Step 2: Creating criminal organizations...")

organizations = [
    {"id": "ORG001", "name": "West Side Crew", "type": "street_gang", "territory": "West", "founded": "2018", "rivals": ["ORG002", "ORG003"]},
    {"id": "ORG002", "name": "South Side Syndicate", "type": "organized_crime", "territory": "South", "founded": "2015", "rivals": ["ORG001"]},
    {"id": "ORG003", "name": "North River Gang", "type": "street_gang", "territory": "North", "founded": "2019", "rivals": ["ORG001", "ORG004"]},
    {"id": "ORG004", "name": "Downtown Dealers", "type": "drug_trafficking", "territory": "Central", "founded": "2016", "rivals": ["ORG003"]},
    {"id": "ORG005", "name": "East Side Burglars", "type": "burglary_ring", "territory": "East", "founded": "2020", "rivals": []},
    {"id": "ORG006", "name": "Loop Hustlers", "type": "theft_ring", "territory": "Loop", "founded": "2017", "rivals": []},
]

for org in organizations:
    db.query("""
        CREATE (o:Organization {
            id: $id,
            name: $name,
            type: $type,
            territory: $territory,
            founded_year: $founded,
            members_count: $members,
            activity_level: $activity,
            threat_level: $threat,
            source: 'synthetic'
        })
    """, {
        **org,
        "members": random.randint(12, 35),
        "activity": random.choice(['low', 'medium', 'high', 'very high']),
        "threat": random.choice(['low', 'medium', 'high', 'critical'])
    })

print(f"✅ Created {len(organizations)} organizations")

# ============================================================================
# PART 3: CREATE INVESTIGATORS (More specialized)
# ============================================================================

print("\n👮 Step 3: Creating investigators...")

investigators = [
    {"id": "INV001", "name": "Det. Sarah Johnson", "badge": "DET-5542", "dept": "Homicide", "specialty": "Serial Crimes", "years": 12},
    {"id": "INV002", "name": "Det. Michael Brown", "badge": "DET-6734", "dept": "Robbery", "specialty": "Armed Robbery", "years": 8},
    {"id": "INV003", "name": "Det. Lisa Garcia", "badge": "DET-4421", "dept": "Narcotics", "specialty": "Drug Trafficking", "years": 15},
    {"id": "INV004", "name": "Det. Robert Chen", "badge": "DET-7891", "dept": "Burglary", "specialty": "Property Crimes", "years": 6},
    {"id": "INV005", "name": "Det. Emily Rodriguez", "badge": "DET-3312", "dept": "Assault", "specialty": "Gang Violence", "years": 10},
    {"id": "INV006", "name": "Det. James Wilson", "badge": "DET-4455", "dept": "Organized Crime", "specialty": "RICO Cases", "years": 14},
    {"id": "INV007", "name": "Det. Amanda Martinez", "badge": "DET-6677", "dept": "Cyber Crimes", "specialty": "Digital Forensics", "years": 5},
]

for inv in investigators:
    db.query("""
        CREATE (i:Investigator {
            id: $id, name: $name, badge_number: $badge,
            department: $dept, specialization: $specialty,
            years_experience: $years,
            cases_solved: $solved, active_cases: $active,
            success_rate: $rate,
            source: 'synthetic'
        })
    """, {
        **inv,
        "solved": random.randint(25, 85),
        "active": random.randint(3, 18),
        "rate": round(random.uniform(0.65, 0.92), 2)
    })

print(f"✅ Created {len(investigators)} investigators")

# ============================================================================
# PART 4: CREATE MODUS OPERANDI PATTERNS (More detailed)
# ============================================================================

print("\n🎭 Step 4: Creating modus operandi patterns...")

mo_patterns = [
    {"id": "MO001", "desc": "Breaking through rear windows at night", "sig": "leaves door unlocked", "type": "Burglary"},
    {"id": "MO002", "desc": "Armed robbery with getaway vehicle", "sig": "uses stolen cars", "type": "Robbery"},
    {"id": "MO003", "desc": "Distraction theft in crowded areas", "sig": "works in pairs", "type": "Theft"},
    {"id": "MO004", "desc": "Late night street assault", "sig": "targets lone victims", "type": "Assault"},
    {"id": "MO005", "desc": "Drug dealing in parks", "sig": "uses lookouts", "type": "Narcotics"},
    {"id": "MO006", "desc": "Smash and grab vehicle theft", "sig": "breaks driver window", "type": "Vehicle Theft"},
    {"id": "MO007", "desc": "Home invasion during daytime", "sig": "poses as delivery person", "type": "Burglary"},
]

for mo in mo_patterns:
    db.query("""
        CREATE (m:ModusOperandi {
            id: $id,
            description: $desc,
            signature_element: $sig,
            crime_type: $type,
            frequency: $freq,
            confidence_score: $conf,
            source: 'synthetic'
        })
    """, {**mo, "freq": random.randint(5, 25), "conf": round(random.uniform(0.70, 0.95), 2)})

print(f"✅ Created {len(mo_patterns)} MO patterns")

# ============================================================================
# PART 5: CREATE PERSONS (More realistic profiles)
# ============================================================================

print("\n👥 Step 5: Creating persons...")

first_names = ["Marcus", "David", "Carlos", "James", "Robert", "Lisa", "Sarah", "Maria", "John", "Michael",
               "Emily", "Jennifer", "Daniel", "Jessica", "Anthony", "Amanda", "Christopher", "Michelle",
               "Matthew", "Ashley", "Joshua", "Stephanie", "Andrew", "Nicole", "Ryan", "Elizabeth"]
               
last_names = ["Rivera", "Lee", "Martinez", "Wilson", "Johnson", "Chen", "Garcia", "Rodriguez", "Smith", "Brown",
              "Williams", "Davis", "Miller", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
              "Martin", "Thompson", "Clark", "Lewis", "Walker", "Hall"]

persons = []
for i in range(120):  # Increased to 120 persons
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
            phone: $phone,
            alias: $alias,
            source: 'synthetic'
        })
    """, {
        "id": person_id,
        "name": name,
        "age": random.randint(18, 65),
        "gender": random.choice(['Male', 'Female']),
        "occupation": random.choice(['Unemployed', 'Mechanic', 'Cook', 'Driver', 'Cashier', 'Retail', 'Construction', 
                                    'Warehouse', 'Security', 'Bartender', 'Cleaner', 'Laborer']),
        "record": random.choice([True, True, False]),
        "risk": round(random.uniform(0.1, 0.95), 2),
        "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Main', 'State', 'Park', 'Lake', 'Elm', 'Pine', 'Maple'])} St",
        "phone": f"312-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "alias": random.choice([None, None, f"{random.choice(['Big', 'Lil', 'Slim', 'Ghost'])}{random.choice(['Mike', 'D', 'Jay', 'K'])}"])
    })
    
    persons.append((person_id, name))

print(f"✅ Created {len(persons)} persons")

# ============================================================================
# PART 6: CREATE CRIMES (More variety and realism)
# ============================================================================

print("\n🚨 Step 6: Creating crimes...")

crime_types_detailed = [
    ("THEFT", ["From Building", "Retail", "From Vehicle", "Pickpocket"]),
    ("BATTERY", ["Simple", "Aggravated", "Domestic"]),
    ("CRIMINAL DAMAGE", ["Vandalism", "Graffiti", "Property Damage"]),
    ("ASSAULT", ["Simple", "Aggravated", "With Weapon"]),
    ("BURGLARY", ["Residential", "Commercial", "Vehicle"]),
    ("ROBBERY", ["Armed", "Strong-arm", "Vehicular Hijacking"]),
    ("NARCOTICS", ["Possession", "Distribution", "Manufacturing"]),
    ("MOTOR VEHICLE THEFT", ["Auto Theft", "Motorcycle Theft", "Carjacking"]),
    ("WEAPONS VIOLATION", ["Unlawful Use", "Unlawful Possession", "Armed Violence"]),
    ("CRIMINAL TRESPASS", ["Residential", "Commercial", "Land"]),
]

crimes_created = 0
crime_ids = []

# Generate crimes over the past year
start_date = datetime.now() - timedelta(days=365)

for i in range(750):  # Increased to 750 crimes
    crime_id = f"C{i:04d}"
    
    # Random date within last year
    crime_date = start_date + timedelta(days=random.randint(0, 365))
    
    # Realistic time distribution (more crimes at night)
    hour_weights = [1,1,1,1,2,2,3,4,5,5,4,4,3,3,3,4,5,6,8,10,9,7,5,3]  # Night = higher
    crime_hour = random.choices(range(24), weights=hour_weights)[0]
    crime_time = f"{crime_hour:02d}:{random.randint(0, 59):02d}"
    
    # Select crime type
    crime_main, crime_subs = random.choice(crime_types_detailed)
    crime_sub = random.choice(crime_subs)
    
    db.query("""
        CREATE (c:Crime {
            id: $id,
            type: $type,
            subtype: $subtype,
            date: $date,
            time: $time,
            case_number: $case_number,
            description: $description,
            arrest_made: $arrest,
            severity: $severity,
            status: $status,
            cleared: $cleared,
            source: 'synthetic'
        })
    """, {
        "id": crime_id,
        "type": crime_main,
        "subtype": crime_sub,
        "date": crime_date.strftime('%Y-%m-%d'),
        "time": crime_time,
        "case_number": f"JC{200000 + i}",
        "description": f"{crime_sub} - {random.choice(['In Progress', 'Completed', 'Attempted'])}",
        "arrest": random.choice([True, False, False, False, False]),
        "severity": random.choice(['minor', 'minor', 'moderate', 'moderate', 'severe']),
        "status": random.choice(['investigating', 'investigating', 'investigating', 'solved', 'cold']),
        "cleared": random.choice([True, False, False, False])
    })
    
    crime_ids.append(crime_id)
    crimes_created += 1

print(f"✅ Created {crimes_created} crimes")

# ============================================================================
# PART 7: CREATE EVIDENCE (More realistic types)
# ============================================================================

print("\n🔍 Step 7: Creating evidence items...")

evidence_ids = []
evidence_types_detailed = {
    'physical': ['DNA sample', 'Fingerprint', 'Blood spatter', 'Fiber sample', 'Hair sample', 'Shoe print', 'Tool marks'],
    'digital': ['CCTV footage', 'Phone records', 'Social media', 'GPS data', 'Email records', 'Text messages'],
    'forensic': ['Ballistics report', 'Toxicology report', 'Autopsy report', 'Handwriting analysis'],
    'testimonial': ['Witness statement', 'Victim statement', 'Confession', 'Expert testimony']
}

for i in range(200):  # Increased to 200 evidence items
    evidence_id = f"E{i:03d}"
    ev_type = random.choice(list(evidence_types_detailed.keys()))
    ev_desc = random.choice(evidence_types_detailed[ev_type])
    
    db.query("""
        CREATE (e:Evidence {
            id: $id,
            type: $type,
            description: $description,
            verified: $verified,
            significance: $significance,
            collection_date: $date,
            chain_of_custody: $custody,
            source: 'synthetic'
        })
    """, {
        "id": evidence_id,
        "type": ev_type,
        "description": ev_desc,
        "verified": random.choice([True, True, True, False]),
        "significance": random.choice(['low', 'low', 'medium', 'medium', 'high', 'critical']),
        "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
        "custody": random.choice(['maintained', 'maintained', 'maintained', 'questioned'])
    })
    
    evidence_ids.append(evidence_id)

print(f"✅ Created {len(evidence_ids)} evidence items")

# ============================================================================
# PART 8: CREATE WEAPONS (More variety)
# ============================================================================

print("\n🔫 Step 8: Creating weapons...")

weapon_types_detailed = [
    ("firearm", "Glock", "19", "9mm"),
    ("firearm", "Glock", "17", "9mm"),
    ("firearm", "Smith & Wesson", "M&P", ".40"),
    ("firearm", "Sig Sauer", "P226", "9mm"),
    ("firearm", "Beretta", "92FS", "9mm"),
    ("firearm", "Colt", "1911", ".45"),
    ("rifle", "AR", "15", "5.56mm"),
    ("shotgun", "Mossberg", "500", "12ga"),
    ("knife", "Buck", "119", "Fixed Blade"),
    ("knife", "Ka-Bar", "USMC", "Fixed Blade"),
    ("other", "Baseball", "Bat", "Blunt"),
    ("other", "Tire", "Iron", "Blunt"),
]

weapons = []

for i in range(45):  # Increased to 45 weapons
    weapon_id = f"W{i:03d}"
    wtype, make, model, caliber = random.choice(weapon_types_detailed)
    
    db.query("""
        CREATE (w:Weapon {
            id: $id, type: $type, make: $make, model: $model,
            caliber: $caliber,
            serial_number: $serial, 
            recovered: $recovered,
            registered: $registered,
            source: 'synthetic'
        })
    """, {
        "id": weapon_id, "type": wtype, "make": make, "model": model,
        "caliber": caliber,
        "serial": f"{make[:3].upper()}{random.randint(100000, 999999)}",
        "recovered": random.choice([True, True, False, False]),
        "registered": random.choice([True, False, False, False])
    })
    weapons.append(weapon_id)

print(f"✅ Created {len(weapons)} weapons")

# ============================================================================
# PART 9: CREATE VEHICLES (More variety)
# ============================================================================

print("\n🚗 Step 9: Creating vehicles...")

vehicles = []
vehicle_makes_detailed = [
    ('Toyota', 'Camry'), ('Toyota', 'Corolla'), ('Toyota', 'RAV4'),
    ('Honda', 'Civic'), ('Honda', 'Accord'), ('Honda', 'CR-V'),
    ('Ford', 'F-150'), ('Ford', 'Explorer'), ('Ford', 'Escape'),
    ('Chevrolet', 'Malibu'), ('Chevrolet', 'Silverado'), ('Chevrolet', 'Equinox'),
    ('Nissan', 'Altima'), ('Nissan', 'Maxima'), ('Nissan', 'Rogue'),
    ('BMW', '3 Series'), ('Mercedes', 'C-Class'), ('Audi', 'A4')
]

for i in range(80):  # Increased to 80 vehicles
    vehicle_id = f"V{i:03d}"
    make, model = random.choice(vehicle_makes_detailed)
    
    db.query("""
        CREATE (v:Vehicle {
            id: $id, make: $make, model: $model, year: $year,
            color: $color, license_plate: $plate,
            vin: $vin,
            reported_stolen: $stolen, 
            registered_owner: $registered,
            source: 'synthetic'
        })
    """, {
        "id": vehicle_id,
        "make": make,
        "model": model,
        "year": random.randint(2005, 2024),
        "color": random.choice(['Black', 'White', 'Silver', 'Gray', 'Blue', 'Red', 'Green', 'Brown']),
        "plate": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}{random.randint(1000, 9999)}",
        "vin": f"1{''.join(random.choices('ABCDEFGHJKLMNPRSTUVWXYZ0123456789', k=16))}",
        "stolen": random.choice([True, False, False, False, False]),
        "registered": random.choice([True, True, True, False])
    })
    vehicles.append(vehicle_id)

print(f"✅ Created {len(vehicles)} vehicles")

# ============================================================================
# PART 10: CREATE RELATIONSHIPS (More realistic patterns)
# ============================================================================

print("\n🔗 Step 10: Creating relationships...")

# Link crimes to locations (every crime has a location)
print("  📍 Linking crimes to locations...")
for crime_id in crime_ids:
    location = random.choice(chicago_locations)
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (l:Location {name: $location})
        MERGE (c)-[:OCCURRED_AT]->(l)
    """, {"crime_id": crime_id, "location": location['name']})

# Link persons to crimes (realistic distribution)
print("  👥 Linking persons to crimes...")
for person_id, person_name in persons:
    # Some are repeat offenders (many crimes), some are one-time (1-2 crimes)
    if random.random() < 0.2:  # 20% are repeat offenders
        num_crimes = random.randint(5, 12)
    else:
        num_crimes = random.randint(1, 4)
    
    selected_crimes = random.sample(crime_ids, min(num_crimes, len(crime_ids)))
    
    for crime_id in selected_crimes:
        db.query("""
            MATCH (p:Person {id: $person_id})
            MATCH (c:Crime {id: $crime_id})
            MERGE (p)-[:PARTY_TO {role: $role, arrested: $arrested}]->(c)
        """, {
            "person_id": person_id,
            "crime_id": crime_id,
            "role": random.choice(['suspect', 'suspect', 'suspect', 'witness', 'accomplice', 'victim']),
            "arrested": random.choice([True, False, False, False])
        })

# Link persons to organizations (60 gang members)
print("  🏢 Creating gang memberships...")
for _ in range(60):  # Increased gang membership
    person_id, _ = random.choice(persons)
    org = random.choice(organizations)
    
    # Don't use None/null in relationship properties
    recruiter = random.choice(['Leader', 'Lieutenant', 'Member', 'Self-recruited'])
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (o:Organization {id: $org_id})
        MERGE (p)-[:MEMBER_OF {
            rank: $rank, 
            since: $since,
            active: $active,
            recruited_by: $recruiter
        }]->(o)
    """, {
        "person_id": person_id,
        "org_id": org['id'],
        "rank": random.choice(['member', 'member', 'member', 'lieutenant', 'enforcer', 'lieutenant', 'leader']),
        "since": f"20{random.randint(15, 24)}-{random.randint(1, 12):02d}-01",
        "active": random.choice([True, True, False]),
        "recruiter": recruiter
    })

# Link crimes to investigators (every crime assigned)
print("  👮 Assigning investigators to crimes...")
for crime_id in crime_ids:
    investigator = random.choice(investigators)
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (i:Investigator {id: $inv_id})
        MERGE (c)-[:INVESTIGATED_BY {
            assigned_date: $date,
            priority: $priority,
            status: $status
        }]->(i)
    """, {
        "crime_id": crime_id,
        "inv_id": investigator['id'],
        "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
        "priority": random.choice(['low', 'medium', 'high', 'critical']),
        "status": random.choice(['active', 'active', 'pending', 'closed'])
    })

# Link crimes to MO patterns
print("  🎭 Matching crimes to MO patterns...")
for crime_id in random.sample(crime_ids, 400):  # More MO matches
    mo = random.choice(mo_patterns)
    analyst_note = random.choice(['High confidence', 'Needs review', 'Confirmed', 'Under analysis'])
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (m:ModusOperandi {id: $mo_id})
        MERGE (c)-[:MATCHES_MO {similarity: $similarity, analyst_notes: $notes}]->(m)
    """, {
        "crime_id": crime_id,
        "mo_id": mo['id'],
        "similarity": round(random.uniform(0.65, 0.98), 2),
        "notes": analyst_note
    })

# Link crimes to evidence (1-5 pieces per crime)
print("  🔍 Linking evidence to crimes...")
for crime_id in crime_ids:
    num_evidence = random.randint(1, 5)
    selected_evidence = random.sample(evidence_ids, min(num_evidence, len(evidence_ids)))
    
    for evidence_id in selected_evidence:
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (e:Evidence {id: $evidence_id})
            MERGE (c)-[:HAS_EVIDENCE {
                collected_by: $collector,
                relevance: $relevance
            }]->(e)
        """, {
            "crime_id": crime_id,
            "evidence_id": evidence_id,
            "collector": random.choice(['CSI Unit', 'Detective', 'Patrol Officer']),
            "relevance": random.choice(['primary', 'secondary', 'supporting'])
        })

# Link evidence to persons (forensic matches)
print("  🔗 Creating evidence-person links...")
for evidence_id in random.sample(evidence_ids, 120):  # More evidence links
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (e:Evidence {id: $evidence_id})
        MATCH (p:Person {id: $person_id})
        MERGE (e)-[:LINKS_TO {
            confidence: $confidence,
            match_type: $match_type,
            verified_by: $verifier
        }]->(p)
    """, {
        "evidence_id": evidence_id,
        "person_id": person_id,
        "confidence": round(random.uniform(0.55, 0.99), 2),
        "match_type": random.choice(['DNA', 'Fingerprint', 'Visual ID', 'Digital', 'Testimony']),
        "verifier": random.choice(['Lab Tech', 'Forensic Expert', 'Detective'])
    })

# Link crimes to vehicles (60-80 connections)
print("  🚗 Linking vehicles to crimes...")
for _ in range(80):
    crime_id = random.choice(crime_ids)
    vehicle_id = random.choice(vehicles)
    location_found = random.choice(['At scene', 'Nearby', 'Different location', 'Not recovered'])
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (c)-[:INVOLVED_VEHICLE {
            role: $role,
            location_found: $found
        }]->(v)
    """, {
        "crime_id": crime_id,
        "vehicle_id": vehicle_id,
        "role": random.choice(['getaway', 'transport', 'scene', 'stolen', 'abandoned']),
        "found": location_found
    })

# Link persons to vehicles (ownership)
print("  🚗 Linking persons to vehicles...")
for vehicle_id in vehicles:
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (v:Vehicle {id: $vehicle_id})
        MERGE (p)-[:OWNS {
            since: $since,
            registration_status: $status
        }]->(v)
    """, {
        "person_id": person_id,
        "vehicle_id": vehicle_id,
        "since": f"20{random.randint(15, 24)}-01-01",
        "status": random.choice(['current', 'current', 'expired', 'suspended'])
    })

# Link crimes to weapons
print("  🔫 Linking weapons to crimes...")
for _ in range(55):  # More weapon-crime links
    crime_id = random.choice(crime_ids)
    weapon_id = random.choice(weapons)
    fired_status = random.choice(['Yes', 'No', 'Unknown'])
    
    db.query("""
        MATCH (c:Crime {id: $crime_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (c)-[:USED_WEAPON {
            recovered_at_scene: $recovered,
            fired: $fired
        }]->(w)
    """, {
        "crime_id": crime_id,
        "weapon_id": weapon_id,
        "recovered": random.choice([True, False, False]),
        "fired": fired_status
    })

# Link persons to weapons (ownership)
print("  🔫 Linking persons to weapons...")
for weapon_id in weapons[:30]:
    person_id, _ = random.choice(persons)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (w:Weapon {id: $weapon_id})
        MERGE (p)-[:OWNS {
            legally_owned: $legal,
            permit_status: $permit
        }]->(w)
    """, {
        "person_id": person_id,
        "weapon_id": weapon_id,
        "legal": random.choice([True, False, False, False]),
        "permit": random.choice(['valid', 'expired', 'none', 'revoked'])
    })

# Create social connections (more realistic network)
print("  👥 Creating social networks...")
for _ in range(250):  # Increased social connections
    (p1_id, _), (p2_id, _) = random.sample(persons, 2)
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:KNOWS {
            relationship: $rel, 
            strength: $strength,
            since: $since,
            verified: $verified
        }]-(p2)
    """, {
        "p1": p1_id,
        "p2": p2_id,
        "rel": random.choice(['friend', 'associate', 'acquaintance', 'coworker', 'neighbor']),
        "strength": round(random.uniform(0.2, 1.0), 2),
        "since": f"20{random.randint(10, 24)}",
        "verified": random.choice([True, True, False])
    })

# Create family connections
print("  👨‍👩‍👧‍👦 Creating family relationships...")
for _ in range(60):  # More family connections
    (p1_id, _), (p2_id, _) = random.sample(persons, 2)
    
    db.query("""
        MATCH (p1:Person {id: $p1})
        MATCH (p2:Person {id: $p2})
        MERGE (p1)-[:FAMILY_REL {
            relation: $relation,
            verified: $verified
        }]-(p2)
    """, {
        "p1": p1_id,
        "p2": p2_id,
        "relation": random.choice(['sibling', 'parent', 'child', 'cousin', 'spouse', 'uncle', 'aunt']),
        "verified": random.choice([True, True, False])
    })

print("  ✅ All relationships created")

# ============================================================================
# FINAL STATISTICS
# ============================================================================

print("\n" + "="*60)
print("📊 FINAL DATABASE STATISTICS")
print("="*60)

stats = db.query("""
    MATCH (n)
    RETURN labels(n)[0] as NodeType, count(n) as Count
    ORDER BY Count DESC
""")

print("\n🔵 Nodes by Type:")
for stat in stats:
    print(f"   {stat['NodeType']}: {stat['Count']}")

rel_stats = db.query("""
    MATCH ()-[r]->()
    RETURN type(r) as RelType, count(r) as Count
    ORDER BY Count DESC
""")

print("\n🔗 Relationships:")
for stat in rel_stats:
    print(f"   {stat['RelType']}: {stat['Count']}")

total_nodes = sum(s['Count'] for s in stats)
total_rels = sum(s['Count'] for s in rel_stats)

print("\n" + "="*60)
print("🎉 ENHANCED SYNTHETIC DATA LOADED SUCCESSFULLY!")
print("="*60)
print(f"\n📊 Total Nodes: {total_nodes}")
print(f"🔗 Total Relationships: {total_rels}")
print("\n✨ Features:")
print("   ✓ 750 crimes with realistic patterns")
print("   ✓ 120 persons with detailed profiles")
print("   ✓ 200 evidence items (physical, digital, forensic)")
print("   ✓ 45 weapons with serial numbers")
print("   ✓ 80 vehicles with VINs")
print("   ✓ Rich relationship metadata")
print("   ✓ Realistic crime distribution over 1 year")
print("="*60)

db.close()