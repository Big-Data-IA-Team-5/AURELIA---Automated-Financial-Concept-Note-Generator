import streamlit as st
from pages.generate import generate_page
from pages.browse import browse_page
from pages.batch_seed import batch_seed_page

st.set_page_config(
    page_title="AURELIA – Concept Note Generator",
    page_icon="💡",
    layout="wide"
)

# Sidebar navigation
menu = st.sidebar.radio(
    "Navigation",
    ["Generate", "Browse Cache", "Batch Seed", "About"]
)

if menu == "Generate":
    generate_page()
elif menu == "Browse Cache":
    browse_page()
elif menu == "Batch Seed":
    batch_seed_page()
else:
    st.title("AURELIA: Automated Financial Concept Note Generator")
    st.markdown("""
    **AURELIA** automatically generates standardized concept notes for financial topics  
    using *Retrieval-Augmented Generation (RAG)* from the *Financial Toolbox* corpus  
    and Wikipedia fallback.
    """)

st.sidebar.markdown("---")
st.sidebar.info("Backend API: `/query` and `/seed` endpoints on FastAPI Cloud Run")