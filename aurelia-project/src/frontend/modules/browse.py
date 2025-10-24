import streamlit as st
import requests

API_URL = st.session_state.get('API_URL', 'https://aurelia-backend-1074058468365.us-central1.run.app')

def browse_page():
    st.title("Browse Cached Concepts")
    
    if st.button("Refresh"):
        st.rerun()

    with st.spinner("Loading..."):
        try:
            response = requests.get(f"{API_URL}/concepts", timeout=10)
            
            if response.status_code == 200:
                notes = response.json()
                
                if not notes:
                    st.info("No cached concepts yet!")
                else:
                    st.success(f"Found {len(notes)} concepts")
                    
                    fintbx = sum(1 for n in notes if n.get('source') == 'fintbx.pdf')
                    wiki = sum(1 for n in notes if n.get('source') == 'wikipedia')
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total", len(notes))
                    col2.metric("fintbx.pdf", fintbx)
                    col3.metric("Wikipedia", wiki)
                    
                    st.markdown("---")
                    
                    search = st.text_input("Search")
                    
                    if search:
                        filtered = [n for n in notes if search.lower() in n.get('concept_name', '').lower()]
                    else:
                        filtered = notes
                    
                    for note in filtered:
                        st.markdown(f"### {note.get('concept_name', 'Unknown')}")
                        
                        if note.get('source') == "fintbx.pdf":
                            st.success("fintbx.pdf")
                        else:
                            st.warning("Wikipedia")
                        
                        if note.get('definition'):
                            st.write(note['definition'])
                        
                        if note.get('formula'):
                            st.code(note['formula'])
                        
                        st.divider()
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"{e}")