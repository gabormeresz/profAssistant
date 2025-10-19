"""
File processing utilities for extracting text from uploaded files.
"""

import io
from typing import List, Dict
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class FileProcessor:
    """Process uploaded files and extract text content."""
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF file."""
        if PdfReader is None:
            raise ImportError("pypdf is not installed. Install it with: pip install pypdf")
        
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            
            text_content = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"--- Page {page_num} ---\n{text}")
            
            return "\n\n".join(text_content)
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from DOCX file."""
        if Document is None:
            raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
        
        try:
            docx_file = io.BytesIO(file_bytes)
            doc = Document(docx_file)
            
            text_content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text)
            
            return "\n\n".join(text_content)
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file_bytes: bytes) -> str:
        """Extract text from plain text file."""
        try:
            # Try UTF-8 first, fall back to latin-1 if needed
            try:
                return file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return file_bytes.decode('latin-1')
        except Exception as e:
            raise ValueError(f"Error extracting text from TXT: {str(e)}")
    
    @classmethod
    def process_file(cls, filename: str, file_bytes: bytes) -> str:
        """
        Process a file and extract its text content based on file extension.
        
        Args:
            filename: Name of the file
            file_bytes: Raw bytes of the file
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file type is not supported or extraction fails
        """
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.pdf':
            return cls.extract_text_from_pdf(file_bytes)
        elif file_ext in ['.docx', '.doc']:
            return cls.extract_text_from_docx(file_bytes)
        elif file_ext in ['.txt', '.md', '.markdown']:
            return cls.extract_text_from_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    @classmethod
    def process_multiple_files(cls, files: List[tuple[str, bytes]]) -> List[Dict[str, str]]:
        """
        Process multiple files and return their contents.
        
        Args:
            files: List of tuples containing (filename, file_bytes)
            
        Returns:
            List of dictionaries with 'filename' and 'content' keys
        """
        results = []
        for filename, file_bytes in files:
            try:
                content = cls.process_file(filename, file_bytes)
                results.append({
                    'filename': filename,
                    'content': content
                })
            except Exception as e:
                # Include error in results but don't fail the whole batch
                results.append({
                    'filename': filename,
                    'content': f"[Error processing file: {str(e)}]"
                })
        
        return results
