from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import List, Dict, Any, Tuple
import time
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

sys.path.append(os.path.dirname(__file__))
from models.concept_note import ConceptNote, ConceptNoteCRUD, get_db, init_db

try:
    from config.shared import GOOGLE_AI_KEY, PROJECT_ID
    logger.info(f"✅ Config loaded: {PROJECT_ID}")
except ImportError:
    GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY")

try:
    from services.instructor_service import generate_concept_note
    INSTRUCTOR_AVAILABLE = True
    logger.info("✅ Instructor available")
except Exception as e:
    INSTRUCTOR_AVAILABLE = False
    logger.warning(f"⚠️ Instructor unavailable: {e}")

try:
    from services.retrieval_service import retrieval_service
    VECTOR_SERVICE_AVAILABLE = True
    count = retrieval_service.count()
    logger.info(f"✅ Pinecone: {count} vectors")
except Exception as e:
    VECTOR_SERVICE_AVAILABLE = False
    logger.warning(f"⚠️ Pinecone unavailable: {e}")

try:
    from services.wikipedia_service import get_wikipedia_content
    WIKIPEDIA_AVAILABLE = True
    logger.info("✅ Wikipedia available")
except:
    WIKIPEDIA_AVAILABLE = False

# ✅ SMART AI-POWERED RELEVANCE CHECK
def check_finance_relevance_with_ai(concept: str) -> Tuple[bool, str]:
    """Use GPT-4o-mini to intelligently determine if concept is finance-related"""
    try:
        from openai import OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_key:
            return True, "AI check unavailable"
        
        client = OpenAI(api_key=openai_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a finance expert. Determine if the given term is related to finance, economics, investing, accounting, or business. Answer ONLY with 'YES' or 'NO' followed by a one-sentence reason."
                },
                {
                    "role": "user",
                    "content": f"Is '{concept}' a finance/economics/business/investing concept?"
                }
            ],
            temperature=0.0,
            max_tokens=30
        )
        
        answer = response.choices[0].message.content.strip()
        
        if answer.upper().startswith("YES"):
            return True, answer
        elif answer.upper().startswith("NO"):
            return False, answer
        else:
            return True, "Uncertain"
            
    except Exception as e:
        logger.warning(f"Relevance check error: {e}")
        return True, "Check failed"

app = FastAPI(title="AURELIA API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics = {
    "start_time": datetime.utcnow(),
    "total_queries": 0,
    "cache_hits": 0,
    "total_response_time": 0.0,
    "instructor_calls": 0,
    "pinecone_queries": 0,
    "wikipedia_fallbacks": 0,
    "rejected_queries": 0
}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AURELIA v2.0.0 - Final")
    init_db()

@app.get("/")
async def root():
    return {
        "service": "AURELIA API",
        "version": "2.0.0",
        "status": "operational",
        "features": ["AI Relevance Check", "PDF Citations", "Instructor", "Pinecone RAG"]
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    pinecone_status = "not available"
    if VECTOR_SERVICE_AVAILABLE:
        try:
            count = retrieval_service.count()
            pinecone_status = f"healthy ({count} vectors from fintbx.pdf)"
        except Exception as e:
            pinecone_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database_status": db_status,
        "pinecone_status": pinecone_status,
        "ai_models": {
            "instructor": "available" if INSTRUCTOR_AVAILABLE else "unavailable"
        },
        "version": "2.0.0"
    }

