"""
Retriever for Financial Documents
Unified interface for querying vector stores (Pinecone/ChromaDB).
This is what P2 will use in the API!
"""
import logging
from typing import List, Dict, Any, Optional

from config.shared import VECTOR_STORE_TYPE, TOP_K_RESULTS, SIMILARITY_THRESHOLD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """
    Unified retriever interface for vector stores.
    P2 uses this to search for relevant chunks.
    """
    
    def __init__(self, store_type: str = None, top_k: int = None):
        """
        Initialize retriever with specified vector store.
        
        Args:
            store_type: "pinecone" or "chroma" (defaults to config)
            top_k: Number of results to return (defaults to config)
        """
        self.store_type = store_type or VECTOR_STORE_TYPE
        self.top_k = top_k or TOP_K_RESULTS
        
        # Initialize vector store based on type
        if self.store_type == "pinecone":
            from src.pipeline.vectorstore.pinecone_store import PineconeStore
            self.store = PineconeStore()
            logger.info("Initialized Pinecone retriever")
        elif self.store_type == "chroma":
            from src.pipeline.vectorstore.chroma_store import ChromaStore
            self.store = ChromaStore()
            logger.info("Initialized ChromaDB retriever")
        else:
            raise ValueError(f"Unknown vector store type: {self.store_type}")
        
        # Initialize embedder for query embedding
        from src.pipeline.embeddings.embedder import FinancialEmbedder
        self.embedder = FinancialEmbedder()
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for relevant chunks based on query text.
        
        THIS IS THE MAIN METHOD P2 WILL USE!
        
        Args:
            query_text: User's question or search query
            top_k: Number of results to return (overrides default)
            filter_metadata: Filter by metadata (e.g., {'page': 5, 'chunk_type': 'table'})
            min_score: Minimum similarity score (0 to 1)
            
        Returns:
            List of relevant chunks with scores, sorted by relevance:
            [
                {
                    'chunk_id': 'chunk_00042',
                    'text': 'Duration is a measure...',
                    'score': 0.89,
                    'page': 25,
                    'section': 'Chapter 3: Bond Analysis',
                    'chunk_type': 'text',
                    'metadata': {...}
                },
                ...
            ]
        """
        logger.info(f"Query: '{query_text}'")
        
        # 1. Convert query to embedding
        query_embedding = self.embedder.embed_query(query_text)
        
        # 2. Search vector store
        k = top_k or self.top_k
        results = self.store.query(
            query_embedding=query_embedding,
            top_k=k,
            filter_dict=filter_metadata
        )
        
        # 3. Filter by minimum score if specified
        min_score = min_score or SIMILARITY_THRESHOLD
        filtered_results = [
            result for result in results
            if result['score'] >= min_score
        ]
        
        logger.info(f"Found {len(filtered_results)} results above threshold {min_score}")
        
        return filtered_results
    
    def query_with_context(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        include_surrounding: bool = False
    ) -> Dict[str, Any]:
        """
        Query with additional context and metadata.
        Useful for generating better answers.
        
        Args:
            query_text: User's question
            top_k: Number of results
            include_surrounding: If True, include chunks before/after
            
        Returns:
            {
                'query': 'What is duration?',
                'results': [...],
                'context': 'Combined text from top results',
                'sources': ['Page 25', 'Page 26'],
                'total_results': 5
            }
        """
        results = self.query(query_text, top_k=top_k)
        
        if not results:
            return {
                'query': query_text,
                'results': [],
                'context': '',
                'sources': [],
                'total_results': 0
            }
        
        # Combine text from top results
        context_texts = []
        sources = set()
        
        for result in results:
            context_texts.append(result['text'])
            sources.add(f"Page {result['page']}")
        
        combined_context = "\n\n".join(context_texts)
        
        return {
            'query': query_text,
            'results': results,
            'context': combined_context,
            'sources': sorted(list(sources)),
            'total_results': len(results)
        }
    
    def get_by_page(self, page_num: int, top_k: int = 10) -> List[Dict]:
        """
        Retrieve all chunks from a specific page.
        
        Args:
            page_num: Page number
            top_k: Max results to return
            
        Returns:
            List of chunks from that page
        """
        # Query with page filter
        dummy_query = "financial document"  # Generic query
        results = self.query(
            query_text=dummy_query,
            top_k=top_k,
            filter_metadata={'page': page_num}
        )
        
        return results
    
    def get_by_section(self, section_name: str, top_k: int = 10) -> List[Dict]:
        """
        Retrieve chunks from a specific section.
        
        Args:
            section_name: Section title (e.g., "Chapter 3: Duration")
            top_k: Max results to return
            
        Returns:
            List of chunks from that section
        """
        results = self.query(
            query_text=section_name,
            top_k=top_k
        )
        
        # Filter by section in metadata
        section_results = [
            r for r in results
            if section_name.lower() in r.get('section', '').lower()
        ]
        
        return section_results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        Useful for monitoring and evaluation.
        
        Returns:
            Dictionary with store statistics
        """
        return self.store.get_stats()


def main():
    """Test the retriever - THIS IS WHAT P2 WILL DO!"""
    
    print("="*50)
    print("Testing Retriever (P2's Interface)")
    print("="*50)
    print()
    
    # Initialize retriever
    retriever = Retriever()
    
    # Get stats
    stats = retriever.get_stats()
    print(f"Vector Store Stats:")
    print(f"  Total chunks: {stats.get('total_vector_count', 0)}")
    print(f"  Dimension: {stats.get('dimension', 0)}")
    print()
    
    # Test queries (simulating what P2's API will do)
    test_queries = [
        "What is duration in bond analysis?",
        "How to calculate Black-Scholes?",
        "Sharpe ratio formula",
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 50)
        
        # Basic query
        results = retriever.query(query, top_k=3)
        
        if results:
            for idx, result in enumerate(results, 1):
                print(f"{idx}. Score: {result['score']:.4f} | Page: {result['page']}")
                print(f"   {result['text'][:150]}...")
                print()
        else:
            print("   No results found!")
            print()
    
    # Test context query
    print("\n" + "="*50)
    print("Testing Context Query")
    print("="*50)
    
    context_result = retriever.query_with_context(
        "Explain duration with examples",
        top_k=5
    )
    
    print(f"Query: {context_result['query']}")
    print(f"Total results: {context_result['total_results']}")
    print(f"Sources: {', '.join(context_result['sources'])}")
    print(f"\nCombined Context ({len(context_result['context'])} chars):")
    print(context_result['context'][:500] + "...")
    
    print("\n" + "="*50)
    print("Retriever test complete!")
    print("P2 can now use this interface in the API!")
    print("="*50)


if __name__ == "__main__":
    main()