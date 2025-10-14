import streamlit as st
import requests
import os
from components.concept_card import render_concept_card

# Try secrets first, fall back to env var, then default
try:
    API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:8000"))
except (FileNotFoundError, KeyError):
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def generate_page():
    st.title("Generate Concept Note")
    
    # Show current API URL for debugging
    with st.expander("API Configuration"):
        st.code(f"API URL: {API_URL}")
    
    concept = st.text_input("Enter a financial concept:", placeholder="e.g. Sharpe Ratio")

    if st.button("Generate Concept Note"):
        if not concept:
            st.error("Please enter a concept name.")
            return

        with st.spinner("Querying AURELIA API..."):
            try:
                response = requests.post(
                    f"{API_URL}/query", 
                    json={"concept": concept},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Retrieved from {data.get('source','unknown')}")
                    render_concept_card(data)
                else:
                    st.error(f"API error {response.status_code}: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to API at {API_URL}. Is the backend running?")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Try again.")
            except Exception as e:
                st.error(f"Connection failed: {e}")