import os
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# Try to import streamlit for cloud deployment
try:
    import streamlit as st
    # Use Streamlit secrets if available (cloud), otherwise fall back to .env (local)
    NEO4J_URI = st.secrets.get("NEO4J_URI", os.getenv("NEO4J_URI"))
    NEO4J_USER = st.secrets.get("NEO4J_USER", os.getenv("NEO4J_USER"))
    NEO4J_PASSWORD = st.secrets.get("NEO4J_PASSWORD", os.getenv("NEO4J_PASSWORD"))
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
except (ImportError, AttributeError):
    # Streamlit not available or secrets not configured, use environment variables
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-oss-20b:free"  # Fast and free!