import instructor
import openai
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client with instructor
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    try:
        client = instructor.patch(openai.OpenAI(api_key=OPENAI_KEY))
        logger.info("✅ Instructor client initialized with OpenAI GPT-4o-mini")
    except Exception as e:
        client = None
        logger.warning(f"⚠️ Failed to initialize instructor client: {e}")
else:
    client = None
    logger.warning("⚠️ No OPENAI_API_KEY found, instructor unavailable")

class ConceptNoteStructure(BaseModel):
    """Pydantic model for structured concept note output"""
    concept_name: str = Field(..., description="The financial concept name")
    definition: str = Field(..., description="Clear, concise definition (2-3 sentences)")
    formula: Optional[str] = Field(None, description="Mathematical formula with proper notation, or None")
    example: str = Field(..., description="Practical example with numerical calculations")
    applications: List[str] = Field(..., description="3-5 real-world applications", min_items=3, max_items=5)

def generate_concept_note(concept: str, context_chunks: List[Dict], source: str) -> Dict[str, Any]:
    """Generate structured concept note using Instructor + GPT-4o-mini"""
    
    if not client or not OPENAI_KEY:
        logger.info(f"📝 Using structured fallback for: {concept}")
        return generate_structured_fallback(concept, context_chunks, source)
    
    # Prepare context from chunks
    # ✅ FIX: Use P1's field names ('text' not 'content', 'page' not 'page_num')
    context = "\n\n".join([
        f"[Page {chunk.get('page', chunk.get('page_num', 'N/A'))}]: {chunk.get('text', chunk.get('content', ''))[:600]}"
        for chunk in context_chunks[:3]
    ])
    
    source_label = "Financial Toolbox PDF (fintbx.pdf)" if source == "fintbx.pdf" else "Wikipedia"
    
    system_prompt = f"""You are an expert financial educator creating concept notes for students.

Context from {source_label}:
{context}

Create a comprehensive, educational concept note that:
1. Provides a clear, accurate definition (2-3 sentences)
2. Includes the mathematical formula with proper notation (if applicable)
3. Gives a practical numerical example with step-by-step calculations
4. Lists 3-5 real-world applications in finance/investing

Be precise, professional, and educational."""
    
    try:
        logger.info(f"🤖 Generating concept with Instructor: {concept}")
        
        response: ConceptNoteStructure = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=ConceptNoteStructure,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a comprehensive concept note for: {concept}"}
            ],
            temperature=0.2,
            max_tokens=1200
        )
        
        # Extract PDF references using P1's 'page' field
        pdf_refs = []
        if source == "fintbx.pdf":
            for chunk in context_chunks:
                page = chunk.get('page') or chunk.get('page_num')
                if page:
                    try:
                        page_int = int(float(page))
                        if page_int not in pdf_refs and page_int > 0:
                            pdf_refs.append(page_int)
                    except:
                        pass
            pdf_refs.sort()
        
        # ✅ CRITICAL FIX: Use input 'concept' parameter, NOT AI-generated response.concept_name
        result = {
            "concept_name": concept,  # ✅ Use what user queried
            "definition": response.definition,
            "formula": response.formula,
            "example": response.example,
            "applications": response.applications,
            "source": source,
            "pdf_references": pdf_refs
        }
        
        logger.info(f"✅ Successfully generated: {concept}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Instructor error for {concept}: {e}")
        return generate_structured_fallback(concept, context_chunks, source)

def generate_structured_fallback(concept: str, context_chunks: List[Dict], source: str) -> Dict[str, Any]:
    """Fallback structured generation without LLM"""
    
    formulas = {
        "duration": "Modified Duration = Macaulay Duration / (1 + YTM/n)",
        "sharpe ratio": "Sharpe Ratio = (Rp - Rf) / σp", 
        "beta": "β = Cov(Ra, Rm) / Var(Rm)",
        "var": "VaR = μ - ασ",
        "value at risk": "VaR = μ - ασ",
        "alpha": "α = Rp - [Rf + β(Rm - Rf)]",
        "capm": "Ra = Rf + βa(Rm - Rf)",
        "treynor ratio": "Treynor Ratio = (Rp - Rf) / β",
        "sortino ratio": "Sortino Ratio = (Rp - Rf) / σd"
    }
    
    concept_lower = concept.lower()
    
    if source == "fintbx.pdf":
        # Use P1's 'text' field
        if context_chunks and (context_chunks[0].get("text") or context_chunks[0].get("content")):
            definition = (context_chunks[0].get("text") or context_chunks[0].get("content", ""))[:350].strip()
            if not definition.endswith('.'):
                definition += "."
        else:
            definition = f"{concept} is a key financial metric."
        
        formula = formulas.get(concept_lower)
        
        applications = [
            "Portfolio risk management",
            "Investment performance evaluation",
            "Quantitative financial analysis",
            "Risk-adjusted returns assessment"
        ]
        
        # Extract pages using P1's 'page' field
        pdf_refs = []
        for chunk in context_chunks:
            page = chunk.get('page') or chunk.get('page_num')
            if page:
                try:
                    page_int = int(float(page))
                    if page_int not in pdf_refs:
                        pdf_refs.append(page_int)
                except:
                    pass
        pdf_refs.sort()
        
        example = f"For example, when analyzing {concept}, professionals consider market data and risk factors."
        
    else:  # Wikipedia
        if context_chunks and (context_chunks[0].get("text") or context_chunks[0].get("content")):
            wiki_content = context_chunks[0].get("text") or context_chunks[0].get("content", "")
            definition = f"{concept}: {wiki_content[:300].strip()}..."
        else:
            definition = f"{concept} is a concept in business and economics."
        
        formula = formulas.get(concept_lower)
        applications = ["Business analysis", "Economic research", "Financial applications"]
        pdf_refs = []
        example = f"In practice, {concept} is applied in various contexts."
    
    return {
        "concept_name": concept,  # ✅ Always use input parameter
        "definition": definition,
        "formula": formula,
        "example": example,
        "applications": applications,
        "source": source,
        "pdf_references": pdf_refs
    }
