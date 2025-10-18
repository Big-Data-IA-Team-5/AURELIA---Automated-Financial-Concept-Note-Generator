# pipeline/chunkers/chunker.py
"""
Document Chunker module using LangChain
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunk documents using LangChain's RecursiveCharacterTextSplitter"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda x: len(self.encoding.encode(x)),
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.chunks = []
        
    def chunk_documents(self, parsed_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk parsed document content
        """
        logger.info(f"Starting chunking with size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        for page_data in parsed_content:
            page_num = page_data['page']
            text = page_data['text']
            
            # Split text into chunks
            page_chunks = self.text_splitter.split_text(text)
            
            # Create chunk objects with metadata
            for chunk_index, chunk_text in enumerate(page_chunks):
                chunk_obj = {
                    'text': chunk_text,
                    'page': page_num,
                    'chunk_index': chunk_index,
                    'chunk_size': len(chunk_text),
                    'token_count': len(self.encoding.encode(chunk_text)),
                    'metadata': {
                        'source': page_data.get('source', 'fintbx.pdf'),
                        'page': page_num,
                        'chunk_id': f"page_{page_num}_chunk_{chunk_index}"
                    }
                }
                self.chunks.append(chunk_obj)
        
        logger.info(f"Created {len(self.chunks)} chunks from {len(parsed_content)} pages")
        return self.chunks
    
    def save_chunks(self, output_path: str = "data/processed/chunks.json"):
        """Save chunks to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.chunks)} chunks to {output_file}")
        return output_file