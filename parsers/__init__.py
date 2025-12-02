# parsers/__init__.py
import os
import sys
import pdfplumber

from .federal import parse_federal_bank
from .pnb import parse_pnb
from .bob import parse_bob
from .sbi import parse_sbi  # ⬅️ add this


def parse_statement(filepath):
    """
    Detect bank format from first-page text and call appropriate parser.

    Returns (bank_name, transactions_list)
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}", file=sys.stderr)
        return None, []

    try:
        with pdfplumber.open(filepath) as pdf:
            first_page = pdf.pages[0]
            first_text = first_page.extract_text()
            if not first_text:
                print(f"[ERROR] Could not extract text from {filepath}", file=sys.stderr)
                return None, []

            lower = first_text.lower()

            # SBI detection
            if "state bank of india" in lower or "sbi " in lower:
                return "SBI", parse_sbi(pdf, filepath)

            # Federal
            if "federal bank" in lower or "federal bank of india" in lower:
                return "Federal Bank", parse_federal_bank(pdf, filepath)

            # PNB
            if "punjab national bank" in lower or "pnb" in lower:
                return "PNB", parse_pnb(pdf, filepath)

            # BOB
            if "statement of account" in lower and ("transac-" in lower or "se-" in lower):
                return "BOB", parse_bob(pdf, filepath)

            print(f"[ERROR] Unknown bank format for {filepath}. Skipping.", file=sys.stderr)
            print(f"[DEBUG] First 200 chars: {first_text[:200]!r}")
            return None, []

    except Exception as e:
        print(f"[ERROR] Could not open/read {filepath}: {e}", file=sys.stderr)
        return None, []
