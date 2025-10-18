# pipeline/vectorstore/chroma_store.py
"""
ChromaDB Vector Store module
"""

import chromadb
from chromadb.config import Settings
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaStore:
    """ChromaDB vector store for embeddings"""
    
    def __init__(self, persist_directory: str = "./data/chromadb", collection_name: str = "financial-toolbox-full"):
        """
        Initialize ChromaDB client and collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = None
        self.initialize_collection()
        
    def initialize_collection(self):
        """Initialize or get existing collection"""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except:
            # Create new collection if doesn't exist
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_embeddings(self, embeddings_data: List[Dict[str, Any]], batch_size: int = 100):
        """
        Add embeddings to ChromaDB
        """
        logger.info(f"Adding {len(embeddings_data)} embeddings to ChromaDB")
        
        # Process in batches
        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i:i + batch_size]
            
            # Prepare batch data
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for j, item in enumerate(batch):
                documents.append(item['text'])
                embeddings.append(item['embedding'])
                
                # Prepare metadata
                metadata = item.get('metadata', {})
                metadata['page'] = item.get('page', 0)
                metadata['chunk_index'] = item.get('chunk_index', 0)
                metadatas.append(metadata)
                
                # Create unique ID
                ids.append(f"doc_{i+j}")
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{(len(embeddings_data) + batch_size - 1)//batch_size}")
        
        logger.info(f"Successfully added all embeddings to ChromaDB")
    
    def query(self, query_text: str = None, query_embedding: List[float] = None, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the vector store
        """
        if query_text:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        elif query_embedding:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        else:
            raise ValueError("Either query_text or query_embedding must be provided")
        
        # Format results
        if results and results['documents'] and results['documents'][0]:
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'found': True
            }
        return {'found': False}
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        count = self.collection.count()
        return {
            'name': self.collection_name,
            'count': count,
            'persist_directory': self.persist_directory
        }