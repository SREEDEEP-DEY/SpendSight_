import os
import sys
import json
from pathlib import Path
from datetime import datetime
import uuid
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Any, Optional
import pdfplumber

# Day 3: Regex engine
from regex_engine.regex_classifier import classify_with_regex

# Your existing parsers
from parsers.bob import parse_bob
from parsers.pnb import parse_pnb
from parsers.sbi import parse_sbi
from parsers.federal import parse_federal_bank
from parsers.idbi import parse_idbi
from parsers.parse_ocr_generic import parse_ocr_generic
from parsers.icici import parse_icici


load_dotenv()

DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

# --------------------------------------------------------
# DB CONNECTION
# --------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# --------------------------------------------------------
# DB HELPERS
# --------------------------------------------------------

def insert_transactions(conn, transactions):
    if not transactions:
        return []

    columns = transactions[0].keys()
    values = [tuple(tx.values()) for tx in transactions]

    query = f"""
    INSERT INTO transactions ({', '.join(columns)})
    VALUES %s
    RETURNING txn_id;
    """

    with conn.cursor() as cur:
        extras.execute_values(cur, query, values)
        inserted_ids = [row[0] for row in cur.fetchall()]
        conn.commit()
        return inserted_ids


def insert_classification_log(conn, txn_id, stage, prediction, confidence, meta):
    q = """
    INSERT INTO classification_log (txn_id, stage, prediction, confidence, meta)
    VALUES (%s, %s, %s, %s, %s::jsonb)
    """
    with conn.cursor() as cur:
        cur.execute(q, (txn_id, stage, prediction, confidence, json.dumps(meta)))
    conn.commit()


def create_document_and_statement(conn, user_id, bank_name, file_path, original_filename):
    doc_q = """
    INSERT INTO documents (user_id, doc_type, file_path, original_filename, status)
    VALUES (%s, 'bank_statement', %s, %s, 'uploaded')
    RETURNING doc_id;
    """

    stmt_q = """
    INSERT INTO statements (doc_id, user_id, bank_name, status)
    VALUES (%s, %s, %s, 'parsed')
    RETURNING statement_id;
    """

    with conn.cursor() as cur:
        cur.execute(doc_q, (user_id, file_path, original_filename))
        doc_id = cur.fetchone()[0]

        cur.execute(stmt_q, (doc_id, user_id, bank_name))
        statement_id = cur.fetchone()[0]

    conn.commit()
    return doc_id, statement_id


def update_document_status(conn, doc_id, status):
    q = "UPDATE documents SET status = %s WHERE doc_id = %s"
    with conn.cursor() as cur:
        cur.execute(q, (status, doc_id))
    conn.commit()

# --------------------------------------------------------
# PDF DETECTION + ROUTING
# --------------------------------------------------------

def parse_statement(filepath):
    import pdfplumber
    from pathlib import Path

    with pdfplumber.open(filepath) as pdf:
        first = (pdf.pages[0].extract_text() or "").lower()
        filename = Path(filepath).name.lower()

        # known banks...
        if "bank of baroda" in first or "statement of account" in first:
            return "BOB", parse_bob(pdf, filepath)
        if "punjab national bank" in first:
            return "PNB", parse_pnb(pdf, filepath)
        if "state bank of india" in first or "sbi" in first:
            return "SBI", parse_sbi(pdf, filepath)
        if "federal bank" in first:
            return "Federal Bank", parse_federal_bank(pdf, filepath)
        if "icici" in first:
            return "ICICI Bank", parse_icici(pdf, filepath)
        if "idbi" in first:
            return "IDBI Bank", parse_idbi(pdf, filepath)

        # # OCR / generic
        # if "_ocr_" in filename or "spendsight ocr" in first:
        #     txns = parse_ocr_generic(text=)
        #     return "GENERIC_OCR", txns

        # # final fallback
        # txns = parse_ocr_generic()
        # if txns:
        #     return "GENERIC_OCR", txns

        return None, []

# import inspect

# def call_parser(func, filepath, full_text=None):
#     """
#     Safely call any parser regardless of whether it accepts:
#       - (pdf, filepath)
#       - (filepath)
#       - (text=...)
#     """
#     sig = inspect.signature(func)
#     params = list(sig.parameters.values())

