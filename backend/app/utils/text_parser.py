import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple


def extract_text_from_txt(file_path: Path) -> str:
    """Read plain text with fallback encoding support."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode text file {file_path.name}")


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        text_parts = []
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Error parsing PDF {file_path.name}: {str(e)}")


def extract_text_from_docx(file_path: Path) -> str:
    """
    Extract text from DOCX by unpacking word/document.xml.
    This works natively with zero external dependencies.
    """
    try:
        with zipfile.ZipFile(file_path, "r") as docx_zip:
            xml_content = docx_zip.read("word/document.xml")
        
        # Word processing namespace
        namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        tree = ET.fromstring(xml_content)
        
        paragraphs = []
        for p in tree.iterfind(".//w:p", namespaces):
            texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Error parsing DOCX {file_path.name}: {str(e)}")


def extract_text_from_file(file_path: Path) -> Tuple[str, str]:
    """
    Extracts text and determines file extension type.
    Supports .pdf, .txt, .docx.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text = extract_text_from_pdf(file_path)
        return clean_text(text), "pdf"
    elif suffix in (".txt", ".md", ".log"):
        text = extract_text_from_txt(file_path)
        return clean_text(text), "txt"
    elif suffix == ".docx":
        text = extract_text_from_docx(file_path)
        return clean_text(text), "docx"
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: .pdf, .txt, .docx")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip null/control bytes."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse multiple consecutive blank lines into double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
