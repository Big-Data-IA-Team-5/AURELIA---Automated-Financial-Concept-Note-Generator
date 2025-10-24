# import streamlit as st
# import json

# def render_concept_card(concept_data: dict):
#     """Render a concept note with proper formatting."""
#     st.markdown(f"{concept_data.get('concept','Unknown Concept')}")
#     source = concept_data.get("source", "unknown")
#     st.caption(f"Source: {source}")

#     note = concept_data.get("note")
#     if not note:
#         st.warning("No note content found.")
#         return

#     if isinstance(note, str):
#         try:
#             note = json.loads(note)
#         except Exception:
#             st.write(note)
#             return

#     for section, content in note.items():
#         st.markdown(f"**{section}**")
#         st.write(content)


#####################################################CLAUDE CODE V2


import streamlit as st
import json

def render_concept_card(concept_data: dict):
    """Render a concept note with proper formatting, PDF references, and clear source indication."""
    
    # Display concept name
    st.markdown(f"### {concept_data.get('concept', 'Unknown Concept')}")
    
    # Get source information
    source = concept_data.get("source", "unknown")
    
    # REQUIREMENT #18: Clear indication when Wikipedia content is used
    if source.lower() == "wikipedia" or source.lower() == "wiki":
        st.warning("**Source: Wikipedia** - No cached corpus data available. This content is from Wikipedia fallback.")
    elif source.lower() == "cached" or source.lower() == "rag" or source.lower() == "financial_toolbox":
        st.success(f"**Source: Financial Toolbox RAG** - Retrieved from cached corpus")
    else:
        st.info(f"**Source: {source}**")
    
    # REQUIREMENT #16: Display PDF section references if available
    if "references" in concept_data and concept_data["references"]:
        with st.expander("**Source References (PDF Sections)**", expanded=True):
            references = concept_data["references"]
            if isinstance(references, list):
                for idx, ref in enumerate(references, 1):
                    if isinstance(ref, dict):
                        doc_name = ref.get("document", "Unknown Document")
                        section = ref.get("section", "N/A")
                        page = ref.get("page", "N/A")
                        chunk_id = ref.get("chunk_id", "N/A")
                        score = ref.get("score", None)
                        
                        st.markdown(f"**Reference {idx}:**")
                        st.caption(f"Document: `{doc_name}`")
                        st.caption(f"Section: `{section}` | Page: `{page}` | Chunk: `{chunk_id}`")
                        if score is not None:
                            st.caption(f"Relevance Score: `{score:.4f}`")
                        st.divider()
                    else:
                        st.caption(f"• {ref}")
            else:
                st.caption(references)
    elif source.lower() not in ["wikipedia", "wiki"]:
        # If it's from RAG but no references provided, show a note
        st.caption("PDF references not available in response")

    # Display note content
    note = concept_data.get("note")
    if not note:
        st.warning("No note content found.")
        return

    # Parse note if it's a JSON string
    if isinstance(note, str):
        try:
            note = json.loads(note)
        except Exception:
            st.write(note)
            return

    # Display note sections
    st.markdown("---")
    st.markdown("#### Concept Note Details")
    
    if isinstance(note, dict):
        for section, content in note.items():
            st.markdown(f"**{section}**")
            st.write(content)
            st.markdown("")  # Add spacing
    else:
        st.write(note)