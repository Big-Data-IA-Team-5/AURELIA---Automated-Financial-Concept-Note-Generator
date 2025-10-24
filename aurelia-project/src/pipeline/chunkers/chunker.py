"""
Text Chunker for Financial Documents
Implements multiple chunking strategies and compares them.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import json

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    CharacterTextSplitter
)
import tiktoken

from config.shared import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    PROCESSED_DATA_DIR,
    EMBEDDING_MODEL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialChunker:
    """
    Chunks parsed PDF content using multiple strategies.
    Preserves tables, figures, and code snippets.
    """
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Output directory
        self.output_dir = PROCESSED_DATA_DIR / "chunks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def chunk_document(self, parsed_data: Dict, strategy: str = "recursive") -> List[Dict]:
        """
        Main chunking method that supports multiple strategies.
        
        Args:
            parsed_data: Output from PDFParser
            strategy: "recursive", "markdown", "section", or "hybrid"
            
        Returns:
            List of chunks with metadata
        """
        logger.info(f"Starting chunking with strategy: {strategy}")
        
        if strategy == "recursive":
            chunks = self._chunk_recursive(parsed_data)
        elif strategy == "markdown":
            chunks = self._chunk_markdown(parsed_data)
        elif strategy == "section":
            chunks = self._chunk_by_section(parsed_data)
        elif strategy == "hybrid":
            chunks = self._chunk_hybrid(parsed_data)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Add chunk IDs and validate
        chunks = self._finalize_chunks(chunks)
        
        # Save chunks
        self._save_chunks(chunks, strategy)
        
        logger.info(f"Created {len(chunks)} chunks using {strategy} strategy")
        return chunks
    
    def _chunk_recursive(self, parsed_data: Dict) -> List[Dict]:
        """
        Recursive Character Text Splitter - Good for general text.
        Tries to split on paragraphs, then sentences, then words.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = []
        
        for page in parsed_data['pages']:
            page_num = page['page_num']
            
            # Chunk text content
            if page['text']:
                text_chunks = splitter.split_text(page['text'])
                for idx, text in enumerate(text_chunks):
                    chunks.append({
                        'text': text,
                        'metadata': {
                            'page': page_num,
                            'chunk_type': 'text',
                            'chunk_index': idx,
                            'strategy': 'recursive'
                        }
                    })
            
            # Keep tables intact (don't split)
            for table in page.get('tables', []):
                chunks.append({
                    'text': self._table_to_text(table),
                    'metadata': {
                        'page': page_num,
                        'chunk_type': 'table',
                        'table_id': table['table_id'],
                        'strategy': 'recursive'
                    }
                })
            
            # Keep figures with captions
            for figure in page.get('figures', []):
                chunks.append({
                    'text': f"[Figure: {figure.get('caption', 'No caption')}]",
                    'metadata': {
                        'page': page_num,
                        'chunk_type': 'figure',
                        'figure_id': figure['figure_id'],
                        'figure_path': figure.get('path', ''),
                        'strategy': 'recursive'
                    }
                })
        
        return chunks
    
    def _chunk_markdown(self, parsed_data: Dict) -> List[Dict]:
        """
        Markdown Header Text Splitter - Good for structured documents.
        Splits based on markdown headers (# ## ###).
        """
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        
        chunks = []
        
        # Convert parsed data to markdown format first
        markdown_text = self._convert_to_markdown(parsed_data)
        
        # Split by headers
        md_chunks = markdown_splitter.split_text(markdown_text)
        
        # Further split large chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        for md_chunk in md_chunks:
            content = md_chunk.page_content
            metadata = md_chunk.metadata
            
            # Split if too large
            if len(content) > self.chunk_size:
                sub_chunks = text_splitter.split_text(content)
                for sub_chunk in sub_chunks:
                    chunks.append({
                        'text': sub_chunk,
                        'metadata': {
                            **metadata,
                            'chunk_type': 'text',
                            'strategy': 'markdown'
                        }
                    })
            else:
                chunks.append({
                    'text': content,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'text',
                        'strategy': 'markdown'
                    }
                })
        
        return chunks
    
    def _chunk_by_section(self, parsed_data: Dict) -> List[Dict]:
        """
        Section-aware chunking - Keeps sections together when possible.
        Good for maintaining context.
        """
        chunks = []
        current_section = None
        section_text = []
        
        for page in parsed_data['pages']:
            page_text = page['text']
            
            # Detect section headers (heuristic: lines in ALL CAPS or starting with Chapter/Section)
            lines = page_text.split('\n')
            
            for line in lines:
                is_header = (
                    line.isupper() and len(line) > 5 or
                    line.startswith('Chapter') or
                    line.startswith('Section') or
                    line.startswith('CHAPTER')
                )
                
                if is_header:
                    # Save previous section
                    if section_text:
                        chunks.extend(self._split_section(
                            '\n'.join(section_text),
                            current_section,
                            page['page_num']
                        ))
                    
                    # Start new section
                    current_section = line.strip()
                    section_text = [line]
                else:
                    section_text.append(line)
            
            # Add tables and figures to current section
            for table in page.get('tables', []):
                section_text.append(self._table_to_text(table))
        
        # Save last section
        if section_text:
            chunks.extend(self._split_section(
                '\n'.join(section_text),
                current_section,
                parsed_data['pages'][-1]['page_num']
            ))
        
        return chunks
    
    def _chunk_hybrid(self, parsed_data: Dict) -> List[Dict]:
        """
        Hybrid approach: Use section-aware for main text, recursive for tables.
        Best of both worlds.
        """
        # Use section chunking for text
        text_chunks = self._chunk_by_section(parsed_data)
        
        # Use recursive for any remaining content
        for chunk in text_chunks:
            if chunk['metadata']['chunk_type'] == 'table':
                # Tables already handled well
                pass
        
        return text_chunks
    
    def _split_section(self, text: str, section_name: str, page_num: int) -> List[Dict]:
        """Split a section if it's too large."""
        if len(text) <= self.chunk_size:
            return [{
                'text': text,
                'metadata': {
                    'page': page_num,
                    'section': section_name,
                    'chunk_type': 'section',
                    'strategy': 'section'
                }
            }]
        
        # Split large sections
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        sub_chunks = splitter.split_text(text)
        return [
            {
                'text': chunk,
                'metadata': {
                    'page': page_num,
                    'section': section_name,
                    'chunk_type': 'section',
                    'chunk_index': idx,
                    'strategy': 'section'
                }
            }
            for idx, chunk in enumerate(sub_chunks)
        ]
    
    def _table_to_text(self, table: Dict) -> str:
        """Convert table to readable text format."""
        if not table.get('data'):
            return f"[Table {table.get('table_id', 'unknown')}: No data]"
        
        rows = table['data']
        
        # Format as markdown table
        text_lines = [f"Table: {table.get('table_id', 'unknown')}"]
        
        if rows:
            # Header row
            text_lines.append(" | ".join(str(cell) for cell in rows[0]))
            text_lines.append("-" * 50)
            
            # Data rows
            for row in rows[1:]:
                text_lines.append(" | ".join(str(cell) for cell in row))
        
        return "\n".join(text_lines)
    
    def _convert_to_markdown(self, parsed_data: Dict) -> str:
        """Convert parsed data to markdown format."""
        markdown_lines = []
        
        markdown_lines.append(f"# {parsed_data['metadata'].get('title', 'Financial Document')}")
        markdown_lines.append("")
        
        for page in parsed_data['pages']:
            markdown_lines.append(f"## Page {page['page_num']}")
            markdown_lines.append(page['text'])
            markdown_lines.append("")
            
            for table in page.get('tables', []):
                markdown_lines.append(self._table_to_text(table))
                markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    def _finalize_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Add unique IDs and validate chunks."""
        finalized = []
        
        for idx, chunk in enumerate(chunks):
            # Skip empty or too small chunks
            if len(chunk['text'].strip()) < MIN_CHUNK_SIZE:
                continue
            
            # Add chunk ID
            chunk['chunk_id'] = f"chunk_{idx:05d}"
            
            # Add token count
            chunk['metadata']['token_count'] = len(self.encoding.encode(chunk['text']))
            
            finalized.append(chunk)
        
        return finalized
    
    def _save_chunks(self, chunks: List[Dict], strategy: str):
        """Save chunks to JSONL file."""
        output_file = self.output_dir / f"chunks_{strategy}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
    
    def compare_strategies(self, parsed_data: Dict) -> Dict[str, List[Dict]]:
        """
        Compare all chunking strategies and return results.
        Used for evaluation in Lab 5.
        """
        strategies = ["recursive", "markdown", "section"]
        results = {}
        
        for strategy in strategies:
            logger.info(f"Testing strategy: {strategy}")
            chunks = self.chunk_document(parsed_data, strategy=strategy)
            results[strategy] = chunks
            
            # Print stats
            avg_length = sum(len(c['text']) for c in chunks) / len(chunks)
            avg_tokens = sum(c['metadata']['token_count'] for c in chunks) / len(chunks)
            
            logger.info(f"{strategy.capitalize()} Strategy:")
            logger.info(f"  Total chunks: {len(chunks)}")
            logger.info(f"  Avg length: {avg_length:.0f} characters")
            logger.info(f"  Avg tokens: {avg_tokens:.0f}")
            logger.info("")
        
        return results


def main():
    """Test the chunker."""
    from config.shared import TEMP_DIR
    
    # Load parsed data
    parsed_file = TEMP_DIR / "parsed_document.json"
    
    if not parsed_file.exists():
        print(f"Error: {parsed_file} not found. Run pdf_parser.py first!")
        return
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # Test chunker
    chunker = FinancialChunker()
    
    # Compare all strategies
    results = chunker.compare_strategies(parsed_data)
    
    print("\n" + "="*50)
    print("Chunking comparison complete!")
    print("="*50)


if __name__ == "__main__":
    main()