"""
utils/document_parser.py
High-Performance Document Ingestion & Text Extraction Engine for InterviewIQ.
Extracts structured clean text from PDF, DOCX, TXT, and Markdown files
with multi-engine fallback (pdfplumber -> pypdfium2 -> pdfminer).
"""

import io
import os
import re
from typing import Dict, Any, Optional

class DocumentParser:
    """Enterprise document parser for candidate resumes and job descriptions."""

    @classmethod
    def extract_text_from_bytes(cls, file_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Extracts clean, normalized text from raw bytes based on file extension.
        Returns a dict containing extracted text, word count, char count, and page count.
        """
        if not file_bytes:
            return {
                "success": False,
                "error": "Empty file payload provided.",
                "text": "",
                "word_count": 0,
                "char_count": 0,
                "page_count": 0,
                "filename": filename,
            }

        ext = os.path.splitext(filename)[1].lower() if filename else ".pdf"
        text = ""
        page_count = 1

        try:
            if ext == ".pdf":
                text, page_count = cls._extract_pdf(file_bytes)
            elif ext in (".docx", ".doc"):
                text, page_count = cls._extract_docx(file_bytes)
            else:
                # Plain text, markdown, csv, or unknown
                text, page_count = cls._extract_plaintext(file_bytes)

            clean_text = cls._normalize_text(text)
            words = len(clean_text.split()) if clean_text else 0
            chars = len(clean_text)

            return {
                "success": True,
                "filename": filename,
                "file_type": ext,
                "text": clean_text,
                "page_count": page_count,
                "word_count": words,
                "char_count": chars,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract document contents: {str(e)}",
                "filename": filename,
                "file_type": ext,
                "text": "",
                "page_count": 0,
                "word_count": 0,
                "char_count": 0,
            }

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes) -> tuple:
        """Extracts text from PDF bytes using pdfplumber with pypdfium2 fallback."""
        text_parts = []
        page_count = 0

        # Engine 1: pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    ptxt = page.extract_text()
                    if ptxt:
                        text_parts.append(ptxt)
            combined = "\n\n".join(text_parts).strip()
            if combined:
                return combined, page_count
        except Exception:
            pass

        # Engine 2: pypdfium2 fallback
        try:
            import pypdfium2
            pdf = pypdfium2.PdfDocument(file_bytes)
            page_count = len(pdf)
            for i in range(page_count):
                ptxt = pdf[i].get_textpage().get_text_range()
                if ptxt:
                    text_parts.append(ptxt)
            combined = "\n\n".join(text_parts).strip()
            if combined:
                return combined, page_count
        except Exception:
            pass

        # Engine 3: pdfminer fallback
        try:
            from pdfminer.high_level import extract_text
            extracted = extract_text(io.BytesIO(file_bytes)).strip()
            if extracted:
                return extracted, max(1, page_count)
        except Exception:
            pass

        return "", max(1, page_count)

    @classmethod
    def _extract_docx(cls, file_bytes: bytes) -> tuple:
        """Extracts text, headings, and tables from DOCX bytes using python-docx."""
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        parts = []

        for p in doc.paragraphs:
            val = p.text.strip()
            if val:
                # Add markdown heading markers if paragraph has a heading style
                if p.style and p.style.name.startswith("Heading 1"):
                    parts.append(f"# {val}")
                elif p.style and p.style.name.startswith("Heading 2"):
                    parts.append(f"## {val}")
                elif p.style and p.style.name.startswith("Heading 3"):
                    parts.append(f"### {val}")
                else:
                    parts.append(val)

        # Extract table rows
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))

        combined = "\n\n".join(parts).strip()
        return combined, 1

    @classmethod
    def _extract_plaintext(cls, file_bytes: bytes) -> tuple:
        """Decodes raw text/markdown bytes with UTF-8 and Latin-1 fallbacks."""
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return file_bytes.decode(enc), 1
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="ignore"), 1

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Cleans extracted text: fixes whitespace, hyphenated line wraps, null bytes."""
        if not text:
            return ""
        # Remove null bytes
        clean = text.replace("\x00", "")
        # Normalize non-breaking spaces
        clean = clean.replace("\u00a0", " ")
        # Fix hyphenated words at line endings (e.g., "distri-\nbuted" -> "distributed")
        clean = re.sub(r"(\b[a-zA-Z]+)-\n\s*([a-zA-Z]+\b)", r"\1\2", clean)
        # Collapse excessive whitespace
        clean = re.sub(r"\r\n", "\n", clean)
        clean = re.sub(r"[ \t]+", " ", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean)
        return clean.strip()
