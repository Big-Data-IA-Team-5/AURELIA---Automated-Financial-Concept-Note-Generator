"""PROJECT AURELIA - Shared Configuration for All Team Members"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== GCP CONFIGURATION =====
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "mineral-concord-474700-v2")
REGION = "us-central1"

# Storage Buckets (Your organized approach)
BUCKET_PDFS = "aurelia-pdf-corpus-474700"
BUCKET_DAGS = "aurelia-airflow-dags-474700" 
BUCKET_ARTIFACTS = "aurelia-artifacts-474700"
BUCKET_FRONTEND = "aurelia-frontend-data-474700"

# ===== DATABASE CONFIGURATION =====
DB_CONNECTION = "mineral-concord-474700-v2:us-central1:aurelia-db"
DB_NAME = "aurelia_concepts"
DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD", "AureliaTeam2025")
DB_HOST = os.getenv("DB_HOST", "34.136.16.4")  # Your public IP
DB_PORT = 5432

# ===== OPENAI CONFIGURATION =====
OPENAI_KEY = os.getenv("OPENAI_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
CHAT_MODEL = "gpt-4o-mini"
MAX_TOKENS = 4096

# ===== VECTOR DATABASE CONFIGURATION =====
# Pinecone (Primary)
PINECONE_KEY = os.getenv("PINECONE_KEY")
PINECONE_INDEX = "aurelia-financial"
PINECONE_ENVIRONMENT = "us-east-1-aws"

# ChromaDB (Backup/Local)
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION = "financial_concepts"

# ===== RAG SYSTEM CONFIGURATION =====
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SIMILARITY_THRESHOLD = 0.8
MAX_RETRIEVED_DOCS = 5

# ===== API CONFIGURATION =====
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# ===== FRONTEND CONFIGURATION =====
STREAMLIT_HOST = "0.0.0.0"
STREAMLIT_PORT = 8501

# ===== AIRFLOW CONFIGURATION =====
AIRFLOW_HOME = "/opt/airflow"
AIRFLOW_DAGS_FOLDER = "/opt/airflow/dags"

# ===== PROCESSING CONFIGURATION =====
MAX_WORKERS = 4
BATCH_SIZE = 10
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 300

# ===== P2 SPECIFIC: HELPER FUNCTIONS =====
def get_database_url(use_proxy=False):
    """Get database URL for different connection types"""
    if use_proxy:
        # When using Cloud SQL Proxy (development)
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:5432/{DB_NAME}"
    else:
        # Direct connection (production) - your current setup
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_database_config():
    """Get database configuration as dictionary"""
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "connection_string": DB_CONNECTION
    }

def validate_config():
    """Validate that required configuration is present"""
    required_vars = [
        ("DB_HOST", DB_HOST),
        ("DB_PASSWORD", DB_PASSWORD),
        ("PROJECT_ID", PROJECT_ID)
    ]
    
    missing = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing.append(var_name)
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    return True

# ===== VALIDATION ON IMPORT =====
if __name__ == "__main__":
    # Test configuration when run directly
    print("PROJECT AURELIA Configuration Test")
    print("=" * 40)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Database Host: {DB_HOST}")
    print(f"Database Name: {DB_NAME}")
    print(f"API Port: {API_PORT}")
    
    try:
        validate_config()
        print("✅ Configuration validation passed")
        
        # Test database URL generation
        direct_url = get_database_url(use_proxy=False)
        proxy_url = get_database_url(use_proxy=True)
        
        print(f"Direct DB URL: {direct_url.replace(DB_PASSWORD, '*****')}")
        print(f"Proxy DB URL: {proxy_url.replace(DB_PASSWORD, '*****')}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")