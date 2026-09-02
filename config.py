import os

# Load .env into the environment (no-op if the file is absent, e.g. on
# Streamlit Cloud or Render, where secrets come from the platform instead)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Safe function to get secrets with fallback
def get_secret(key, default=None):
    """Get a secret from Streamlit secrets if available, else the environment.

    Streamlit is imported lazily and treated as optional: this module is also
    imported by the FastAPI backend (via database.py / langgraph_agent.py),
    and a top-level `import streamlit` there would drag Streamlit - plus
    everything else in the root requirements - into the API deployment image.
    """
    try:
        import streamlit as st  # noqa: PLC0415 - intentionally lazy/optional

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Fall back to environment variables
    return os.getenv(key, default)

# Neo4j Configuration
NEO4J_URI = get_secret("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = get_secret("NEO4J_USERNAME", "neo4j")
NEO4J_USER = get_secret("NEO4J_USER", NEO4J_USERNAME)  # Alias for compatibility
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD", "password")

# OpenAI/OpenRouter Configuration
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", None)
OPENAI_BASE_URL = get_secret("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_MODEL = get_secret("OPENAI_MODEL", "anthropic/claude-3.5-sonnet")

# Groq Configuration (LangGraph agent)
GROQ_API_KEY = get_secret("GROQ_API_KEY", None)
GROQ_MODEL = get_secret("GROQ_MODEL", "openai/gpt-oss-120b")

# Application Settings
DEBUG = get_secret("DEBUG", "false").lower() == "true"

# Print configuration status (for debugging)
if DEBUG:
    print("=" * 50)
    print("Configuration Loaded:")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Neo4j Username: {NEO4J_USERNAME}")
    print(f"Neo4j Password: {'*' * len(NEO4J_PASSWORD) if NEO4J_PASSWORD else 'Not Set'}")
    print(f"OpenAI API Key: {'Set' if OPENAI_API_KEY else 'Not Set'}")
    print(f"OpenAI Base URL: {OPENAI_BASE_URL}")
    print(f"OpenAI Model: {OPENAI_MODEL}")
    print(f"Groq API Key: {'Set' if GROQ_API_KEY else 'Not Set'}")
    print(f"Groq Model: {GROQ_MODEL}")
    print("=" * 50)