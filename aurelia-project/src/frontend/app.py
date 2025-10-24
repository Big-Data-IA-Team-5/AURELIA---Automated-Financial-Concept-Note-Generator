import streamlit as st
from modules.generate import generate_page
from modules.browse import browse_page
from modules.batch_seed import batch_seed_page
import requests

st.set_page_config(
    page_title="AURELIA - Financial Concept Generator",  
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "https://aurelia-backend-1074058468365.us-central1.run.app"

if 'API_URL' not in st.session_state:
    st.session_state.API_URL = API_URL

st.sidebar.title("AURELIA")
st.sidebar.markdown("**AI Financial Concept Generator**")
st.sidebar.markdown("---")

menu = st.sidebar.radio("Navigation", ["Home", "Generate", "Browse Cache", "Batch Seed"], index=0)

st.sidebar.markdown("---")

try:
    health = requests.get(f"{API_URL}/health", timeout=3).json()
    version = health.get("version", "?")
    db_status = health.get("database_status", "unknown")
    pinecone = health.get("pinecone_status", "")
    ai_models = health.get("ai_models", {})
    
    lines = ["**System Status:**"]
    if db_status == "healthy":
        lines.append("- Database:  PostgreSQL")
    if "vectors" in pinecone:
        count = pinecone.split('(')[1].split(' ')[0]
        lines.append(f"- Pinecone:  {count} vectors")
    if ai_models.get('instructor') == 'available':
        lines.append("- Instructor: GPT-4o-mini")
    lines.append(f"- Version: v{version}")
    
    st.sidebar.success("\n".join(lines))
except:
    st.sidebar.error(" Backend unreachable")

st.sidebar.markdown("---")

if menu == "Home":
    st.title(" AURELIA")
    st.markdown("**AI Financial Concept Generator**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ###  Features
        - **20,711 Vectors** from fintbx.pdf
        - **Instructor + OpenAI**
        - **Pinecone RAG**
        - **PostgreSQL Caching**
        """)
    with col2:
        st.markdown("""
        ###  Quick Start
        1. **Generate** - Create notes
        2. **Browse Cache** - View saved
        3. **Batch Seed** - Bulk generate
        """)
    
    try:
        metrics = requests.get(f"{API_URL}/metrics", timeout=3).json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Queries", metrics.get("total_queries", 0))
        col2.metric("Instructor", metrics.get("instructor_calls", 0))
        col3.metric("Pinecone", metrics.get("pinecone_queries", 0))
        col4.metric("Cache Rate", f"{metrics.get('cache_hit_rate', 0):.1f}%")
    except:
        pass

elif menu == "Generate":
    generate_page()
elif menu == "Browse Cache":
    browse_page()
elif menu == "Batch Seed":
    batch_seed_page()