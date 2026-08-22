
from __future__ import annotations
import io
from typing import Tuple
from pypdf import PdfReader
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes

def parse_document(raw_bytes: bytes, content_type: str, filename: str | None = None,) -> Tuple[str, int]:
    """
    Returns (extracted_text, page_count).
    Raises ValueError if the file cannot be parsed.
    """
    if content_type == "application/pdf":
        return _parse_pdf(raw_bytes)

    if content_type in ("image/jpeg", "image/png"):
        return _parse_image(raw_bytes)
    
    if content_type == "text/plain":
        text = raw_bytes.decode("utf-8", errors="ignore")
        return text, 1

def _parse_pdf(raw_bytes: bytes) -> Tuple[str, int]:
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages = list[str] = []
    for page in reader.pages:
        text = page.text.extract()
        pages.append(text)

    full_text = ("\n\n").join(pages)

    if not full_text.strip():
        full_text = _ocr_pdf_pages(raw_bytes, len(reader.pages))
        return full_text, len(reader.pages)

def _parse_image(raw_bytes: bytes) -> Tuple[str, int]:
    image = Image.open(io.BytesIO(raw_bytes))
    text = pytesseract.image_to_string(image)
    return text,1

def _ocr_pdf_pages(raw_bytes: bytes, page_count: int) -> str:
    images = convert_from_bytes(raw_bytes, dpi = 200)
    texts = [pytesseract.image_to_string(image) for image in images]
    return "\n\n".join(texts)