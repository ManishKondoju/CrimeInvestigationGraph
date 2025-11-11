# face_recognition.py - Synthetic Face Recognition System
import streamlit as st
from PIL import Image
import numpy as np
from database import Database
import io
import base64

class FaceRecognition:
    """
    Synthetic Face Recognition using embedding similarity.
    In production, you'd use deepface or face_recognition library.
    For demo, we'll use synthetic embeddings.
    """
    
    def __init__(self, db):
        self.db = db
        
    def generate_synthetic_embedding(self, image):
        """
        Generate a synthetic face embedding from an image.
        In production, use: deepface.represent(img, model_name='Facenet')
        
        For demo purposes, we create a 128-dimensional vector based on image properties.
        """
        # Convert to numpy array
        img_array = np.array(image)
        
        # Generate synthetic embedding based on image statistics
        # In production, this would be a real face embedding
        embedding = []
        
        # Use image properties to create a "fingerprint"
        for channel in range(3):  # RGB
            channel_data = img_array[:, :, channel].flatten()
            embedding.extend([
                np.mean(channel_data),
                np.std(channel_data),
                np.median(channel_data),
                np.percentile(channel_data, 25),
                np.percentile(channel_data, 75)
            ])
        
        # Add shape features
        embedding.extend([
            img_array.shape[0],  # height
            img_array.shape[1],  # width
            img_array.shape[0] / img_array.shape[1]  # aspect ratio
        ])
        
        # Pad to 128 dimensions
        while len(embedding) < 128:
            embedding.append(np.random.normal(0, 0.1))
        
        embedding = embedding[:128]
        
        # Normalize
        embedding = np.array(embedding)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.tolist()
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def search_by_face(self, image, top_k=5):
        """
        Search for suspects by face similarity.
        
        Args:
            image: PIL Image object
            top_k: Number of top matches to return
            
        Returns:
            List of dictionaries with suspect info and similarity scores
        """
        # Generate embedding for uploaded image
        query_embedding = self.generate_synthetic_embedding(image)
        
        # Get all persons with face embeddings from database
        persons_query = """
        MATCH (p:Person)
        WHERE p.face_embedding IS NOT NULL
        RETURN p.name as name, 
               p.age as age,
               p.gender as gender,
               p.face_embedding as embedding,
               id(p) as person_id
        """
        
        persons = self.db.query(persons_query)
        
        if not persons:
            return []
        
        # Calculate similarities
        results = []
        for person in persons:
            try:
                # Parse embedding (stored as string in Neo4j)
                stored_embedding = eval(person['embedding']) if isinstance(person['embedding'], str) else person['embedding']
                
                # Calculate similarity
                similarity = self.cosine_similarity(query_embedding, stored_embedding)
                
                results.append({
                    'person_id': person['person_id'],
                    'name': person['name'],
                    'age': person['age'],
                    'gender': person['gender'],
                    'similarity': similarity,
                    'confidence': f"{similarity * 100:.1f}%"
                })
            except Exception as e:
                st.warning(f"Error processing person {person.get('name', 'Unknown')}: {str(e)}")
                continue
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def get_suspect_profile(self, person_id):
        """Get complete profile for a suspect including criminal history"""
        query = """
        MATCH (p:Person)
        WHERE id(p) = $person_id
        
        // Get crimes
        OPTIONAL MATCH (p)-[:PARTY_TO]->(c:Crime)
        OPTIONAL MATCH (c)-[:OCCURRED_AT]->(l:Location)
        
        // Get gang affiliation
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(o:Organization)
        
        // Get weapons
        OPTIONAL MATCH (p)-[:OWNS]->(w:Weapon)
        
        // Get known associates
        OPTIONAL MATCH (p)-[:KNOWS]->(associate:Person)
        
        RETURN p.name as name,
               p.age as age,
               p.gender as gender,
               collect(DISTINCT {
                   type: c.type,
                   date: c.date,
                   severity: c.severity,
                   location: l.name
               }) as crimes,
               collect(DISTINCT o.name) as gangs,
               collect(DISTINCT w.type) as weapons,
               collect(DISTINCT associate.name) as associates
        """
        
        result = self.db.query(query, {'person_id': person_id})
        
        if result:
            return result[0]
        return None
    
    def initialize_synthetic_embeddings(self):
        """
        Initialize synthetic face embeddings for all persons in database.
        This should be run once during setup.
        """
        try:
            # Get all persons without embeddings
            persons = self.db.query("""
                MATCH (p:Person)
                WHERE p.face_embedding IS NULL
                RETURN id(p) as person_id, p.name as name
            """)
            
            if not persons:
                return 0
            
            # Generate synthetic embeddings
            count = 0
            for person in persons:
                # Generate a unique synthetic embedding based on person_id
                np.random.seed(person['person_id'])  # Consistent embedding per person
                synthetic_embedding = np.random.randn(128)
                synthetic_embedding = synthetic_embedding / np.linalg.norm(synthetic_embedding)
                
                # Store in Neo4j
                update_query = """
                MATCH (p:Person)
                WHERE id(p) = $person_id
                SET p.face_embedding = $embedding
                """
                
                self.db.query(update_query, {
                    'person_id': person['person_id'],
                    'embedding': str(synthetic_embedding.tolist())
                })
                
                count += 1
            
            return count
        
        except Exception as e:
            st.error(f"Error initializing embeddings: {str(e)}")
            return 0


