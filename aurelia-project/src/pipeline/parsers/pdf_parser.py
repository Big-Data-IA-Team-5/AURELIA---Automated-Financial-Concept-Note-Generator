# pipeline/parsers/pdf_parser.py
"""
PDF Parser module for extracting text from PDF documents
"""

import pdfplumber
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF documents and extract text content"""
    
    def __init__(self, pdf_path: str = "data/raw/fintbx.pdf"):
        self.pdf_path = Path(pdf_path)
        self.parsed_content = []
        
    def parse(self, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Parse PDF and extract text from each page
        """
        logger.info(f"Parsing PDF: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            pages_to_parse = pdf.pages[:max_pages] if max_pages else pdf.pages
            
            for page_num, page in enumerate(pages_to_parse, 1):
                try:
                    text = page.extract_text()
                    if text:
                        self.parsed_content.append({
                            'page': page_num,
                            'text': text,
                            'char_count': len(text),
                            'source': str(self.pdf_path)
                        })
                except Exception as e:
                    logger.error(f"Error parsing page {page_num}: {e}")
                    
        logger.info(f"Successfully parsed {len(self.parsed_content)} pages")
        return self.parsed_content
    
    def save_parsed_content(self, output_path: str = "data/processed/parsed_content.json"):
        """Save parsed content to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.parsed_content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parsed content to {output_file}")
        return output_file