#     try:
#         if len(params) == 2:
#             # Old style: (pdf, filepath)
#             with pdfplumber.open(filepath) as pdf:
#                 return func(pdf, filepath)

#         elif len(params) == 1:
#             # New style: (filepath)
#             return func(filepath)

#         else:
#             # Text-based OCR style: parse_ocr_generic(text=...)
#             if "text" in sig.parameters:
#                 return func(text=full_text)
#             if "filepath" in sig.parameters:
#                 return func(filepath=filepath)

#         # fallback
#         return func(filepath)

#     except Exception as e:
#         print(f"[ParserAdapter] Error calling {func.__name__}: {e}")
#         return []

# def parse_statement(filepath):
#     """
#     Detect bank format and route to the appropriate parser.
#     Returns (bank_name_or_tag, list_of_raw_txns)

#     NOTE: we avoid passing the pdfplumber PDF object to parsers because the
#     object is closed at the end of the 'with' block — instead pass filepath or
#     the extracted text to parsers (safer across processes).
#     """
#     import pdfplumber
#     from pathlib import Path
#     import logging

#     logger = logging.getLogger("PipeLine.parse_statement")
#     filename = Path(filepath).name.lower()

#     # Extract page-level text and full-text while the file handle is open
#     first = ""
#     full_text_str = ""
#     try:
#         with pdfplumber.open(filepath) as pdf:
#             if pdf.pages:
#                 first = (pdf.pages[0].extract_text() or "").strip().lower()
#             # build full text
#             pages_text = []
#             for p in pdf.pages:
#                 pages_text.append(p.extract_text() or "")
#             full_text_str = "\n".join(pages_text).strip().lower()
#     except Exception as e:
#         logger.exception("Failed to open/extract text from PDF %s: %s", filepath, e)
#         # If we couldn't open PDF, attempt to fall back to passing the filepath to parsers
#         first = ""
#         full_text_str = ""

#     logger.info("Parsing file=%s (first_page_preview=%s...)", filepath, first[:120].replace("\n", " "))

#     # small helper
#     def has_any(hay: str, needles):
#         if not hay:
#             return False
#         for n in needles:
#             if n and n in hay:
#                 return True
#         return False

#     # Primary detection using first page + filename

#     # Bank of Baroda / BOB
#     # BOB
#     if has_any(first, ["bank of baroda", "statement of account"]):
#         return "BOB", call_parser(parse_bob, filepath)

#     # PNB
#     if "punjab national bank" in first or "pnb" in filename:
#         return "PNB", call_parser(parse_pnb, filepath)

#     # SBI
#     if has_any(first, ["state bank of india", "sbi"]):
#         return "SBI", call_parser(parse_sbi, filepath)

#     # Federal
#     if "federal bank" in first:
#         return "Federal Bank", call_parser(parse_federal_bank, filepath)

#     # ICICI
#     if has_any(first, ["icici bank", "icici"]):
#         return "ICICI Bank", call_parser(parse_icici, filepath)

#     # IDBI
#     if has_any(first, ["idbi bank", "idbi"]):
#         return "IDBI Bank", call_parser(parse_idbi, filepath)

#     # OCR-generic
#     if "_ocr_" in filename or "ocr" in filename:
#         return "GENERIC_OCR", call_parser(parse_ocr_generic, filepath, full_text_str)

    

#     # Final fallback: if full_text_str has table-like content, try generic parser
#     if full_text_str:
#         try:
#             txns = call_parser(parse_ocr_generic,filepath,full_text_str)
#             if txns:
#                 return "GENERIC_OCR", txns
#         except Exception:
#             logger.debug("Fallback generic parser failed for %s", filepath, exc_info=True)

#     logger.warning("Could not detect bank for file=%s; returning (None, [])", filepath)
#     return None, []

# --------------------------------------------------------
# NORMALIZATION
# --------------------------------------------------------

