# parsers/federal.py
import re
import sys
from .utils import clean_amount_if_needed


def parse_federal_bank(pdf, filepath):
    """
    Parse Federal Bank-style statements.
    (Matches your 'Federal Bank of India' sample.)
    """
    print(f"[INFO] Parsing 'Federal Bank' format for {filepath}...")
    txns, last = [], None

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for line in lines:
            # Three variants as in your original code
            m1 = re.match(r"^(\d{2}/\d{2}/\d{4})\s+([\d,\.]+)\s+(DR|CR)\s+([\d,\.]+)\s+(.*)", line)
            m2 = re.match(r"^(\d{2}/\d{2}/\d{4})\s+([\d,\.]+)\s+([\d,\.]+)\s+(DR|CR)\s+(.*)", line)
            m3 = re.match(r"^s?\s*(\d{2}/\d{2}/\d{4})\s+([\d,\.]+)\s+([\d,\.]+)\s+(DR|CR)\s+(.*)", line)
            match = m1 or m2 or m3

            if match:
                try:
                    if m1:
                        date, amt, typ, bal, desc = match.groups()
                    else:
                        date, bal, amt, typ, desc = match.groups()
                    amt_val = clean_amount_if_needed(amt)
                    tx = {
                        "bank": "Federal Bank",
                        "date": date.strip("s"),
                        "description": desc.strip(),
                        "debit": amt_val if typ.upper() == "DR" else 0.0,
                        "credit": amt_val if typ.upper() == "CR" else 0.0,
                        "balance": clean_amount_if_needed(bal),
                        "category": None,
                    }
                    txns.append(tx)
                    last = tx
                except Exception as e:
                    print(f"[WARN] Skipping malformed line: {line} ({e})", file=sys.stderr)

            elif last and not (
                line.startswith(("Date", "Continued on", "End of statement")) or line.strip() == ""
            ):
                # Continuation of previous description
                last["description"] += " " + line.strip()

    print(f"[SUCCESS] Parsed {len(txns)} transactions from {filepath}.")
    return txns
