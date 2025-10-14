import streamlit as st
import json

def render_concept_card(concept_data: dict):
    """Render a concept note with proper formatting."""
    st.markdown(f"{concept_data.get('concept','Unknown Concept')}")
    source = concept_data.get("source", "unknown")
    st.caption(f"Source: {source}")

    note = concept_data.get("note")
    if not note:
        st.warning("No note content found.")
        return

    if isinstance(note, str):
        try:
            note = json.loads(note)
        except Exception:
            st.write(note)
            return

    for section, content in note.items():
        st.markdown(f"**{section}**")
        st.write(content)