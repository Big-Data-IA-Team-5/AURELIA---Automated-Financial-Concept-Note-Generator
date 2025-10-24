"""
Pinecone Vector Store for Financial Documents
Stores and manages embeddings in Pinecone cloud vector database.
"""
import logging
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

from config.shared import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME,
    EMBEDDING_DIMENSION
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PineconeStore:
    """
    Manages Pinecone vector store for embeddings.
    Handles index creation, upserting vectors, and querying.
    """
    
    def __init__(self):
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not found in environment variables!")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = PINECONE_INDEX_NAME
        self.dimension = EMBEDDING_DIMENSION
        
        # Create or connect to index
        self._setup_index()
        
        # Get index object
        self.index = self.pc.Index(self.index_name)
        
        logger.info(f"Connected to Pinecone index: {self.index_name}")
    
    def _setup_index(self):
        """
        Create Pinecone index if it doesn't exist.
        Uses serverless spec for cost efficiency.
        """
        # Check if index exists
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name in existing_indexes:
            logger.info(f"Index '{self.index_name}' already exists")
            return
        
        # Create new index
        logger.info(f"Creating new index '{self.index_name}'...")
        
        self.pc.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric="cosine",  # Cosine similarity for text embeddings
            spec=ServerlessSpec(
                cloud="aws",  # or "gcp"
                region="us-east-1"  # Choose based on your location
            )
        )
        
        logger.info(f"Index '{self.index_name}' created successfully!")
    
    def upsert_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """
        Upload chunks with embeddings to Pinecone.
        
        Args:
            chunks: List of chunks with embeddings
            batch_size: Number of vectors to upload per batch
        """
        logger.info(f"Upserting {len(chunks)} chunks to Pinecone...")
        
        # Prepare vectors for Pinecone
        vectors = []
        for chunk in chunks:
            vector = {
                'id': chunk['chunk_id'],
                'values': chunk['embedding'],
                'metadata': {
                    'text': chunk['text'][:1000],  # Pinecone metadata limit
                    'page': chunk['metadata'].get('page', 0),
                    'chunk_type': chunk['metadata'].get('chunk_type', 'text'),
                    'strategy': chunk['metadata'].get('strategy', 'unknown'),
                    'token_count': chunk['metadata'].get('token_count', 0),
                    'section': chunk['metadata'].get('section', '')[:500] if chunk['metadata'].get('section') else ''
                }
            }
            vectors.append(vector)
        
        # Upload in batches
        for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading to Pinecone"):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
            except Exception as e:
                logger.error(f"Error upserting batch {i//batch_size}: {e}")
        
        # Wait for index to be ready
        logger.info("Waiting for index to be ready...")
        stats = self.index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
        
        logger.info(f"Successfully upserted {len(chunks)} chunks!")
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar vectors in Pinecone.
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of results to return
            filter_dict: Optional metadata filter (e.g., {'page': 5})
            
        Returns:
            List of matching chunks with scores
        """
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            matches = []
            for match in results['matches']:
                matches.append({
                    'chunk_id': match['id'],
                    'score': match['score'],
                    'text': match['metadata'].get('text', ''),
                    'page': match['metadata'].get('page', 0),
                    'chunk_type': match['metadata'].get('chunk_type', 'text'),
                    'section': match['metadata'].get('section', ''),
                    'metadata': match['metadata']
                })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            return []
    
    def delete_all(self):
        """
        Delete all vectors from the index.
        USE WITH CAUTION!
        """
        logger.warning("Deleting all vectors from index...")
        self.index.delete(delete_all=True)
        logger.info("All vectors deleted!")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the index.
        """
        stats = self.index.describe_index_stats()
        return {
            'total_vector_count': stats['total_vector_count'],
            'dimension': stats['dimension'],
            'index_fullness': stats.get('index_fullness', 0)
        }
    
    def fetch_vector(self, chunk_id: str) -> Optional[Dict]:
        """
        Fetch a specific vector by ID.
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            Vector data with metadata
        """
        try:
            result = self.index.fetch(ids=[chunk_id])
            if chunk_id in result['vectors']:
                return result['vectors'][chunk_id]
            return None
        except Exception as e:
            logger.error(f"Error fetching vector {chunk_id}: {e}")
            return None


def main():
    """Test Pinecone store."""
    from config.shared import PROCESSED_DATA_DIR
    
    # Load chunks with embeddings
    embeddings_file = PROCESSED_DATA_DIR / "embeddings" / "chunks_with_embeddings_recursive.jsonl"
    
    if not embeddings_file.exists():
        print(f"Error: {embeddings_file} not found. Run embedder.py first!")
        return
    
    chunks = []
    with open(embeddings_file, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    
    print(f"Loaded {len(chunks)} chunks with embeddings")
    
    # Initialize Pinecone store
    store = PineconeStore()
    
    # Upload chunks
    store.upsert_chunks(chunks)
    
    # Get stats
    stats = store.get_stats()
    print(f"\nPinecone Index Stats:")
    print(f"  Total vectors: {stats['total_vector_count']}")
    print(f"  Dimension: {stats['dimension']}")
    print(f"  Index fullness: {stats['index_fullness']:.2%}")
    
    # Test query
    print("\nTesting query...")
    test_embedding = chunks[0]['embedding']  # Use first chunk's embedding
    results = store.query(test_embedding, top_k=3)
    
    print(f"\nTop 3 similar chunks:")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. Score: {result['score']:.4f}, Page: {result['page']}")
        print(f"   Text: {result['text'][:100]}...")
        print()
    
    print("="*50)
    print("Pinecone store test complete!")
    print("="*50)


if __name__ == "__main__":
    main()