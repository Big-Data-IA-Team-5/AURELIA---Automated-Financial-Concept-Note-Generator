import instructor
import openai
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

# Only create instructor client if OpenAI key is available
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    client = instructor.patch(openai.OpenAI(api_key=OPENAI_KEY))
else:
    client = None

class ConceptNoteStructure(BaseModel):
    concept_name: str
    definition: str
    formula: Optional[str] = None
    example: str
    applications: List[str]

def generate_concept_with_instructor(concept: str, context_chunks: List[Dict], source: str) -> Dict[str, Any]:
    """Generate structured concept note using instructor (if available)"""
    
    if not client or not OPENAI_KEY:
        # Fallback to structured template if no OpenAI key
        return generate_structured_fallback(concept, context_chunks, source)
    
    # Combine context
    context = "\n\n".join([chunk.get("content", "") for chunk in context_chunks])
    
    system_prompt = f"""You are a financial expert creating concept notes.
    Create a comprehensive concept note for '{concept}' using the provided context.
    
    Context:
    {context}
    
    Generate a clear, educational concept note with practical applications."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model
            response_model=ConceptNoteStructure,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a comprehensive concept note for: {concept}"}
            ],
            temperature=0.1
        )
        
        return {
            "concept_name": response.concept_name,
            "definition": response.definition,
            "formula": response.formula,
            "example": response.example,
            "applications": response.applications,
            "source": source,
            "pdf_references": [chunk.get("page_num") for chunk in context_chunks if chunk.get("page_num")]
        }
        
    except Exception as e:
        print(f"Instructor error: {e}")
        return generate_structured_fallback(concept, context_chunks, source)

def generate_structured_fallback(concept: str, context_chunks: List[Dict], source: str) -> Dict[str, Any]:
    """Fallback structured generation without LLM"""
    formulas = {
        "duration": "Modified Duration = Macaulay Duration / (1 + YTM/n)",
        "sharpe ratio": "Sharpe Ratio = (Rp - Rf) / σp", 
        "beta": "β = Cov(Ra, Rm) / Var(Rm)",
        "var": "VaR = μ - ασ",
        "alpha": "α = Rp - [Rf + β(Rm - Rf)]"
    }
    
    if source == "fintbx":
        definition = f"{concept} is a key financial metric used in quantitative analysis and risk management."
        applications = ["Portfolio risk management", "Investment performance evaluation", "Quantitative analysis"]
        formula = formulas.get(concept.lower())
        pdf_refs = [chunk.get("page_num") for chunk in context_chunks if chunk.get("page_num")]
    else:
        definition = f"{concept} is a concept with applications in various business contexts."
        applications = ["General business analysis", "Economic research"]
        formula = None
        pdf_refs = []
    
    return {
        "concept_name": concept,
        "definition": definition,
        "formula": formula,
        "example": f"For example, when analyzing {concept}, professionals consider market conditions and historical data.",
        "applications": applications,
        "source": source,
        "pdf_references": pdf_refs
    }