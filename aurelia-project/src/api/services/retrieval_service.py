from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone
    from openai import OpenAI
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    logger.warning("⚠️ Pinecone or OpenAI not installed")

class VectorRetrievalService:
    """Uses OpenAI text-embedding-3-large (3072D) to match P1's vectors"""
    
    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
            logger.info("✅ OpenAI embeddings: text-embedding-3-large (3072D)")
        else:
            self.openai_client = None
            logger.error("❌ OPENAI_API_KEY not found")
        
        self.pinecone_client = None
        self.pinecone_index = None
        self.use_pinecone = False
        self._init_pinecone()
    
    def _init_pinecone(self):
        if not DEPS_AVAILABLE or not self.openai_client:
            return
        
        api_key = os.getenv("PINECONE_API_KEY") or os.getenv("PINECONE_KEY")
        if not api_key:
            logger.error("❌ PINECONE_API_KEY not found")
            return
        
        try:
            self.pinecone_client = Pinecone(api_key=api_key)
            index_name = os.getenv("PINECONE_INDEX", "aurelia-fintbx")
            self.pinecone_index = self.pinecone_client.Index(index_name)
            
            stats = self.pinecone_index.describe_index_stats()
            count = stats.get('total_vector_count', 0)
            dim = stats.get('dimension', 0)
            logger.info(f"✅ P1's Pinecone: {count} vectors ({dim}D)")
            self.use_pinecone = True
        except Exception as e:
            logger.error(f"❌ Pinecone error: {e}")
            self.use_pinecone = False
    
    def search_similar(self, query: str, n_results: int = 5) -> Dict:
        if not self.use_pinecone or not self.openai_client:
            return {"chunks": [], "scores": [], "total_found": 0}
        
        try:
            # Use OpenAI text-embedding-3-large (MATCHES P1's 3072D!)
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=query
            )
            embedding = response.data[0].embedding
            
            results = self.pinecone_index.query(
                vector=embedding,
                top_k=n_results,
                include_metadata=True
            )
            
            chunks = []
            for match in results.get('matches', []):
                metadata = match.get('metadata', {})
                chunks.append({
                    "content": metadata.get('text', ''),
                    "page_num": int(metadata.get('page', 0)),
                    "score": match.get('score', 0.0),
                    "metadata": {"page_num": int(metadata.get('page', 0)), "source": "fintbx.pdf"}
                })
            
            scores = [c['score'] for c in chunks[:3]]
            logger.info(f"🔍 Pinecone (3072D): {len(chunks)} chunks (scores: {[f'{s:.3f}' for s in scores]})")
            return {"chunks": chunks, "scores": [c["score"] for c in chunks], "total_found": len(chunks)}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"chunks": [], "scores": [], "total_found": 0}
    
    @property
    def collection(self):
        return self
    
    def count(self):
        if self.use_pinecone and self.pinecone_index:
            try:
                return self.pinecone_index.describe_index_stats().get('total_vector_count', 0)
            except:
                return 0
        return 0

retrieval_service = VectorRetrievalService()



