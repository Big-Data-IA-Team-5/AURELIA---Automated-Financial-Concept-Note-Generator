import chromadb
from chromadb.config import Settings
import openai
from typing import List, Dict
import os

class VectorRetrievalService:
    def __init__(self):
        # Initialize ChromaDB (simpler than Pinecone for quick implementation)
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))
        self.collection_name = "aurelia_financial"
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def get_or_create_collection(self):
        try:
            collection = self.client.get_collection(self.collection_name)
        except:
            collection = self.client.create_collection(self.collection_name)
        return collection
    
    def add_documents(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add documents to vector store"""
        collection = self.get_or_create_collection()
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search_similar(self, query: str, n_results: int = 5) -> Dict:
        """Search for similar chunks"""
        collection = self.get_or_create_collection()
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'][0]:
            return {
                "chunks": [],
                "scores": [],
                "total_found": 0
            }
        
        chunks = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i] if results['distances'] else 1.0
            score = 1 - distance  # Convert distance to similarity score
            
            chunks.append({
                "content": doc,
                "metadata": metadata,
                "score": score,
                "page_num": metadata.get('page_num', 'unknown')
            })
        
        return {
            "chunks": chunks,
            "scores": [chunk["score"] for chunk in chunks],
            "total_found": len(chunks)
        }

# Global instance
retrieval_service = VectorRetrievalService()