@app.get("/concepts")
async def list_concepts(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Get all cached concepts"""
    try:
        concepts = ConceptNoteCRUD.get_all_concepts(db, limit=limit)
        return [concept.to_dict() for concept in concepts]
    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    uptime = (datetime.utcnow() - metrics["start_time"]).total_seconds()
    cache_rate = (metrics["cache_hits"] / max(metrics["total_queries"], 1)) * 100
    
    return {
        "uptime_seconds": uptime,
        "total_queries": metrics["total_queries"],
        "cache_hit_rate": cache_rate,
        "instructor_calls": metrics["instructor_calls"],
        "pinecone_queries": metrics["pinecone_queries"],
        "wikipedia_fallbacks": metrics["wikipedia_fallbacks"],
        "rejected_queries": metrics["rejected_queries"]
    }

def retrieve_for_concept(concept: str):
    """Retrieve from Pinecone"""
    if not VECTOR_SERVICE_AVAILABLE:
        return {"chunks": [], "scores": [], "total_found": 0}
    
    try:
        result = retrieval_service.search_similar(concept, n_results=5)
        chunks = result.get("chunks", [])
        scores = [c.get("score", 0) for c in chunks]
        logger.info(f"🔍 Pinecone: {len(chunks)} chunks (scores: {[f'{s:.3f}' for s in scores[:3]]})")
        return result
    except Exception as e:
        logger.error(f"Pinecone error: {e}")
        return {"chunks": [], "scores": [], "total_found": 0}

@app.post("/query")
async def query_concept(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Generate concept note with AI relevance check and PDF citations"""
    start_time = time.time()
    metrics["total_queries"] += 1
    
    concept = request.get("concept", "").strip()
    force_refresh = request.get("force_refresh", False)
    
    if not concept:
        raise HTTPException(status_code=400, detail="Concept required")
    
    try:
        cached = ConceptNoteCRUD.get_concept(db, concept)
        
        if cached and not force_refresh:
            metrics["cache_hits"] += 1
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "concept_note": cached.to_dict(),
                "cached": True,
                "processing_time_ms": processing_time,
                "source": cached.source if hasattr(cached, 'source') else 'unknown',
                "ai_model": "cached",
                "pdf_pages": cached.pdf_references if hasattr(cached, 'pdf_references') else []
            }
        
        retrieval_result = retrieve_for_concept(concept)
        chunks = retrieval_result.get("chunks", [])
        max_score = max([c.get("score", 0) for c in chunks]) if chunks else 0
        
        use_fallback = max_score < 0.3
        
        if use_fallback:
            is_finance, reason = check_finance_relevance_with_ai(concept)
            
            if not is_finance:
                metrics["rejected_queries"] += 1
                logger.warning(f"🚫 Rejected: '{concept}' - {reason}")
                raise HTTPException(
                    status_code=400,
                    detail=f"This query doesn't appear to be finance-related. {reason}. Please enter a financial concept."
                )
            
            if WIKIPEDIA_AVAILABLE:
                metrics["wikipedia_fallbacks"] += 1
                logger.info(f"🌐 Wikipedia: {concept} (finance, not in PDF)")
                wiki_content = get_wikipedia_content(concept)
                chunks = [{"content": wiki_content, "page": "Wikipedia", "score": 1.0}]
                source = "wikipedia"
            else:
                raise HTTPException(status_code=404, detail="Not found")
        else:
            source = "fintbx.pdf"
            logger.info(f"📊 fintbx.pdf: '{concept}' (score: {max_score:.3f})")
        
        # ✅ FIX: Extract pages using P1's field name 'page' (not 'page_num')
        pdf_pages = []
        if source == "fintbx.pdf" and chunks:
            for chunk in chunks:
                # P1 uses 'page' field (float like 1851.0)
                page = chunk.get('page') or chunk.get('page_num')
                if not page and 'metadata' in chunk:
                    page = chunk['metadata'].get('page') or chunk['metadata'].get('page_num')
                
                if page:
                    try:
                        page_int = int(float(page))  # Convert 1851.0 to 1851
                        if page_int not in pdf_pages and page_int > 0:
                            pdf_pages.append(page_int)
                    except (ValueError, TypeError):
                        pass
            
            pdf_pages.sort()
            logger.info(f"📄 Pages: {pdf_pages}")
        
        if INSTRUCTOR_AVAILABLE:
            metrics["instructor_calls"] += 1
            concept_note = generate_concept_note(concept, chunks, source)
            ai_model = "gpt-4o-mini (instructor)"
        else:
            concept_note = {
                "concept_name": concept,
                "definition": f"{concept} is a financial concept.",
                "formula": None,
                "example": f"Example for {concept}",
                "applications": ["Financial analysis"],
                "source": source
            }
            ai_model = "fallback"
        
        # Add PDF references
        if source == "fintbx.pdf":
            concept_note['pdf_references'] = pdf_pages
        
        existing = ConceptNoteCRUD.get_concept(db, concept)
        
        if existing:
            for key, value in concept_note.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            saved = existing
        else:
            saved = ConceptNoteCRUD.create_concept(db, concept_note)
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "concept_note": saved.to_dict(),
            "cached": False,
            "processing_time_ms": processing_time,
            "chunks_retrieved": len(chunks),
            "source": source,
            "ai_model": ai_model,
            "pdf_pages": pdf_pages if source == "fintbx.pdf" else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/seed")
async def seed_concepts(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Seed from fintbx.pdf only - skip if not found"""
    concepts = request.get("concepts", [])
    if not concepts:
        raise HTTPException(status_code=400, detail="Concepts required")
    
    results = []
    successful = 0
    skipped = 0
    
    for concept in concepts:
        try:
            retrieval_result = retrieve_for_concept(concept)
            chunks = retrieval_result.get("chunks", [])
            max_score = max([c.get("score", 0) for c in chunks]) if chunks else 0
            
            if max_score < 0.3:
                logger.info(f"⏭️ Skipping '{concept}' (score: {max_score:.3f})")
                results.append({
                    "concept": concept,
                    "success": False,
                    "skipped": True,
                    "reason": f"Not found in PDF"
                })
                skipped += 1
                continue
            
            # ✅ FIX: Extract pages using P1's 'page' field
            pdf_pages = []
            for chunk in chunks:
                page = chunk.get('page') or chunk.get('page_num')
                if not page and 'metadata' in chunk:
                    page = chunk['metadata'].get('page') or chunk['metadata'].get('page_num')
                
                if page:
                    try:
                        page_int = int(float(page))
                        if page_int not in pdf_pages and page_int > 0:
                            pdf_pages.append(page_int)
                    except:
                        pass
            
            pdf_pages.sort()
            
            if INSTRUCTOR_AVAILABLE:
                concept_note = generate_concept_note(concept, chunks, "fintbx.pdf")
            else:
                concept_note = {"concept_name": concept, "source": "fintbx.pdf"}
            
            concept_note['pdf_references'] = pdf_pages
            
            existing = ConceptNoteCRUD.get_concept(db, concept)
            if existing:
                for key, value in concept_note.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                db.commit()
                saved = existing
            else:
                saved = ConceptNoteCRUD.create_concept(db, concept_note)
            
            results.append({
                "concept": concept,
                "success": True,
                "source": "fintbx.pdf",
                "pages": pdf_pages
            })
            successful += 1
            
        except Exception as e:
            logger.error(f"Error: {e}")
            results.append({"concept": concept, "success": False, "error": str(e)})
    
    return {
        "results": results,
        "total": len(concepts),
        "successful": successful,
        "skipped": skipped
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
