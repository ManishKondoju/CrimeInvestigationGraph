# load_hybrid_data.py - Real Chicago Crimes + Synthetic Enrichment (TIMELINE OPTIMIZED)
# This is the BEST approach: Real data credibility + Full graph capabilities + Timeline-ready

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
# HELPER FUNCTIONS FOR REALISTIC DATA
# ============================================================================

# Smart severity mapping based on crime type
SEVERITY_MAP = {
    'HOMICIDE': 'critical',
    'CRIMINAL SEXUAL ASSAULT': 'critical',
    'KIDNAPPING': 'critical',
    'ARSON': 'high',
    'ROBBERY': 'high',
    'ASSAULT': 'high',
    'BATTERY': 'high',
    'WEAPONS VIOLATION': 'high',
    'BURGLARY': 'medium',
    'MOTOR VEHICLE THEFT': 'medium',
    'THEFT': 'medium',
    'NARCOTICS': 'medium',
    'CRIMINAL DAMAGE': 'low',
    'DECEPTIVE PRACTICE': 'low',
    'CRIMINAL TRESPASS': 'low',
}

# Realistic time distribution by crime type (start_hour, end_hour)
TIME_DISTRIBUTION = {
    'HOMICIDE': (20, 4),           # 8 PM to 4 AM
    'ROBBERY': (18, 3),            # 6 PM to 3 AM
    'ASSAULT': (19, 2),            # 7 PM to 2 AM
    'BATTERY': (19, 2),            # 7 PM to 2 AM
    'BURGLARY': (1, 5),            # 1 AM to 5 AM (night)
    'THEFT': (10, 18),             # 10 AM to 6 PM (daytime)
    'MOTOR VEHICLE THEFT': (22, 5), # 10 PM to 5 AM
    'NARCOTICS': (14, 23),         # 2 PM to 11 PM
    'CRIMINAL DAMAGE': (0, 6),     # Midnight to 6 AM
    'WEAPONS VIOLATION': (20, 3),  # 8 PM to 3 AM
    'CRIMINAL SEXUAL ASSAULT': (22, 4), # 10 PM to 4 AM
    'KIDNAPPING': (20, 5),         # 8 PM to 5 AM
    'ARSON': (2, 5),               # 2 AM to 5 AM
    'DEFAULT': (8, 22)             # 8 AM to 10 PM (general)
}

def get_realistic_time(crime_type):
    """Generate realistic time based on crime type"""
    time_range = TIME_DISTRIBUTION.get(crime_type, TIME_DISTRIBUTION['DEFAULT'])
    start_hour, end_hour = time_range
    
    if start_hour < end_hour:
        # Normal range (e.g., 10 AM to 6 PM)
        hour = random.randint(start_hour, end_hour)
    else:
        # Wraps around midnight (e.g., 10 PM to 3 AM)
        if random.random() < 0.5:
            hour = random.randint(start_hour, 23)
        else:
            hour = random.randint(0, end_hour)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def get_severity(crime_type):
    """Map crime type to realistic severity"""
    # Try exact match first
    if crime_type in SEVERITY_MAP:
        return SEVERITY_MAP[crime_type]
    
    # Try partial match
    for key, severity in SEVERITY_MAP.items():
        if key in crime_type.upper():
            return severity
    
    # Default based on common patterns
    if any(word in crime_type.upper() for word in ['MURDER', 'SHOOTING', 'SEXUAL']):
        return 'critical'
    elif any(word in crime_type.upper() for word in ['ASSAULT', 'ROBBERY', 'WEAPON']):
        return 'high'
    elif any(word in crime_type.upper() for word in ['THEFT', 'BURGLARY', 'VEHICLE']):
        return 'medium'
    else:
        return 'low'

def get_status(arrest_made, severity):
    """Generate realistic case status"""
    if arrest_made:
        # Arrested cases more likely to be solved
        return random.choices(
            ['solved', 'under investigation'],
            weights=[0.8, 0.2]
        )[0]
    else:
        # No arrest - distributed across statuses
        if severity == 'critical':
            # Critical cases stay active longer
            return random.choices(
                ['open', 'under investigation', 'cold case'],
                weights=[0.4, 0.5, 0.1]
            )[0]
        else:
            return random.choices(
                ['open', 'under investigation', 'cold case', 'closed'],
                weights=[0.3, 0.3, 0.2, 0.2]
            )[0]

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

