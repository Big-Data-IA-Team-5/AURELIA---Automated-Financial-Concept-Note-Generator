import streamlit as st
import requests
import os
from components.concept_card import render_concept_card

try:
    API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:8000"))
except (FileNotFoundError, KeyError):
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def browse_page():
    st.title("Browse Cached Concepts")
    
    with st.expander("API Configuration"):
        st.code(f"API URL: {API_URL}")

    if st.button("Refresh"):
        st.rerun()

    with st.spinner("Loading cached concept notes..."):
        try:
            response = requests.get(f"{API_URL}/list", timeout=10)
            if response.status_code == 200:
                notes = response.json()
                if not notes:
                    st.info("No cached concepts yet. Generate some first!")
                else:
                    st.success(f"Found {len(notes)} cached concepts")
                    for note in notes:
                        with st.container():
                            render_concept_card(note)
                            st.divider()
            else:
                st.error(f"Error fetching cache: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to API at {API_URL}")
        except Exception as e:
            st.error(f"Connection failed: {e}")