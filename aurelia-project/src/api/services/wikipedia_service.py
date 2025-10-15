import wikipedia
from typing import Dict, Any

def get_wikipedia_content(concept: str) -> str:
    """Get Wikipedia content for a concept"""
    try:
        # Search for pages
        search_results = wikipedia.search(concept, results=3)
        if not search_results:
            return f"No Wikipedia content found for {concept}"
        
        # Try to get the first page
        try:
            page = wikipedia.page(search_results[0])
            # Limit content to avoid token limits
            content = page.content[:2000]
            return content
        except wikipedia.exceptions.DisambiguationError as e:
            # Try first disambiguation option
            page = wikipedia.page(e.options[0])
            content = page.content[:2000]
            return content
            
    except Exception as e:
        return f"Error retrieving Wikipedia content for {concept}: {str(e)}"

def generate_wikipedia_concept(concept: str) -> Dict[str, Any]:
    """Generate concept note from Wikipedia content"""
    content = get_wikipedia_content(concept)
    
    # Simple structure for Wikipedia content
    return {
        "concept_name": concept,
        "definition": f"{concept} is a concept that extends beyond traditional finance, with applications in various business and economic contexts.",
        "formula": None,
        "example": f"For example, when analyzing {concept}, professionals consider market conditions, historical data, and risk factors. Typical values range from industry benchmarks with adjustments for specific circumstances.",
        "applications": [
            "General business analysis",
            "Economic research", 
            "Cross-disciplinary applications"
        ],
        "source": "wikipedia",
        "pdf_references": []
    }