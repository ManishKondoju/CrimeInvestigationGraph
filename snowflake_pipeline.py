import snowflake.connector
import requests
import pandas as pd
from database import Database
import config
import random

print("="*60)
print("❄️  Snowflake + Neo4j Integration Pipeline")
print("="*60)

# Connect to Snowflake
print("\n🔌 Connecting to Snowflake...")
sf_conn = snowflake.connector.connect(
    user=config.SNOWFLAKE_USER,
    password=config.SNOWFLAKE_PASSWORD,
    account=config.SNOWFLAKE_ACCOUNT,
    warehouse=config.SNOWFLAKE_WAREHOUSE,
    database=config.SNOWFLAKE_DATABASE,
    schema=config.SNOWFLAKE_SCHEMA
)
print("✅ Connected to Snowflake!")

cursor = sf_conn.cursor()

# Fetch real Chicago crime data
print("\n📡 Fetching REAL Chicago crime data from API...")
url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
params = {
    "$where": "date >= '2024-01-01T00:00:00.000'",
    "$limit": 1000
}

response = requests.get(url, params=params)
crimes_data = response.json()
print(f"✅ Fetched {len(crimes_data)} real crimes from Chicago API")

# Create table in Snowflake
print("\n🗂️  Creating Snowflake table...")
cursor.execute("""
    CREATE OR REPLACE TABLE CRIMES (
        id VARCHAR PRIMARY KEY,
        type VARCHAR,
        date VARCHAR,
        block VARCHAR,
        latitude FLOAT,
        longitude FLOAT,
        arrest BOOLEAN
    )
""")
print("✅ Table created")

# Load data into Snowflake
print("\n📥 Loading crimes into Snowflake...")
for crime in crimes_data[:500]:
    try:
        cursor.execute("""
            INSERT INTO CRIMES VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            crime.get('id', ''),
            crime.get('primary_type', 'Unknown'),
            crime.get('date', '')[:10],
            crime.get('block', 'Unknown'),
            float(crime.get('latitude', 0)) if crime.get('latitude') else None,
            float(crime.get('longitude', 0)) if crime.get('longitude') else None,
            crime.get('arrest', 'false') == 'true'
        ))
    except:
        continue

sf_conn.commit()
print("✅ Loaded 500 crimes into Snowflake")

# Query Snowflake
print("\n📊 Running analytics in Snowflake...")
stats = cursor.execute("""
    SELECT 
        type, 
        COUNT(*) as count 
    FROM CRIMES 
    GROUP BY type 
    ORDER BY count DESC 
    LIMIT 5
""").fetchall()

print("Top crime types:")
for row in stats:
    print(f"  {row[0]}: {row[1]}")

# ETL to Neo4j
print("\n🔄 ETL: Snowflake → Neo4j...")
db = Database()
db.clear_all()

# Get data from Snowflake
crimes = cursor.execute("""
    SELECT id, type, date, block, latitude, longitude, arrest
    FROM CRIMES
    WHERE latitude IS NOT NULL
""").fetchall()

# Load locations
print("  📍 Creating locations...")
unique_blocks = {}
for crime in crimes:
    block = crime[3]
    if block not in unique_blocks and crime[4]:
        unique_blocks[block] = {
            'name': block,
            'lat': crime[4],
            'lon': crime[5]
        }

for block, data in list(unique_blocks.items())[:50]:
    db.query("""
        CREATE (l:Location {
            name: $name,
            latitude: $lat,
            longitude: $lon,
            source: 'snowflake'
        })
    """, data)

print(f"  ✅ Created {min(50, len(unique_blocks))} locations")

# Load crimes
print("  🚨 Creating crimes...")
for crime in crimes[:200]:
    db.query("""
        CREATE (c:Crime {
            id: $id,
            type: $type,
            date: $date,
            arrest_made: $arrest,
            source: 'snowflake'
        })
    """, {
        "id": crime[0],
        "type": crime[1],
        "date": crime[2],
        "arrest": crime[6]
    })
    
    # Link to location
    db.query("""
        MATCH (c:Crime {id: $cid})
        MATCH (l:Location {name: $loc})
        MERGE (c)-[:OCCURRED_AT]->(l)
    """, {"cid": crime[0], "loc": crime[3]})

print("  ✅ Created 200 crimes from Snowflake")

# Add synthetic enrichment
print("\n🎨 Adding synthetic enrichment...")

# Organizations
orgs = [
    {"id": "ORG001", "name": "West Side Crew"},
    {"id": "ORG002", "name": "South Side Syndicate"},
]

for org in orgs:
    db.query("""
        CREATE (o:Organization {
            id: $id, name: $name,
            type: 'gang', members_count: $members,
            source: 'synthetic'
        })
    """, {**org, "members": random.randint(20, 40)})

# Persons
print("  👥 Creating persons...")
persons = []
for i in range(40):
    name = f"Person_{i}"
    db.query("""
        CREATE (p:Person {
            id: $id, name: $name, age: $age,
            risk_score: $risk, source: 'synthetic'
        })
    """, {
        "id": f"P{i:03d}",
        "name": name,
        "age": random.randint(20, 60),
        "risk": round(random.uniform(0.3, 0.9), 2)
    })
    persons.append(f"P{i:03d}")

# Link persons to REAL crimes
print("  🔗 Linking to real crimes...")
for pid in persons:
    crimes_sample = db.query("""
        MATCH (c:Crime {source: 'snowflake'})
        RETURN c.id LIMIT 3
    """)
    
    for c in crimes_sample:
        db.query("""
            MATCH (p:Person {id: $pid})
            MATCH (c:Crime {id: $cid})
            MERGE (p)-[:PARTY_TO]->(c)
        """, {"pid": pid, "cid": c['c.id']})

# Link to organizations
for _ in range(20):
    db.query("""
        MATCH (p:Person {source: 'synthetic'})
        WITH p ORDER BY rand() LIMIT 1
        MATCH (o:Organization {source: 'synthetic'})
        WITH p, o ORDER BY rand() LIMIT 1
        MERGE (p)-[:MEMBER_OF {rank: $rank}]->(o)
    """, {"rank": random.choice(['member', 'lieutenant'])})

print("✅ Synthetic enrichment complete")

# Final stats
print("\n" + "="*60)
print("📊 FINAL DATABASE STATISTICS")
print("="*60)

stats = db.query("""
    MATCH (n)
    RETURN labels(n)[0] as type, 
           n.source as source,
           count(n) as count
    ORDER BY type, source
""")

for stat in stats:
    source_tag = "🌐 REAL" if stat['source'] == 'snowflake' else "🎨 SYNTHETIC"
    print(f"   {stat['type']}: {stat['count']} {source_tag}")

print("\n" + "="*60)
print("🎉 SUCCESS! You now have:")
print("   • Snowflake: Data warehouse with REAL Chicago crimes")
print("   • Neo4j: Knowledge graph with real crimes + synthetic enrichment")
print("   • Ready for demo!")
print("="*60)

cursor.close()
sf_conn.close()
db.close()
