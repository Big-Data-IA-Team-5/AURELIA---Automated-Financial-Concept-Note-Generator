import time
import random

def retrieve_for_concept(concept: str, vector_store="pinecone"):
    """Mock P1's retrieval function for testing"""
    
    # Simulate processing time
    time.sleep(0.1)
    
    # Mock retrieval results with varying scores
    if concept.lower() in ["duration", "sharpe ratio", "beta", "alpha"]:
        # High score for "known" financial concepts
        score = random.uniform(0.75, 0.95)
        chunks = [
            {
                "content": f"Financial concept: {concept} is a key metric used in quantitative finance for measuring risk and return characteristics.",
                "page_num": random.randint(1, 50),
                "score": score,
                "chunk_id": f"chunk_{random.randint(1000, 9999)}"
            },
            {
                "content": f"In practice, {concept} is calculated using specific formulas and is widely applied in portfolio management and risk assessment.",
                "page_num": random.randint(1, 50), 
                "score": score - 0.05,
                "chunk_id": f"chunk_{random.randint(1000, 9999)}"
            }
        ]
    else:
        # Low score for unknown concepts (triggers Wikipedia fallback)
        score = random.uniform(0.3, 0.6)
        chunks = [
            {
                "content": f"Limited information found about {concept} in the financial database.",
                "page_num": random.randint(1, 50),
                "score": score,
                "chunk_id": f"chunk_{random.randint(1000, 9999)}"
            }
        ]
    
    return {
        "chunks": chunks,
        "vector_store": vector_store,
        "retrieval_time_ms": random.uniform(80, 150),
        "query": concept,
        "total_chunks_available": random.randint(800, 1200)
    }