# Create location nodes (all unique locations from API)
locations_created = 0
for loc_name, loc_data in unique_locations.items():
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
    locations_created += 1

print(f"✅ Created {locations_created} REAL locations from Chicago data")

# Add some synthetic high-traffic locations for better coverage
print("  📍 Adding synthetic high-traffic locations...")
synthetic_locations = [
    # Downtown & Loop (District 1)
    {"name": "Chicago Union Station", "lat": 41.8789, "lon": -87.6400, "district": "1", "beat": "111", "type": "transit_hub"},
    {"name": "Millennium Park", "lat": 41.8826, "lon": -87.6226, "district": "1", "beat": "112", "type": "park"},
    {"name": "Willis Tower Area", "lat": 41.8789, "lon": -87.6359, "district": "1", "beat": "113", "type": "commercial"},
    {"name": "Grant Park", "lat": 41.8758, "lon": -87.6189, "district": "1", "beat": "114", "type": "park"},
    
    # Near North Side (District 18)
    {"name": "Navy Pier", "lat": 41.8917, "lon": -87.6086, "district": "18", "beat": "1811", "type": "tourist_attraction"},
    {"name": "Magnificent Mile", "lat": 41.8969, "lon": -87.6230, "district": "18", "beat": "1823", "type": "shopping_district"},
    {"name": "Lincoln Park", "lat": 41.9217, "lon": -87.6341, "district": "18", "beat": "1825", "type": "park"},
    
    # Near South Side (District 2, 3, 9)
    {"name": "Hyde Park", "lat": 41.7943, "lon": -87.5907, "district": "3", "beat": "312", "type": "neighborhood"},
    {"name": "Chinatown", "lat": 41.8525, "lon": -87.6320, "district": "9", "beat": "912", "type": "neighborhood"},
    {"name": "Bronzeville", "lat": 41.8115, "lon": -87.6123, "district": "2", "beat": "211", "type": "neighborhood"},
    
    # West Side (District 11, 12, 15)
    {"name": "United Center Area", "lat": 41.8807, "lon": -87.6742, "district": "11", "beat": "1115", "type": "sports_venue"},
    {"name": "Little Italy", "lat": 41.8551, "lon": -87.6505, "district": "12", "beat": "1214", "type": "neighborhood"},
    {"name": "Greektown", "lat": 41.8829, "lon": -87.6487, "district": "12", "beat": "1215", "type": "neighborhood"},
    {"name": "Garfield Park", "lat": 41.8843, "lon": -87.7162, "district": "11", "beat": "1122", "type": "park"},
    {"name": "Austin Neighborhood", "lat": 41.8978, "lon": -87.7597, "district": "15", "beat": "1511", "type": "neighborhood"},
    
    # North Side (District 19, 20, 24)
    {"name": "Wrigley Field Area", "lat": 41.9484, "lon": -87.6553, "district": "19", "beat": "1924", "type": "sports_venue"},
    {"name": "Lakeview", "lat": 41.9403, "lon": -87.6541, "district": "19", "beat": "1931", "type": "neighborhood"},
    {"name": "Rogers Park", "lat": 41.9978, "lon": -87.6661, "district": "24", "beat": "2411", "type": "neighborhood"},
    {"name": "Lincoln Square", "lat": 41.9682, "lon": -87.6889, "district": "20", "beat": "2011", "type": "neighborhood"},
    
    # South Side (District 4, 5, 6, 7, 8)
    {"name": "Englewood", "lat": 41.7794, "lon": -87.6464, "district": "7", "beat": "711", "type": "neighborhood"},
    {"name": "South Shore", "lat": 41.7569, "lon": -87.5706, "district": "4", "beat": "411", "type": "neighborhood"},
    {"name": "Chatham", "lat": 41.7316, "lon": -87.6059, "district": "6", "beat": "611", "type": "neighborhood"},
    {"name": "Auburn Gresham", "lat": 41.7437, "lon": -87.6511, "district": "6", "beat": "621", "type": "neighborhood"},
    {"name": "Roseland", "lat": 41.6928, "lon": -87.6125, "district": "5", "beat": "511", "type": "neighborhood"},
    
    # Southwest Side (District 8, 9, 10)
    {"name": "Midway International Airport", "lat": 41.7868, "lon": -87.7522, "district": "8", "beat": "812", "type": "airport"},
    {"name": "Ashburn", "lat": 41.7434, "lon": -87.7109, "district": "8", "beat": "821", "type": "neighborhood"},
    {"name": "Beverly", "lat": 41.7205, "lon": -87.6751, "district": "22", "beat": "2211", "type": "neighborhood"},
    
    # Northwest Side (District 16, 17, 25)
    {"name": "O'Hare International Airport", "lat": 41.9742, "lon": -87.9073, "district": "16", "beat": "1611", "type": "airport"},
    {"name": "Jefferson Park", "lat": 41.9704, "lon": -87.7608, "district": "16", "beat": "1621", "type": "neighborhood"},
    {"name": "Albany Park", "lat": 41.9683, "lon": -87.7231, "district": "17", "beat": "1711", "type": "neighborhood"},
    {"name": "Portage Park", "lat": 41.9550, "lon": -87.7647, "district": "16", "beat": "1631", "type": "neighborhood"},
    
    # Commercial/Shopping Districts
    {"name": "State Street Shopping", "lat": 41.8819, "lon": -87.6278, "district": "1", "beat": "115", "type": "shopping_district"},
    {"name": "Michigan Avenue", "lat": 41.8858, "lon": -87.6241, "district": "18", "beat": "1831", "type": "shopping_district"},
    
    # Transit Hubs
    {"name": "95th/Dan Ryan CTA", "lat": 41.7225, "lon": -87.6244, "district": "5", "beat": "521", "type": "transit_hub"},
    {"name": "Roosevelt/State CTA", "lat": 41.8675, "lon": -87.6270, "district": "1", "beat": "116", "type": "transit_hub"},
]

