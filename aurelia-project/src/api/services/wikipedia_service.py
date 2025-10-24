import wikipedia
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_wikipedia_content(concept: str) -> str:
    """Get Wikipedia content for a concept"""
    try:
        logger.info(f"Fetching Wikipedia content for: {concept}")
        
        # Search for pages
        search_results = wikipedia.search(concept, results=3)
        if not search_results:
            logger.warning(f"No Wikipedia results found for: {concept}")
            return f"No Wikipedia content found for {concept}"
        
        logger.info(f"Wikipedia search results: {search_results}")
        
        # Try to get the first page
        try:
            page = wikipedia.page(search_results[0])
            # Limit content to avoid token limits
            content = page.content[:4000]
            logger.info(f"âœ… Retrieved Wikipedia content for: {concept} ({len(content)} chars)")
            return content
            
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation for {concept}, trying: {e.options[0]}")
            # Try first disambiguation option
            page = wikipedia.page(e.options[0])
            content = page.content[:4000]
            return content
            
    except wikipedia.exceptions.PageError as e:
        logger.error(f"Wikipedia page not found for {concept}: {e}")
        return f"Error retrieving Wikipedia content: Page id \"{concept.lower()}\" does not match any pages. Try another id!"
        
    except Exception as e:
        logger.error(f"Wikipedia error for {concept}: {type(e).__name__}: {e}")
        return f"Error retrieving Wikipedia content: {str(e)}"

def generate_wikipedia_concept(concept: str) -> Dict[str, Any]:
    """
    Generate concept note from Wikipedia content
    This is a fallback when PDF corpus doesn't have the concept
    """
    content = get_wikipedia_content(concept)
    
    # Check if content retrieval failed
    if content.startswith("Error") or content.startswith("No Wikipedia"):
        definition = content
    else:
        # Use first 200 chars of Wikipedia content as definition
        definition = f"{concept}: {content[:200]}..."
    
    return {
        "concept_name": concept,
        "definition": definition,
        "formula": None,
        "example": f"Various applications of {concept} in financial and business contexts.",
        "applications": [
            "General business analysis",
            "Economic research", 
            "Cross-disciplinary applications"
        ],
        "source": "wikipedia",
        "pdf_references": []
    }