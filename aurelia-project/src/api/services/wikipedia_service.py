"""
Wikipedia fallback service when concept not found in PDF
"""

import wikipedia
from typing import Optional, Dict
from .instructor_service import generate_concept_note


def get_wikipedia_content(concept: str) -> Optional[str]:
    """
    Fetch Wikipedia content for a concept
    """
    try:
        wikipedia.set_lang("en")
        page = wikipedia.page(concept, auto_suggest=True)
        content = f"{page.summary}\n\n{page.content[:4000]}"
        print(f"✅ Found Wikipedia page for: {concept}")
        return content
        
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            print(f"⚠️ Disambiguation for '{concept}', trying: {e.options[0]}")
            page = wikipedia.page(e.options[0])
            content = f"{page.summary}\n\n{page.content[:4000]}"
            return content
        except Exception as inner_e:
            print(f"❌ Error with disambiguation: {inner_e}")
            return None
            
    except wikipedia.exceptions.PageError:
        print(f"❌ Wikipedia page not found for: {concept}")
        return None
        
    except Exception as e:
        print(f"❌ Wikipedia error: {e}")
        return None


def generate_from_wikipedia(concept: str) -> Dict:
    """
    Generate concept note using Wikipedia as source
    """
    print(f"🔍 Searching Wikipedia for: {concept}")
    
    wiki_content = get_wikipedia_content(concept)
    
    if not wiki_content:
        return {
            "concept_name": concept,
            "definition": f"Could not find information for '{concept}' in Wikipedia.",
            "formula": None,
            "example": "N/A",
            "applications": ["Information not available"],
            "key_points": ["Concept not found in Wikipedia"],
            "source": "wikipedia",
            "error": "Wikipedia page not found"
        }
    
    wiki_chunks = [
        {
            "content": wiki_content,
            "page_num": "Wikipedia",
            "score": 1.0
        }
    ]
    
    result = generate_concept_note(concept, wiki_chunks, source="wikipedia")
    return result


if __name__ == "__main__":
    print("Testing Wikipedia Fallback Service...")
    print("=" * 50)
    
    import json
    result = generate_from_wikipedia("Cryptocurrency")
    print(json.dumps(result, indent=2))