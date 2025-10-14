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
