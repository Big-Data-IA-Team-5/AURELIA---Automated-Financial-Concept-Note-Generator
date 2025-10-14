import streamlit as st
import requests
import time
import os

try:
    API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:8000"))
except (FileNotFoundError, KeyError):
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def batch_seed_page():
    st.title("Batch Seed Concepts")
    
    with st.expander("API Configuration"):
        st.code(f"API URL: {API_URL}")

    text = st.text_area(
        "Enter concepts (one per line):",
        placeholder="Sharpe Ratio\nBeta\nAlpha\nVolatility"
    )
    
    if st.button("Seed Concepts"):
        concepts = [c.strip() for c in text.splitlines() if c.strip()]
        if not concepts:
            st.error("Please enter at least one concept.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        fail_count = 0

        for idx, concept in enumerate(concepts):
            status_text.text(f"Seeding {concept}...")
            try:
                response = requests.post(
                    f"{API_URL}/seed", 
                    json={"concept": concept},
                    timeout=30
                )
                if response.status_code == 200:
                    st.success(f"Seeded {concept} ({response.json().get('source')})")
                    success_count += 1
                else:
                    st.warning(f"Failed {concept}: {response.text}")
                    fail_count += 1
            except Exception as e:
                st.error(f"Error seeding {concept}: {e}")
                fail_count += 1
            
            progress_bar.progress((idx + 1) / len(concepts))
            time.sleep(0.5)
        
        status_text.text("Batch seeding complete!")
        st.info(f"Success: {success_count} | Failed: {fail_count}")