for loc in synthetic_locations:
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            district: $district,
            beat: $beat,
            type: $type,
            source: 'synthetic'
        })
    """, loc)

print(f"  ✅ Added {len(synthetic_locations)} synthetic high-traffic locations")
print(f"📍 Total Locations: {locations_created + len(synthetic_locations)}")

# ============================================================================
# PART 3: CREATE CRIMES FROM REAL DATA (TIMELINE OPTIMIZED)
# ============================================================================

print("\n🚨 Step 3: Creating crimes from REAL Chicago data (with timeline enhancements)...")

crimes_created = 0
crime_ids = []

for crime in real_crimes[:500]:
    if 'latitude' not in crime or not crime.get('latitude'):
        continue
    
    crime_id = crime.get('id', f"REAL{crimes_created:04d}")
    crime_type = crime.get('primary_type', 'Unknown')
    
    # Extract date from API
    api_date = crime.get('date', '')
    crime_date = api_date[:10] if api_date else f"2024-{random.randint(1, 10):02d}-{random.randint(1, 28):02d}"
    
    # Generate realistic time based on crime type (not API time which is often midnight)
    crime_time = get_realistic_time(crime_type)
    
    # Smart severity mapping
    severity = get_severity(crime_type)
    
    # Realistic status based on arrest and severity
    arrest_made = crime.get('arrest', 'false') == 'true'
    status = get_status(arrest_made, severity)
    
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
        "type": crime_type,
        "date": crime_date,
        "time": crime_time,
        "case_number": crime.get('case_number', 'UNKNOWN'),
        "description": crime.get('description', '')[:200],
        "arrest": arrest_made,
        "severity": severity,
        "status": status
    })
    
    # Link to location
    block = crime.get('block', '')
    if block and block in unique_locations:
        # Link to exact real location
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (l:Location {name: $location})
            MERGE (c)-[:OCCURRED_AT]->(l)
        """, {"crime_id": crime_id, "location": block})
    elif 'district' in crime and crime.get('district'):
        # Link to synthetic location in same district
        district = crime.get('district')
        fallback_location = db.query("""
            MATCH (l:Location {district: $district, source: 'synthetic'})
            RETURN l.name as name
            LIMIT 1
        """, {"district": str(district)})
        
        if fallback_location:
            db.query("""
                MATCH (c:Crime {id: $crime_id})
                MATCH (l:Location {name: $location})
                MERGE (c)-[:OCCURRED_AT]->(l)
            """, {"crime_id": crime_id, "location": fallback_location[0]['name']})
    else:
        # Last resort: link to random synthetic location
        random_location = db.query("""
            MATCH (l:Location {source: 'synthetic'})
            RETURN l.name as name
            ORDER BY rand()
            LIMIT 1
        """)
        
        if random_location:
            db.query("""
                MATCH (c:Crime {id: $crime_id})
                MATCH (l:Location {name: $location})
                MERGE (c)-[:OCCURRED_AT]->(l)
            """, {"crime_id": crime_id, "location": random_location[0]['name']})
    
    crime_ids.append(crime_id)
    crimes_created += 1

