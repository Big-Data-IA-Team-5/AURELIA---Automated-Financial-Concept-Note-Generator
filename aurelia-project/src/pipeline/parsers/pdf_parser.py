"""
PDF Parser for Financial Documents
Extracts text, tables, figures, and formulas from PDF files.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json

import pdfplumber
from PIL import Image

from config.shared import TEMP_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """
    Comprehensive PDF parser that extracts:
    - Text with reading order
    - Tables
    - Figures/images with captions
    - Code snippets
    - Formulas
    """
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.output_dir = TEMP_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def parse(self) -> Dict:
        """
        Main parsing method that orchestrates all extraction.
        
        Returns:
            Dict with structure:
            {
                'metadata': {...},
                'pages': [
                    {
                        'page_num': 1,
                        'text': '...',
                        'tables': [...],
                        'figures': [...],
                        'reading_order': [...]
                    }
                ]
            }
        """
        logger.info(f"Starting to parse: {self.pdf_path}")
        
        result = {
            'metadata': self._extract_metadata(),
            'pages': []
        }
        
        # Try Docling first for advanced parsing
        try:
            docling_result = self._parse_with_docling()
            if docling_result:
                logger.info("Successfully parsed with Docling")
                return docling_result
        except Exception as e:
            logger.warning(f"Docling parsing failed: {e}. Falling back to traditional methods.")
        
        # Fallback to traditional parsing
        result['pages'] = self._parse_with_pdfplumber()
        
        # Save intermediate results
        self._save_intermediate_results(result)
        
        logger.info(f"Parsing complete. Extracted {len(result['pages'])} pages")
        return result
    
    def _extract_metadata(self) -> Dict:
        """Extract PDF metadata."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                metadata = pdf.metadata or {}
                metadata['page_count'] = len(pdf.pages)
                return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {'page_count': 0}
    
    def _parse_with_docling(self) -> Optional[Dict]:
        """
        Use Docling for advanced PDF understanding.
        Docling handles reading order, tables, formulas better.
        """
        try:
            from docling.document_converter import DocumentConverter
            
            converter = DocumentConverter()
            result = converter.convert(str(self.pdf_path))
            
            # Convert Docling result to our format
            parsed_data = {
                'metadata': {
                    'source': 'docling',
                    'page_count': len(result.pages) if hasattr(result, 'pages') else 0
                },
                'pages': []
            }
            
            if hasattr(result, 'pages'):
                for page_num, page in enumerate(result.pages, start=1):
                    page_data = {
                        'page_num': page_num,
                        'text': page.text if hasattr(page, 'text') else '',
                        'tables': self._extract_docling_tables(page),
                        'figures': self._extract_docling_figures(page),
                        'reading_order': page.reading_order if hasattr(page, 'reading_order') else []
                    }
                    parsed_data['pages'].append(page_data)
            
            return parsed_data
            
        except Exception as e:
            logger.warning(f"Docling parsing error: {e}")
            return None
    
    def _parse_with_pdfplumber(self) -> List[Dict]:
        """
        Traditional parsing with pdfplumber.
        """
        pages_data = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                logger.info(f"Parsing page {page_num}/{len(pdf.pages)}")
                
                page_data = {
                    'page_num': page_num,
                    'text': self._extract_text(page),
                    'tables': self._extract_tables(page),
                    'figures': [],  # Simplified - no figure extraction without PyMuPDF
                    'word_boxes': page.extract_words()  # For layout analysis
                }
                
                pages_data.append(page_data)
        
        return pages_data
    
    def _extract_text(self, page) -> str:
        """Extract text from a pdfplumber page."""
        try:
            text = page.extract_text(
                x_tolerance=3,
                y_tolerance=3,
                layout=True  # Preserve layout
            )
            return text if text else ""
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def _extract_tables(self, page) -> List[Dict]:
        """Extract tables from a pdfplumber page."""
        tables = []
        try:
            extracted_tables = page.extract_tables()
            for idx, table in enumerate(extracted_tables):
                if table:
                    tables.append({
                        'table_id': f"page_{page.page_number}_table_{idx}",
                        'data': table,
                        'bbox': None  # Could extract bbox if needed
                    })
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return tables
    
    def _extract_docling_tables(self, page) -> List[Dict]:
        """Extract tables from Docling page."""
        tables = []
        if hasattr(page, 'tables'):
            for idx, table in enumerate(page.tables):
                tables.append({
                    'table_id': f"docling_table_{idx}",
                    'data': table.to_dict() if hasattr(table, 'to_dict') else str(table)
                })
        return tables
    
    def _extract_docling_figures(self, page) -> List[Dict]:
        """Extract figures from Docling page."""
        figures = []
        if hasattr(page, 'figures'):
            for idx, figure in enumerate(page.figures):
                figures.append({
                    'figure_id': f"docling_figure_{idx}",
                    'caption': figure.caption if hasattr(figure, 'caption') else ""
                })
        return figures
    
    def _save_intermediate_results(self, result: Dict):
        """Save parsed results to temp directory."""
        output_path = self.output_dir / "parsed_document.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved intermediate results to: {output_path}")


def main():
    """Test the parser."""
    from config.shared import PDF_PATH
    
    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        print("Please add fintbx.pdf to data/raw/ folder")
        return
    
    parser = PDFParser(PDF_PATH)
    result = parser.parse()
    print(f"\n{'='*50}")
    print(f"✓ Parsed {len(result['pages'])} pages")
    print(f"✓ Metadata: {result['metadata']}")
    if result['pages']:
        print(f"✓ First page text preview: {result['pages'][0]['text'][:200]}...")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()