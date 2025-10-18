# pipeline/embeddings/embedder.py
"""
Embeddings Generator module
"""

from sentence_transformers import SentenceTransformer
from openai import OpenAI
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    """Generate embeddings using Sentence Transformers or OpenAI"""
    
    def __init__(self, model_type: str = "sentence-transformers", model_name: str = None):
        """
        Initialize embedder
        """
        self.model_type = model_type
        self.embeddings = []
        
        if model_type == "sentence-transformers":
            self.model_name = model_name or "all-MiniLM-L6-v2"
            logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
        elif model_type == "openai":
            self.model_name = model_name or "text-embedding-3-large"
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.embedding_dim = 3072 if "3-large" in self.model_name else 1536
            logger.info(f"Using OpenAI embeddings model: {self.model_name}")
        
    def generate_embeddings(self, chunks: List[Dict[str, Any]], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks
        """
        texts = [chunk['text'] for chunk in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks")
        
        if self.model_type == "sentence-transformers":
            # Process in batches for efficiency
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = chunks[i:i + batch_size]
                
                # Generate embeddings
                batch_embeddings = self.model.encode(batch_texts, show_progress_bar=True)
                
                # Create embedding objects
                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    self.embeddings.append({
                        'text': chunk['text'],
                        'embedding': embedding.tolist(),
                        'metadata': chunk.get('metadata', {}),
                        'page': chunk.get('page'),
                        'chunk_index': chunk.get('chunk_index')
                    })
                    
        elif self.model_type == "openai":
            # Process with OpenAI API
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = chunks[i:i + batch_size]
                
                try:
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch_texts
                    )
                    
                    for chunk, embedding_obj in zip(batch_chunks, response.data):
                        self.embeddings.append({
                            'text': chunk['text'],
                            'embedding': embedding_obj.embedding,
                            'metadata': chunk.get('metadata', {}),
                            'page': chunk.get('page'),
                            'chunk_index': chunk.get('chunk_index')
                        })
                except Exception as e:
                    logger.error(f"Error generating OpenAI embeddings: {e}")
                    
        logger.info(f"Generated {len(self.embeddings)} embeddings")
        return self.embeddings
    
    def save_embeddings(self, output_path: str = "data/processed/embeddings.json"):
        """Save embeddings to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.embeddings, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.embeddings)} embeddings to {output_file}")
        return output_file