import sys
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# GravityAI Streamlit API Clients
from frontend.client.api_client import GravityAPIClient as GravityAPIClient