def render_face_recognition_page(db):
    """Render the face recognition page in Streamlit"""
    
    st.title("🔍 Face Recognition - Suspect Identification")
    st.markdown("Upload a suspect photo to search the criminal database")
    st.markdown("---")
    
    # Initialize face recognition system
    face_rec = FaceRecognition(db)
    
    # Setup section
    with st.expander("⚙️ System Setup (Run Once)", expanded=False):
        st.markdown("**Initialize face embeddings for all suspects in database**")
        
        if st.button("🔄 Initialize Face Embeddings"):
            with st.spinner("Generating synthetic face embeddings..."):
                count = face_rec.initialize_synthetic_embeddings()
                if count > 0:
                    st.success(f"✅ Successfully initialized {count} face embeddings!")
                else:
                    st.info("ℹ️ All suspects already have face embeddings")
    
    st.markdown("---")
    
    # Upload section
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📸 Upload Suspect Photo")
        
        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of the suspect's face"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Photo", use_column_width=True)
            
            # Search button
            if st.button("🔍 Search Database", type="primary", use_container_width=True):
                with st.spinner("🔎 Searching criminal database..."):
                    # Perform face recognition search
                    matches = face_rec.search_by_face(image, top_k=5)
                    
                    if matches:
                        st.session_state['face_matches'] = matches
                        st.success(f"✅ Found {len(matches)} potential matches!")
                    else:
                        st.warning("⚠️ No matches found. Make sure face embeddings are initialized.")
    
    with col2:
        st.markdown("### 🎯 Search Results")
        
        if 'face_matches' in st.session_state and st.session_state['face_matches']:
            matches = st.session_state['face_matches']
            
            # Display top match prominently
            top_match = matches[0]
            
            if top_match['similarity'] > 0.7:
                alert_type = "error"
                alert_emoji = "🚨"
                alert_text = "HIGH CONFIDENCE MATCH"
            elif top_match['similarity'] > 0.5:
                alert_type = "warning"
                alert_emoji = "⚠️"
                alert_text = "MODERATE CONFIDENCE"
            else:
                alert_type = "info"
                alert_emoji = "ℹ️"
                alert_text = "LOW CONFIDENCE"
            
            if alert_type == "error":
                st.error(f"{alert_emoji} **{alert_text}**")
            elif alert_type == "warning":
                st.warning(f"{alert_emoji} **{alert_text}**")
            else:
                st.info(f"{alert_emoji} **{alert_text}**")
            
            st.markdown(f"""
            <div style='background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 12px; border-left: 4px solid #667eea;'>
                <h3 style='margin: 0; color: #667eea;'>{top_match['name']}</h3>
                <p style='margin: 10px 0 0 0; font-size: 1.1rem;'>
                    <strong>Confidence:</strong> {top_match['confidence']}<br/>
                    <strong>Age:</strong> {top_match['age']}<br/>
                    <strong>Gender:</strong> {top_match['gender']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Button to view full profile
            if st.button(f"📋 View Full Profile - {top_match['name']}", use_container_width=True):
                st.session_state['selected_suspect_id'] = top_match['person_id']
                st.session_state['selected_suspect_name'] = top_match['name']
        else:
            st.info("👆 Upload a photo to search for suspects")
    
    st.markdown("---")
    
    # Other matches
    if 'face_matches' in st.session_state and len(st.session_state['face_matches']) > 1:
        st.markdown("### 🔢 Other Potential Matches")
        
        cols = st.columns(4)
        for i, match in enumerate(st.session_state['face_matches'][1:5], 1):
            with cols[(i-1) % 4]:
                confidence_color = '#ef4444' if match['similarity'] > 0.7 else '#f59e0b' if match['similarity'] > 0.5 else '#3b82f6'
                
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-left: 3px solid {confidence_color}; margin: 5px 0;'>
                    <strong>{match['name']}</strong><br/>
                    <span style='color: #94a3b8; font-size: 0.9rem;'>
                        {match['confidence']}<br/>
                        Age: {match['age']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Full profile display
    if 'selected_suspect_id' in st.session_state:
        st.markdown(f"### 📋 Complete Profile: {st.session_state.get('selected_suspect_name', 'Unknown')}")
        
        profile = face_rec.get_suspect_profile(st.session_state['selected_suspect_id'])
        
        if profile:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 👤 Personal Info")
                st.markdown(f"**Name:** {profile['name']}")
                st.markdown(f"**Age:** {profile['age']}")
                st.markdown(f"**Gender:** {profile['gender']}")
            
            with col2:
                st.markdown("#### 🏴 Affiliations")
                gangs = [g for g in profile['gangs'] if g]
                if gangs:
                    for gang in gangs:
                        st.markdown(f"- {gang}")
                else:
                    st.markdown("*No gang affiliations*")
            
            with col3:
                st.markdown("#### 🔫 Weapons")
                weapons = [w for w in profile['weapons'] if w]
                if weapons:
                    for weapon in weapons:
                        st.markdown(f"- {weapon}")
                else:
                    st.markdown("*No registered weapons*")
            
            # Criminal history
            st.markdown("#### 🚨 Criminal History")
            crimes = [c for c in profile['crimes'] if c.get('type')]
            
            if crimes:
                crimes_df = []
                for crime in crimes:
                    crimes_df.append({
                        'Type': crime['type'],
                        'Date': crime['date'],
                        'Severity': crime['severity'],
                        'Location': crime['location']
                    })
                
                st.dataframe(crimes_df, use_container_width=True, hide_index=True)
            else:
                st.info("No criminal history recorded")
            
            # Known associates
            st.markdown("#### 👥 Known Associates")
            associates = [a for a in profile['associates'] if a]
            
            if associates:
                cols = st.columns(min(len(associates), 4))
                for i, associate in enumerate(associates[:8]):
                    with cols[i % 4]:
                        st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 5px 0;'>
                            {associate}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No known associates")
            
            # Clear button
            if st.button("🔙 Back to Search", use_container_width=True):
                del st.session_state['selected_suspect_id']
                del st.session_state['selected_suspect_name']
                st.rerun()
        else:
            st.error("Unable to load suspect profile")