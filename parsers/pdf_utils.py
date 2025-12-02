# parsers/pdf_utils.py

"""
PDF Utilities for SpendSight
----------------------------

This module handles:
  • Full-text extraction (page by page)
  • Table extraction using pdfplumber
  • Line normalization and cleanup
  • OCR fallback (optional)
  • Removal of common encoding artifacts (e.g., \uFFFE, \uF0B7)
  • Helper for reading entire PDF once and reusing page objects

All bank parsers should import from this module instead of calling
pdfplumber API directly.
"""

import re
import pdfplumber

# OPTIONAL: OCR fallback (if pdfplumber text is missing)
# Uncomment if you install pytesseract & pillow
# from PIL import Image
# import pytesseract


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

ENCODING_JUNK_CHARS = [
    "\uFEFF",  # BOM
    "\uFFFE",
    "\uF0B7",  # weird bullet
    "\uF0A7",
    "\uFFFD",  # replacement char
    "￾",       # SBI artifact
]


def clean_text(text: str) -> str:
    """
    Remove persistent junk characters and normalize whitespace.
    """
    if not text:
        return ""

    for junk in ENCODING_JUNK_CHARS:
        text = text.replace(junk, "")

    # Normalize weird spacing
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)

    return text.strip()


# ------------------------------------------------------------
# PDF-level helpers
# ------------------------------------------------------------

def load_pdf(filepath: str):
    """Open PDF safely and return pdfplumber object."""
    return pdfplumber.open(filepath)


def get_page_text(page) -> str:
    """Extract text from a page and clean it."""
    raw = page.extract_text() or ""
    return clean_text(raw)


def extract_all_text(pdf) -> str:
    """
    Extract text from all pages into a single string.
    Best used for bank detection & debugging.
    """
    all_text = []
    for page in pdf.pages:
        all_text.append(get_page_text(page))
    return "\n".join(all_text)


def extract_text_by_page(pdf):
    """
    Returns a list of cleaned text per page.
    Useful for multi-page parsers.
    """
    return [get_page_text(page) for page in pdf.pages]


# ------------------------------------------------------------
# Table extraction helpers
# ------------------------------------------------------------

DEFAULT_TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
}


def extract_tables_from_page(page, settings=None):
    """
    Extract tables using pdfplumber's extract_table/extract_tables.
    Provides a clean, unified interface.
    """
    settings = settings or DEFAULT_TABLE_SETTINGS

    try:
        tables = page.extract_tables(settings)
        if not tables:
            return []
        # Clean tables: remove None/nested newlines
        clean_tables = []
        for tbl in tables:
            clean_tbl = []
            for row in tbl:
                clean_tbl.append([clean_text(cell or "") for cell in row])
            clean_tables.append(clean_tbl)
        return clean_tables
    except Exception:
        return []


def extract_first_table(pdf, settings=None):
    """Return only the first table found in the entire PDF."""
    for page in pdf.pages:
        tbls = extract_tables_from_page(page, settings)
        if tbls:
            return tbls[0]
    return []


# ------------------------------------------------------------
# OCR fallback (optional)
# ------------------------------------------------------------

def ocr_page(page):
    """
    Fallback OCR extraction method if pdfplumber returns no text.
    Requires pytesseract and pillow installed.
    """
    # Uncomment if enabling OCR:
    # image = page.to_image(resolution=300).original
    # pil_image = Image.fromarray(image)
    # text = pytesseract.image_to_string(pil_image)
    # return clean_text(text)
    return None  # disabled for now


# ------------------------------------------------------------
# Multi-line helpers (SBI-friendly)
# ------------------------------------------------------------

def split_into_lines(text):
    """
    Split text into meaningful lines.
    Remove empty lines and whitespace noise.
    """
    lines = text.split("\n")
    lines = [clean_text(ln) for ln in lines]
    return [ln for ln in lines if ln.strip()]


def concat_wrapped_lines(lines):
    """
    For banks like SBI, lines belonging to the same transaction
    may break mid-sentence.
    
    This helper merges lines intelligently:
      - If a line ends without a number/date but next line starts
        with lowercase or continuation, merge them.
    """
    merged = []
    buffer = ""

    for line in lines:
        if not buffer:
            buffer = line
            continue

        # Heuristic: next line starts without a date or amount → continuation
        if re.match(r"^\d{1,2}[-/ ]\w{3}", line):  # new date → new transaction
            merged.append(buffer)
            buffer = line
        elif re.match(r".*[A-Za-z]$", buffer) and not re.match(r"^\d", line):
            # previous line ends with letter & next does not start with number
            buffer += " " + line
        else:
            merged.append(buffer)
            buffer = line

    if buffer:
        merged.append(buffer)

    return merged
