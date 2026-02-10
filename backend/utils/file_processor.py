"""
File processing utilities for extracting text from uploaded files.
"""

import io
import logging
from typing import List, Dict
from pathlib import Path
from fastapi import HTTPException, UploadFile

from config import UploadConfig

logger = logging.getLogger(__name__)

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
            raise ImportError(
                "pypdf is not installed. Install it with: pip install pypdf"
            )

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
            raise ImportError(
                "python-docx is not installed. Install it with: pip install python-docx"
            )

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
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1")
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

        if file_ext == ".pdf":
            return cls.extract_text_from_pdf(file_bytes)
        elif file_ext in [".docx", ".doc"]:
            return cls.extract_text_from_docx(file_bytes)
        elif file_ext in [".txt", ".md", ".markdown"]:
            return cls.extract_text_from_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")


async def file_processor(files: List[UploadFile]) -> List[Dict[str, str]]:
    file_processor_instance = FileProcessor()
    file_contents = []
    for uploaded_file in files:
        try:
            file_bytes = await uploaded_file.read()

            # Enforce server-side file size limit
            if len(file_bytes) > UploadConfig.MAX_FILE_SIZE:
                max_mb = UploadConfig.MAX_FILE_SIZE / (1024 * 1024)
                logger.warning(
                    "File '%s' rejected: %d bytes (limit: %d MB)",
                    uploaded_file.filename,
                    len(file_bytes),
                    max_mb,
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"File '{uploaded_file.filename}' exceeds the {max_mb:.0f} MB size limit",
                )

            content = file_processor_instance.process_file(
                uploaded_file.filename or "unknown", file_bytes
            )
            file_contents.append(
                {"filename": uploaded_file.filename, "content": content}
            )
        except HTTPException:
            raise  # Re-raise size limit errors as-is
        except Exception as e:
            file_contents.append(
                {
                    "filename": uploaded_file.filename,
                    "content": f"[Error processing file: {str(e)}]",
                }
            )
    return file_contents
