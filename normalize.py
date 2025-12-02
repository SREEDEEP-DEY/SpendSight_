# normalize.py
import re
from datetime import datetime

def clean_amount(text):
    """
    Convert amount-like strings into float.
    Reused from your original script with small tweaks.
    """
    if text is None:
        return 0.0
    cleaned = str(text).replace(",", "").replace("\n", "").strip()
    cleaned = re.sub(r"\s+(Cr|DR|DR\.|CR|Dr|Cr)\.?$", "", cleaned, flags=re.IGNORECASE)
    if cleaned in ("", "-", "NA"):
        return 0.0
    match = re.search(r"[\d\.]+", cleaned)
    return float(match.group(0)) if match else 0.0


def parse_date(raw_date: str):
    """
    Try multiple date formats and return a datetime.date.
    Raises ValueError if nothing matches.
    """
    raw = raw_date.replace("\n", "").strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {raw_date!r}")


def normalize_txn(tx: dict, statement_id, user_id):
    """
    Convert parser output into the canonical transaction schema
    expected by the `transactions` table.

    Expected input dict from parsers:
      {
        "bank": "BOB" | "PNB" | "Federal Bank",
        "date": "01/12/2024",
        "description": "...",
        "debit": float,
        "credit": float,
        "balance": float,
        "category": None
      }
    """
    txn_date = parse_date(tx["date"])
    debit = float(tx.get("debit", 0.0) or 0.0)
    credit = float(tx.get("credit", 0.0) or 0.0)

    if debit > 0 and credit > 0:
        # should not normally happen; treat as debit for now
        direction = "debit"
        amount = -debit
    elif debit > 0:
        direction = "debit"
        amount = -debit
    elif credit > 0:
        direction = "credit"
        amount = credit
    else:
        direction = None
        amount = 0.0

    desc = (tx.get("description") or "").strip()

    return {
        "statement_id": statement_id,
        "user_id": user_id,
        "txn_date": txn_date,
        "posting_date": txn_date,   # you can change this later
        "description_raw": desc,
        "description_clean": desc,  # later you can run cleaning/normalization
        "amount": amount,
        "direction": direction,
        "vendor": None,
        "category": None,
        "subcategory": None,
        "confidence": None,
        "classification_source": None,
    }
