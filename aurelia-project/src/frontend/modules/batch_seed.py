
import streamlit as st
import requests
import time

API_URL = st.session_state.get('API_URL', 'https://aurelia-backend-1074058468365.us-central1.run.app')

def batch_seed_page():
    st.title(" Batch Seed Concepts")
    
    st.markdown("Pre-populate the cache with multiple financial concepts.")
    
    text = st.text_area("Enter concepts (one per line):", placeholder="Sharpe Ratio\nBeta\nAlpha", height=200)
    
    if st.button("Seed Concepts", type="primary", use_container_width=True):
        concepts = [c.strip() for c in text.splitlines() if c.strip()]
        if not concepts:
            st.error("Enter at least one concept")
            return

        st.info(f"Seeding {len(concepts)} concepts...")
        
        progress = st.progress(0)
        status = st.empty()
        
        results = []
        success_count = 0
        fintbx_count = 0
        wiki_count = 0
        cache_hits = 0

        for idx, concept in enumerate(concepts):
            status.text(f"⏳ {concept}...")
            try:
                r = requests.post(f"{API_URL}/query", json={"concept": concept}, timeout=30)
                
                if r.status_code == 200:
                    data = r.json()
                    
                    # FIX: Handle all cases for source extraction
                    source = data.get('source')
                    
                    # If no source at top level, check in concept_note
                    if not source or source == 'unknown':
                        concept_note = data.get('concept_note', {})
                        source = concept_note.get('source', 'unknown')
                    
                    # If still unknown, default to fintbx.pdf for cached items
                    if source == 'unknown' and data.get('cached'):
                        source = 'fintbx.pdf'  
                    
                    cached = data.get('cached', False)
                    
                    # Count by source
                    if source == "fintbx.pdf":
                        fintbx_count += 1
                        emoji = "📊"
                    elif source == "wikipedia":
                        wiki_count += 1
                        emoji = "📚"
                    else:
                        emoji = ""
                    
                    if cached:
                        cache_hits += 1
                        results.append(f"{concept} {emoji} (cached - {source})")
                    else:
                        results.append(f"{concept} {emoji} (new - {source})")
                    
                    success_count += 1
                else:
                    results.append(f"{concept} (failed)")
            except:
                results.append(f"{concept} (error)")
            
            progress.progress((idx + 1) / len(concepts))
            time.sleep(0.2)
        
        status.text("")
        progress.empty()
        
        st.success("Batch seeding complete!")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Success", success_count)
        col2.metric("fintbx.pdf", fintbx_count)
        col3.metric("Wikipedia", wiki_count)
        col4.metric("Cached", cache_hits)
        col5.metric("Total", len(concepts))
        
        st.markdown("---")
        st.markdown("### Detailed Results")
        for result in results:
            st.text(result)

