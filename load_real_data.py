import requests
import pandas as pd
from database import Database
from datetime import datetime
import random

db = Database()

print("="*60)
print("🌐 Loading REAL Chicago Crime Data from API")
print("="*60)

# Clear database
db.clear_all()

# Fetch data from Chicago Data Portal API
print("📡 Fetching data from Chicago API...")

# API endpoint (limit to recent data for faster testing)
url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

# Parameters: Get crimes from last 2 years, limit to 5000 for testing
params = {
    "$where": "date >= '2023-01-01T00:00:00.000'",
    "$limit": 5000,
    "$order": "date DESC"
}

response = requests.get(url, params=params)
crimes_data = response.json()

print(f"✅ Fetched {len(crimes_data)} real crime records")

# ===== STEP 1: CREATE REAL LOCATIONS FROM API DATA =====
print("\n📍 Creating locations from real crime data...")

unique_locations = {}
for crime in crimes_data:
    if 'latitude' in crime and 'longitude' in crime:
        # Use block as location identifier
        block = crime.get('block', 'Unknown')
        if block not in unique_locations:
            unique_locations[block] = {
                'name': block,
                'lat': float(crime['latitude']),
                'lon': float(crime['longitude']),
                'district': crime.get('district', 'Unknown'),
                'beat': crime.get('beat', 'Unknown')
            }

# Create location nodes
for loc_name, loc_data in list(unique_locations.items())[:100]:  # Limit to 100 locations
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            district: $district,
            beat: $beat,
            type: 'street_block'
        })
    """, loc_data)

print(f"✅ Created {min(100, len(unique_locations))} real locations")

# ===== STEP 2: CREATE REAL CRIMES FROM API =====
print("\n🚨 Creating crimes from real data...")

crime_count = 0
for crime in crimes_data[:500]:  # Limit to 500 crimes for testing
    if 'latitude' not in crime or 'longitude' not in crime:
        continue
    
    crime_id = crime.get('id', f"C{crime_count:04d}")
    
    db.query("""
        CREATE (c:Crime {
            id: $id,
            type: $type,
            date: $date,
            time: $time,
            case_number: $case_number,
            description: $description,
            arrest: $arrest,
            severity: $severity,
            status: $status
        })
    """, {
        "id": crime_id,
        "type": crime.get('primary_type', 'Unknown'),
        "date": crime.get('date', '')[:10],  # Extract date part
        "time": crime.get('date', '')[11:16],  # Extract time part
        "case_number": crime.get('case_number', 'UNKNOWN'),
        "description": crime.get('description', '')[:200],
        "arrest": crime.get('arrest', 'false') == 'true',
        "severity": random.choice(['minor', 'moderate', 'severe']),
        "status": 'solved' if crime.get('arrest') == 'true' else random.choice(['investigating', 'cold'])
    })
    
    # Link to location
    block = crime.get('block', 'Unknown')
    if block in unique_locations:
        db.query("""
            MATCH (c:Crime {id: $crime_id})
            MATCH (l:Location {name: $location})
            MERGE (c)-[:OCCURRED_AT]->(l)
        """, {"crime_id": crime_id, "location": block})
    
    crime_count += 1

print(f"✅ Created {crime_count} real crimes")

# ===== STEP 3: ADD SYNTHETIC ENRICHMENT (Your Value-Add!) =====
print("\n🎨 Adding synthetic enrichment (Organizations, Evidence, etc.)...")

# Create Organizations (Synthetic - based on crime patterns)
print("  🏢 Creating criminal organizations...")
organizations = [
    {"id": "ORG001", "name": "West Side Crew", "type": "gang", "territory": "West"},
    {"id": "ORG002", "name": "South Side Syndicate", "type": "organized_crime", "territory": "South"},
    {"id": "ORG003", "name": "North River Gang", "type": "gang", "territory": "North"},
]

for org in organizations:
    db.query("""
        CREATE (o:Organization {
            id: $id,
            name: $name,
            type: $type,
            territory: $territory,
            members_count: $members,
            activity_level: $activity
        })
    """, {**org, "members": random.randint(15, 40), "activity": random.choice(['low', 'medium', 'high'])})

print(f"✅ Created {len(organizations)} organizations")

# Create Persons (Synthetic - but linked to REAL crimes)
print("  👥 Creating persons and linking to real crimes...")

first_names = ["Marcus", "David", "Carlos", "James", "Robert", "Lisa", "Sarah", "Maria"]
last_names = ["Rivera", "Lee", "Martinez", "Wilson", "Johnson", "Chen", "Garcia", "Rodriguez"]

persons_created = []
for i in range(60):
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
            risk_score: $risk
        })
    """, {
        "id": person_id,
        "name": name,
        "age": random.randint(18, 65),
        "gender": random.choice(['Male', 'Female']),
        "occupation": random.choice(['Unemployed', 'Mechanic', 'Cook', 'Driver']),
        "record": random.choice([True, True, False]),
        "risk": round(random.uniform(0.1, 0.9), 2)
    })
    
    persons_created.append((person_id, name))

print(f"✅ Created {len(persons_created)} persons")

# Link persons to REAL crimes
print("  🔗 Linking persons to real crimes...")
for person_id, person_name in persons_created:
    # Each person linked to 2-8 random real crimes
    num_crimes = random.randint(2, 8)
    
    # Get random crime IDs
    sample_crimes = db.query(f"""
        MATCH (c:Crime)
        RETURN c.id as id
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

# Link persons to organizations
print("  🏢 Creating gang memberships...")
for _ in range(30):
    person_id, _ = random.choice(persons_created)
    org = random.choice(organizations)
    
    db.query("""
        MATCH (p:Person {id: $person_id})
        MATCH (o:Organization {id: $org_id})
        MERGE (p)-[:MEMBER_OF {rank: $rank}]->(o)
    """, {
        "person_id": person_id,
        "org_id": org['id'],
        "rank": random.choice(['member', 'lieutenant', 'enforcer'])
    })

print("✅ Created gang memberships")

# Add Evidence (Synthetic)
print("  🔍 Creating evidence items...")
for i in range(50):
    db.query("""
        CREATE (e:Evidence {
            id: $id,
            type: $type,
            description: $description,
            verified: $verified,
            significance: $significance
        })
    """, {
        "id": f"E{i:03d}",
        "type": random.choice(['physical', 'digital', 'forensic', 'testimonial']),
        "description": random.choice(['DNA sample', 'Fingerprint', 'Security footage', 'Witness statement']),
        "verified": random.choice([True, True, False]),
        "significance": random.choice(['low', 'medium', 'high', 'critical'])
    })

print("✅ Created 50 evidence items")

# Final stats
stats = db.query("""
    MATCH (n)
    RETURN labels(n)[0] as type, count(n) as count
    ORDER BY count DESC
""")

print("\n" + "="*60)
print("🎉 DATABASE LOADED SUCCESSFULLY!")
print("="*60)
for stat in stats:
    print(f"   {stat['type']}: {stat['count']}")
print("="*60)

db.close()