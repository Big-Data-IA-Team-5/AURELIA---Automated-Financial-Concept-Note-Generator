
import streamlit as st
import requests

API_URL = st.session_state.get('API_URL', 'https://aurelia-backend-1074058468365.us-central1.run.app')

def generate_page():
    st.title("Generate Concept Note")
    
    concept = st.text_input("Enter a financial concept:", placeholder="e.g., Sharpe Ratio, Duration")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        force_refresh = st.checkbox("Force refresh", value=False)
    with col2:
        generate_button = st.button("Generate", type="primary", use_container_width=True)

    if generate_button and concept:
        with st.spinner(f"Generating '{concept}'..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"concept": concept, "force_refresh": force_refresh},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    concept_note = data.get('concept_note', {})
                    
                    concept_name = concept_note.get('concept_name', concept)
                    definition = concept_note.get('definition', '')
                    formula = concept_note.get('formula')
                    example = concept_note.get('example', '')
                    applications = concept_note.get('applications', [])
                    
                    # ✅ FIX: Extract PDF pages from BOTH locations
                    pdf_pages = data.get('pdf_pages', [])
                    if not pdf_pages:
                        pdf_pages = concept_note.get('pdf_references', [])
                    
                    source = data.get('source', 'unknown')
                    cached = data.get('cached', False)
                    processing_time = data.get('processing_time_ms', 0)
                    ai_model = data.get('ai_model', 'unknown')
                    chunks = data.get('chunks_retrieved', 0)
                    
                    # Metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.success("Cached" if cached else " New")
                    with col2:
                        st.success(" fintbx.pdf" if source == "fintbx.pdf" else " Wikipedia")
                    with col3:
                        st.metric("Time", f"{processing_time:.0f}ms" if processing_time else "Instant")
                    with col4:
                        st.metric("Chunks", chunks)
                    
                    st.caption(f" {ai_model}")
                    st.markdown("---")
                    
                    # Concept display
                    st.markdown(f"## {concept_name}")
                    
                    if definition:
                        st.markdown("###  Definition")
                        st.write(definition)
                    
                    if formula:
                        st.markdown("###  Formula")
                        st.code(formula)
                    
                    if example:
                        st.markdown("###  Example")
                        st.write(example)
                    
                    if applications:
                        st.markdown("###  Applications")
                        for app in applications:
                            st.write(f"• {app}")
                    
                    if pdf_pages and len(pdf_pages) > 0 and source == "fintbx.pdf":
                        st.markdown("###  PDF References")
                        st.info(f"**Source Pages:** {', '.join([f'Page {p}' for p in pdf_pages])}")
                    
                    with st.expander(" Debug: Raw Response"):
                        st.json(data)
                else:
                    st.error(f" Error: {response.status_code}")
                    st.code(response.text)
            except Exception as e:
                st.error(f" Error: {e}")
