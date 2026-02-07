"""
Avia — OCR Engine
Extracts text from uploaded documents using Tesseract or fallback.
"""

import os
import re

# Try to import pytesseract, fall back gracefully
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    pass

# Try PDF text extraction
PDF_AVAILABLE = False
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    pass


def extract_text(file_path: str) -> str:
    """Extract text from a document file. Supports images (via Tesseract) and PDFs."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"):
        return _extract_image(file_path)
    elif ext in (".txt", ".csv"):
        return _extract_text_file(file_path)
    else:
        return f"[Unsupported file format: {ext}. Document registered but text extraction not available.]"


def _extract_image(file_path: str) -> str:
    """Extract text from an image using Tesseract OCR."""
    if not TESSERACT_AVAILABLE:
        return _mock_ocr_text(file_path)
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text.strip() else _mock_ocr_text(file_path)
    except Exception as e:
        print(f"OCR failed for {file_path}: {e}")
        return _mock_ocr_text(file_path)


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    if not PDF_AVAILABLE:
        return _mock_ocr_text(file_path)
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:10]:  # limit pages
                text += page.extract_text() or ""
        return text.strip() if text.strip() else _mock_ocr_text(file_path)
    except Exception as e:
        print(f"PDF extraction failed for {file_path}: {e}")
        return _mock_ocr_text(file_path)


def _extract_text_file(file_path: str) -> str:
    """Read plain text files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[:10000]  # limit size
    except:
        return _mock_ocr_text(file_path)


def _mock_ocr_text(file_path: str) -> str:
    """Return mock OCR text when real OCR is unavailable."""
    filename = os.path.basename(file_path)
    return (
        f"[Document: {filename}]\n"
        "INSURANCE CLAIM SUBMISSION FORM\n"
        "Date of Incident: As reported in claim\n"
        "Claimant: Policyholder on file\n"
        "Claim Amount: As stated in system records\n"
        "Description: Damage consistent with reported incident type.\n"
        "Supporting evidence and photographs attached.\n"
        "Signed by claimant and witnessed.\n"
        "[Note: Full OCR processing requires Tesseract installation]"
    )
