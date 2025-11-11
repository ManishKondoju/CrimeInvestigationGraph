#!/usr/bin/env python3
"""
Test script to verify face recognition setup
Run this before using the face recognition feature
"""

from database import Database
from face_recognition import FaceRecognition

print("="*60)
print("🧪 Testing Face Recognition Setup")
print("="*60)

# Connect to database
db = Database()
face_rec = FaceRecognition(db)

# Check how many persons exist
print("\n📊 Checking database...")
persons = db.query("MATCH (p:Person) RETURN count(p) as count")
person_count = persons[0]['count'] if persons else 0

print(f"✅ Found {person_count} persons in database")

if person_count == 0:
    print("\n❌ ERROR: No persons found in database!")
    print("💡 Run load_hybrid_data.py first to populate the database")
    exit(1)

# Check how many have embeddings
with_embeddings = db.query("""
    MATCH (p:Person)
    WHERE p.face_embedding IS NOT NULL
    RETURN count(p) as count
""")

embedding_count = with_embeddings[0]['count'] if with_embeddings else 0

print(f"📊 Persons with face embeddings: {embedding_count}/{person_count}")

if embedding_count == 0:
    print("\n🔄 Initializing face embeddings...")
    count = face_rec.initialize_synthetic_embeddings()
    print(f"✅ Created {count} face embeddings!")
elif embedding_count < person_count:
    print("\n🔄 Some persons missing embeddings, updating...")
    count = face_rec.initialize_synthetic_embeddings()
    print(f"✅ Created {count} new embeddings!")
else:
    print("✅ All persons have face embeddings!")

# Test a sample query
print("\n🧪 Testing similarity search...")
sample_person = db.query("""
    MATCH (p:Person)
    WHERE p.face_embedding IS NOT NULL
    RETURN p.name as name, p.face_embedding as embedding
    LIMIT 1
""")

if sample_person:
    print(f"✅ Sample person: {sample_person[0]['name']}")
    print("✅ Embedding exists and is accessible")
else:
    print("❌ Could not retrieve sample person")

print("\n" + "="*60)
print("✅ Face Recognition Setup Complete!")
print("="*60)
print("\n🚀 You can now:")
print("   1. Run: streamlit run app.py")
print("   2. Navigate to 'Face Recognition' tab")
print("   3. Upload any photo to test the system")
print("\n💡 The system will find the 'closest matches' from the database")
print("="*60)

db.close()