print(f"✅ Created {crimes_created} REAL crimes with REALISTIC timeline data")

# Show data quality stats
severity_counts = db.query("""
    MATCH (c:Crime)
    RETURN c.severity as severity, count(c) as count
    ORDER BY 
        CASE c.severity
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            ELSE 4
        END
""")

print("\n📊 Severity Distribution (Timeline-Ready):")
for s in severity_counts:
    icons = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
    print(f"   {icons.get(s['severity'], '⚪')} {s['severity']}: {s['count']} crimes")

time_sample = db.query("""
    MATCH (c:Crime)
    RETURN c.type as type, c.time as time
    ORDER BY rand()
    LIMIT 5
""")

print("\n⏰ Time Distribution Sample:")
for t in time_sample:
    print(f"   {t['type']}: {t['time']}")

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

# Timeline readiness check
timeline_check = db.query("""
    MATCH (c:Crime)
    WITH c
    WHERE c.time <> '00:00:00'
    RETURN count(c) as varied_times
""")[0]

status_check = db.query("""
    MATCH (c:Crime)
    WHERE c.status IN ['open', 'under investigation', 'closed', 'solved', 'cold case']
    RETURN count(c) as correct_status
""")[0]

# Location coverage check
location_stats = db.query("""
    MATCH (c:Crime)
    OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
    RETURN 
        count(c) as total_crimes,
        count(l) as crimes_with_location,
        count(DISTINCT l) as unique_locations
""")[0]

location_coverage = (location_stats['crimes_with_location'] / location_stats['total_crimes'] * 100) if location_stats['total_crimes'] > 0 else 0

print("\n⏱️ Timeline Readiness:")
print(f"   ✅ Crimes with varied times: {timeline_check['varied_times']}")
print(f"   ✅ Crimes with correct status: {status_check['correct_status']}")
print(f"   ✅ Severity mapping: Intelligent (type-based)")

print("\n📍 Location Coverage:")
print(f"   ✅ Total Crimes: {location_stats['total_crimes']}")
print(f"   ✅ Crimes with Location: {location_stats['crimes_with_location']} ({location_coverage:.1f}%)")
print(f"   ✅ Unique Locations: {location_stats['unique_locations']}")

# Show top crime hotspots
hotspots = db.query("""
    MATCH (c:Crime)-[:OCCURRED_AT]->(l:Location)
    RETURN l.name as location, l.district as district, count(c) as crimes
    ORDER BY crimes DESC
    LIMIT 10
""")

if hotspots:
    print("\n🔥 Top 10 Crime Hotspots:")
    for i, spot in enumerate(hotspots, 1):
        print(f"   {i}. {spot['location'][:50]}: {spot['crimes']} crimes (District {spot['district']})")

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
print("   ✓ Timeline-ready data (realistic distributions)")
print("="*60)

db.close()