def clean_amount(v):
    if not v:
        return 0.0
    s = str(v).replace(",", "").replace(" ", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except:
        return 0.0



DATE_PATTERNS = [
    # 12-06-2023, 12/06/2023, 12.06.2023
    r"(?P<date>\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})",
    # 2023-06-12
    r"(?P<date>\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})",
]

AMOUNT_PATTERN = r"(?P<amount>[+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"


def _try_parse_date(s: str):
    s = s.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
                "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None
# --- add near the top of PipeLine.py (imports area) ---
from datetime import datetime, date
try:
    # dateutil is very forgiving with varied date formats
    from dateutil.parser import parse as _dateutil_parse
    _HAS_DATEUTIL = True
except Exception:
    _HAS_DATEUTIL = False

import re

# -------------------------
# parse_date helper
# -------------------------
def parse_date(s: str) -> Optional[date]:
    """
    Parse a date-like string from bank statements into a datetime.date.
    Returns None if parsing fails.

    Handles:
      - common textual dates (e.g., 12-Jan-2023, 12/01/23, 2023-01-12)
      - formats like '12 JAN' (assume current year)
      - ddmmyyyy or ddmmyy numeric forms
    """
    if not s:
        return None
    s = str(s).strip()
    # quick numeric cleanup
    s = re.sub(r'[^\w\-/\. ]', ' ', s)  # remove stray symbols except separators
    s = re.sub(r'\s+', ' ', s).strip()

    # Try dateutil first (if available)
    if _HAS_DATEUTIL:
        try:
            dt = _dateutil_parse(s, dayfirst=True, fuzzy=True)
            return dt.date()
        except Exception:
            pass

    # Manual heuristics (fallback)
    # 1) dd-mm-yyyy or dd/mm/yyyy or dd.mm.yyyy
    m = re.match(r'(\d{1,2})[\/\-. ](\d{1,2})[\/\-. ](\d{2,4})$', s)
    if m:
        d, mth, y = m.groups()
        d = int(d); mth = int(mth); y = int(y)
        if y < 100:  # two-digit year
            y += 2000 if y < 70 else 1900
        try:
            return date(y, mth, d)
        except Exception:
            pass

    # 2) y-m-d or yyyy-mm-dd
    m = re.match(r'(\d{4})[\/\-. ](\d{1,2})[\/\-. ](\d{1,2})$', s)
    if m:
        y, mth, d = map(int, m.groups())
        try:
            return date(y, mth, d)
        except Exception:
            pass

    # 3) ddMonyyyy or ddMonyy e.g., 12JAN2023 or 12JAN23
    m = re.match(r'(\d{1,2})\s*([A-Za-z]{3,})\s*(\d{2,4})?$', s)
    if m:
        d = int(m.group(1))
        mon = m.group(2)[:3].title()
        y = m.group(3)
        try:
            y = int(y) if y else datetime.now().year
            if y < 100:
                y += 2000 if y < 70 else 1900
            dt = datetime.strptime(f"{d} {mon} {y}", "%d %b %Y")
            return dt.date()
        except Exception:
            pass

    # 4) plain 6/8 digit numeric like 120120 or 12012020
    m = re.match(r'^(\d{6,8})$', s)
    if m:
        digits = m.group(1)
        if len(digits) == 6:  # ddmmyy
            d = int(digits[0:2]); mth = int(digits[2:4]); y = int(digits[4:6])
            y += 2000 if y < 70 else 1900
        else:  # 8 digits ddmmyyyy
            d = int(digits[0:2]); mth = int(digits[2:4]); y = int(digits[4:8])
        try:
            return date(y, mth, d)
        except Exception:
            pass

    # If all fail, return None
    return None


def normalize_txn(tx, statement_id, user_id):
    """
    Normalize a raw parsed transaction into the canonical schema.

    - Tries 'amount' first (to preserve existing behaviour if it works)
    - If that is zero / empty, falls back to typical debit/credit fields
    - Outflows (debits / withdrawals) are stored as NEGATIVE
    - Inflows (credits / deposits / salary / interest) as POSITIVE
    """

    raw_date = str(tx.get("date", "")).strip()
    if not raw_date or len(raw_date) < 4:
        return None

    d = parse_date(raw_date)
    if not d:
        return None

    desc = tx.get("description", "").strip()

    # 1) Primary: use tx["amount"] if it is non-zero
    amt = clean_amount(tx.get("amount"))
    if amt is None:
        amt = Decimal("0.00")

    # If parser already gave a valid non-zero amount, trust it
    if amt != 0:
        signed_amount = amt
        amount_source = "amount"
    else:
        # 2) Fallback: infer from typical debit / credit style fields
        signed_amount, amount_source = _infer_amount_from_raw_fields(tx)

    # Optional: debug once in a while
    # print("NORMALIZED TX:", desc[:60], "| raw:", tx, "| amt:", signed_amount, "| src:", amount_source)

    return {
        "user_id": user_id,
        "statement_id": statement_id,
        "txn_date": d,
        "description_raw": desc,
        "amount": signed_amount,
        "vendor": None,
        "category": None,
        "subcategory": None,
        "confidence": 0.0,
        "classification_source": None,
    }


def _infer_amount_from_raw_fields(tx):
    """
    Try to derive a signed amount from common raw fields.

    Convention:
      - Debits / withdrawals -> NEGATIVE
      - Credits / deposits / salary / interest -> POSITIVE

    Returns:
      (Decimal amount, source_key: str | None)
    """
    # Helper to check a raw field is "non-empty"
    def _has_value(v):
        return v not in (None, "", "-", " ", "\u00a0")

    # 1) Debit-like fields (money going OUT)
    debit_keys = [
        "debit",
        "withdrawal",
        "withdrawal_amount",
        "debit_amount",
        "dr_amount",
        "dr",
    ]

    for key in debit_keys:
        if _has_value(tx.get(key)):
            raw = tx.get(key)
            amt = clean_amount(raw)
            try:
                amt = abs(amt)
            except Exception:
                amt = Decimal("0.00")
            return -amt, key  # store as NEGATIVE

    # 2) Credit-like fields (money coming IN)
    credit_keys = [
        "credit",
        "deposit",
        "deposit_amount",
        "credit_amount",
        "cr_amount",
        "cr",
    ]

    for key in credit_keys:
        if _has_value(tx.get(key)):
            raw = tx.get(key)
            amt = clean_amount(raw)
            try:
                amt = abs(amt)
            except Exception:
                amt = Decimal("0.00")
            return amt, key  # store as POSITIVE

    # 3) Absolute fallback: if *nothing* is present, return 0.00
    return Decimal("0.00"), None

# --------------------------------------------------------
# MAIN PIPELINE PER FILE
# --------------------------------------------------------

def process_pdf(conn, filepath, user_id):
    print(f"\n--- Processing: {os.path.basename(filepath)}")

    bank, raw_txns = parse_statement(filepath)
    if not bank or not raw_txns:
        print("[WARN] Could not detect bank or parse PDF.")
        return 0

    doc_id, statement_id = create_document_and_statement(
        conn, user_id, bank, filepath, os.path.basename(filepath)
    )

    normalized = []
    for tx in raw_txns:
        n = normalize_txn(tx, statement_id, user_id)
        if n:
            normalized.append(n)

    # INSERT FIRST to get txn_ids
    txn_ids = insert_transactions(conn, normalized)

    # APPLY REGEX CLASSIFICATION
    for idx, txn_id in enumerate(txn_ids):
        tx = normalized[idx]
        desc = tx["description_raw"]

        category, subcategory, vendor, conf, meta = classify_with_regex(desc)

        # UPDATE transactions
        q = """
        UPDATE transactions
        SET vendor=%s, category=%s, subcategory=%s, confidence=%s, classification_source='regex'
        WHERE txn_id=%s
        """
        with conn.cursor() as cur:
            cur.execute(q, (vendor, category, subcategory, conf, txn_id))
        conn.commit()

        # INSERT INTO LOG
        prediction = f"{category}.{subcategory}" if category else None
        insert_classification_log(conn, txn_id, "regex", prediction, conf, meta)

    update_document_status(conn, doc_id, "parsed")
    return len(txn_ids)

# --------------------------------------------------------
# MAIN
# --------------------------------------------------------

def main():
    if not DEFAULT_USER_ID:
        print("[ERROR] DEFAULT_USER_ID not set")
        sys.exit(1)

    input_dir = Path("./data/input")
    files = [str(p) for p in input_dir.glob("*.pdf")]

    print("SpendSight – Day 3 Pipeline\n")

    conn = get_db_connection()
    total = 0

    for f in files:
        total += process_pdf(conn, f, DEFAULT_USER_ID)

    conn.close()

    print(f"\nTotal processed: {total}")


if __name__ == "__main__":
    main()
