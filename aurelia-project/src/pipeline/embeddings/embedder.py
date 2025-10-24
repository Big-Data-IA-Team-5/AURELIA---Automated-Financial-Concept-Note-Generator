"""
Embeddings Generator for Financial Documents
Converts text chunks into vector embeddings using OpenAI's text-embedding-3-large.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import json
import time

import openai
from openai import OpenAI
import numpy as np
from tqdm import tqdm

from config.shared import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    PROCESSED_DATA_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialEmbedder:
    """
    Generate embeddings for text chunks using OpenAI's embedding model.
    Handles batching, rate limiting, and caching.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables!")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = EMBEDDING_MODEL
        self.dimension = EMBEDDING_DIMENSION
        
        # Rate limiting (OpenAI: 3,000 requests/min for tier 1)
        self.batch_size = 100  # Process 100 chunks at a time
        self.delay_between_batches = 1  # 1 second delay
        
        # Output directory
        self.output_dir = PROCESSED_DATA_DIR / "embeddings"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def embed_chunks(self, chunks: List[Dict], strategy: str = "recursive") -> List[Dict]:
        """
        Generate embeddings for all chunks.
        
        Args:
            chunks: List of chunks from chunker
            strategy: Name of chunking strategy (for saving)
            
        Returns:
            List of chunks with embeddings added
        """
        logger.info(f"Starting embedding generation for {len(chunks)} chunks")
        logger.info(f"Model: {self.model}, Dimension: {self.dimension}")
        
        # Check if embeddings already exist (caching)
        cache_file = self.output_dir / f"embeddings_{strategy}.npy"
        if cache_file.exists():
            logger.info(f"Found cached embeddings at {cache_file}")
            embeddings = np.load(cache_file)
            
            # Add embeddings to chunks
            for idx, chunk in enumerate(chunks):
                chunk['embedding'] = embeddings[idx].tolist()
            
            return chunks
        
        # Generate embeddings in batches
        all_embeddings = []
        total_tokens = 0
        
        for i in tqdm(range(0, len(chunks), self.batch_size), desc="Embedding chunks"):
            batch = chunks[i:i + self.batch_size]
            batch_texts = [chunk['text'] for chunk in batch]
            
            try:
                # Call OpenAI API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts,
                    encoding_format="float"
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Track token usage
                total_tokens += response.usage.total_tokens
                
                # Rate limiting
                if i + self.batch_size < len(chunks):
                    time.sleep(self.delay_between_batches)
                    
            except Exception as e:
                logger.error(f"Error embedding batch {i//self.batch_size}: {e}")
                # Add zero vectors for failed embeddings
                zero_embedding = [0.0] * self.dimension
                for _ in range(len(batch)):
                    all_embeddings.append(zero_embedding)
        
        # Add embeddings to chunks
        for idx, chunk in enumerate(chunks):
            chunk['embedding'] = all_embeddings[idx]
        
        # Cache embeddings
        embeddings_array = np.array(all_embeddings)
        np.save(cache_file, embeddings_array)
        logger.info(f"Saved embeddings cache to {cache_file}")
        
        # Calculate cost (OpenAI pricing: $0.13 per 1M tokens for text-embedding-3-large)
        cost = (total_tokens / 1_000_000) * 0.13
        logger.info(f"Embedding complete! Total tokens: {total_tokens:,}, Estimated cost: ${cost:.4f}")
        
        return chunks
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.
        Used by retriever for similarity search.
        
        Args:
            query: User's search query
            
        Returns:
            Embedding vector (list of floats)
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query,
                encoding_format="float"
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return [0.0] * self.dimension
    
    def save_chunks_with_embeddings(self, chunks: List[Dict], strategy: str = "recursive"):
        """
        Save chunks with embeddings to JSONL file.
        This is what gets loaded into the vector store.
        """
        output_file = self.output_dir / f"chunks_with_embeddings_{strategy}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(chunks)} chunks with embeddings to {output_file}")
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1, embedding2: Vector embeddings
            
        Returns:
            Similarity score (0 to 1, higher = more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def get_embedding_stats(self, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Calculate statistics about embeddings.
        Useful for evaluation in Lab 5.
        """
        embeddings = np.array([chunk['embedding'] for chunk in chunks])
        
        stats = {
            'num_embeddings': len(embeddings),
            'dimension': embeddings.shape[1],
            'mean_norm': float(np.mean(np.linalg.norm(embeddings, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(embeddings, axis=1))),
            'min_value': float(np.min(embeddings)),
            'max_value': float(np.max(embeddings)),
            'mean_value': float(np.mean(embeddings)),
        }
        
        logger.info("Embedding Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        return stats


def main():
    """Test the embedder."""
    from config.shared import PROCESSED_DATA_DIR
    
    # Load chunks
    chunks_file = PROCESSED_DATA_DIR / "chunks" / "chunks_recursive.jsonl"
    
    if not chunks_file.exists():
        print(f"Error: {chunks_file} not found. Run chunker.py first!")
        return
    
    chunks = []
    with open(chunks_file, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Generate embeddings
    embedder = FinancialEmbedder()
    chunks_with_embeddings = embedder.embed_chunks(chunks, strategy="recursive")
    
    # Save
    embedder.save_chunks_with_embeddings(chunks_with_embeddings, strategy="recursive")
    
    # Get stats
    stats = embedder.get_embedding_stats(chunks_with_embeddings)
    
    # Test query embedding
    query = "What is duration in bond analysis?"
    query_embedding = embedder.embed_query(query)
    print(f"\nQuery embedding dimension: {len(query_embedding)}")
    
    # Test similarity
    similarity = embedder.compute_similarity(
        query_embedding,
        chunks_with_embeddings[0]['embedding']
    )
    print(f"Similarity with first chunk: {similarity:.4f}")
    
    print("\n" + "="*50)
    print("Embedding generation complete!")
    print("="*50)


if __name__ == "__main__":
    main()