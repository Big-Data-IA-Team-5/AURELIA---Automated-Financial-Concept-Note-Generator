"""
Instructor service using Google Gemini for structured concept note generation
"""

import json
import google.generativeai as genai
from typing import List, Dict
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from config.shared import GOOGLE_AI_KEY

# Configure Gemini
genai.configure(api_key=GOOGLE_AI_KEY)


def generate_concept_note(
    concept: str, 
    chunks: List[dict],  # Changed to match your retrieval service format
    source: str = "fintbx"
) -> Dict:
    """
    Generate structured concept note using Google Gemini
    
    Args:
        concept: The financial concept name
        chunks: List of chunks from retrieval_service with content, metadata, score
        source: Source of information ('fintbx' or 'wikipedia')
    
    Returns:
        Dictionary with concept note data
    """
    
    # Combine chunks into context (matches your retrieval service format)
    if chunks:
        context = "\n\n".join([
            f"[Page {chunk.get('page_num', chunk.get('metadata', {}).get('page_num', 'N/A'))}]: {chunk.get('content', '')}" 
            for chunk in chunks
        ])
    else:
        context = "No specific context available."
    
    # Create detailed prompt for Gemini
    prompt = f"""You are a financial education expert. Generate a comprehensive concept note for the following financial concept.

**Concept:** {concept}

**Context:**
{context}

**Instructions:**
1. Provide a clear, accurate definition (2-3 sentences)
2. Include the mathematical formula if applicable (use proper notation)
3. Give a practical numerical example with calculations
4. List 3-5 real-world applications
5. Provide 3-5 key points students should remember

**Output as JSON with this exact structure:**
{{
    "concept_name": "{concept}",
    "definition": "clear definition here",
    "formula": "mathematical formula or null if not applicable",
    "example": "detailed example with numbers and calculations",
    "applications": ["application 1", "application 2", "application 3"],
    "key_points": ["point 1", "point 2", "point 3"]
}}

**Important:** 
- Return ONLY valid JSON, no markdown formatting
- Be accurate and educational
- Use the provided context when available
- If no formula exists, use null for formula field
"""

    try:
        # Use Gemini Flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate response
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        # Parse JSON
        concept_data = json.loads(response_text)
        
        # Add metadata
        concept_data['source'] = source
        concept_data['chunks_used'] = len(chunks)
        concept_data['model'] = 'gemini-1.5-flash'
        
        # Add PDF references if from fintbx
        if source == "fintbx" and chunks:
            concept_data['pdf_references'] = [
                chunk.get('page_num', chunk.get('metadata', {}).get('page_num', 'N/A')) 
                for chunk in chunks
            ]
        else:
            concept_data['pdf_references'] = None
        
        print(f"✅ Successfully generated concept note for: {concept}")
        return concept_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response text: {response_text[:500]}")
        
        return {
            "concept_name": concept,
            "definition": f"A financial concept related to {concept}.",
            "formula": None,
            "example": "Please try again.",
            "applications": ["Financial analysis", "Risk management"],
            "key_points": ["Important financial concept"],
            "source": source,
            "pdf_references": None,
            "error": str(e)
        }
    
    except Exception as e:
        print(f"❌ Error generating concept note: {e}")
        return {
            "concept_name": concept,
            "definition": f"Error: {str(e)}",
            "formula": None,
            "example": "N/A",
            "applications": ["N/A"],
            "key_points": ["Error occurred"],
            "source": source,
            "pdf_references": None,
            "error": str(e)
        }


if __name__ == "__main__":
    print("Testing Instructor Service with Google Gemini...")
    print("=" * 50)
    
    test_chunks = [
        {
            "content": "Duration is a measure of the sensitivity of the price of a bond to a change in interest rates.",
            "page_num": 42,
            "score": 0.85,
            "metadata": {"page_num": 42, "source": "fintbx"}
        }
    ]
    
    result = generate_concept_note("Duration", test_chunks, "fintbx")
    print(json.dumps(result, indent=2))