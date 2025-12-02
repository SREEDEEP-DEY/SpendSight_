# parsers/sbi.py

"""
SBI (State Bank of India) Statement Parser for SpendSight

Assumptions / SBI-like format (synthetic but realistic):
  - Columns: Date | Value Date | Description | Ref | Debit | Credit | Balance
  - Dates often like: "06 Sep 2019" or "6 Sep 2019"
  - Descriptions can span multiple lines
  - Debit/Credit + Balance amounts appear at the END of the transaction block
  - Some OCR / encoding junk characters may appear (handled by pdf_utils.clean_text)

Output format (per transaction dict):
  {
    "bank": "SBI",
    "date": "06 Sep 2019",
    "description": "...",
    "debit": float,
    "credit": float,
    "balance": float,
    "category": None
  }

These will later be normalized into the canonical DB schema by normalize.normalize_txn().
"""

import re
import sys

from .pdf_utils import extract_text_by_page, split_into_lines, concat_wrapped_lines
from .utils import clean_amount_if_needed


# Date patterns SBI commonly uses (e.g., "6 Sep 2019", "06 Sep 2019")
DATE_REGEX = re.compile(
    r"^(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
    re.IGNORECASE,
)


def _is_header_or_footer(line: str) -> bool:
    """
    Heuristic filter for header/footer lines that we don't want to treat
    as transaction content.
    """
    l = line.lower()
    if not l:
        return True

    header_keywords = [
        "state bank of india",
        "account statement",
        "account no",
        "branch",
        "ifsc",
        "micr",
        "savings bank account",
        "page",
        "total",  # sometimes summary rows
        "balance brought forward",
        "balance carried forward",
        "date particulars",
        "value date",  # often in tab header
    ]

    return any(k in l for k in header_keywords)


def _looks_like_txn_start(line: str) -> bool:
    """
    Whether this line likely starts a new transaction.
    SBI usually starts with a date like "06 Sep 2019".
    """
    line = line.strip()
    if not line:
        return False
    if _is_header_or_footer(line):
        return False
    return bool(DATE_REGEX.match(line))


def _extract_amounts_and_desc(buffer: str):
    """
    Given a merged transaction text block (date + value date + desc + amounts),
    extract:
      - date_str (first date)
      - desc (description without trailing amounts)
      - debit, credit, balance

    We assume the LAST one or two amounts in the buffer are:
      - transaction amount (debit or credit)
      - balance

    Heuristics:
      - If we find two amount-like tokens at the end → treat second as balance
      - Decide debit vs credit via simple pattern in description (" by " → credit,
        " to " → debit, else default to debit).
    """
    # 1) Extract the first date (transaction date)
    m_date = DATE_REGEX.match(buffer)
    if not m_date:
        raise ValueError(f"No valid date at start of transaction block: {buffer[:80]!r}")

    date_str = m_date.group(1)  # e.g., "06 Sep 2019"
    rest = buffer[m_date.end() :].strip()

    # Optional: value date as second date (ignore for now)
    m_val = DATE_REGEX.match(rest)
    if m_val:
        rest = rest[m_val.end() :].strip()

    # 2) Find amount tokens at the end (e.g. "... 2,000.00 25,844.76")
    #    We'll scan from the right for up to 2 amounts.
    amount_pattern = re.compile(r"([\d,]+\.\d{2})")
    all_amounts = amount_pattern.findall(rest)

    debit = 0.0
    credit = 0.0
    balance = 0.0
    desc = rest

    if not all_amounts:
        # No amounts found; treat whole rest as description
        return date_str, desc.strip(), debit, credit, balance

    # Take up to last 2 amounts
    last1 = all_amounts[-1]
    last2 = all_amounts[-2] if len(all_amounts) >= 2 else None

    # Assume last1 is ALWAYS balance
    balance = clean_amount_if_needed(last1)

    # Assume last2 (if present) is transaction amount
    if last2:
        tx_amount = clean_amount_if_needed(last2)
        # Strip those amounts from the end of the rest
        desc = rest
        # Remove the last1 and last2 occurrences from the end
        desc = re.sub(rf"{re.escape(last1)}\s*$", "", desc).strip()
        desc = re.sub(rf"{re.escape(last2)}\s*$", "", desc).strip()
    else:
        tx_amount = 0.0
        desc = re.sub(rf"{re.escape(last1)}\s*$", "", rest).strip()

    # 3) Infer debit or credit from description
    lower_desc = desc.lower()
    is_credit = False

    # Very rough heuristics; you can refine based on real samples:
    # SBI often uses "BY" for credits & "TO" for debits.
    if " by " in f" {lower_desc} ":
        is_credit = True
    if " to " in f" {lower_desc} ":
        is_credit = False

    if tx_amount > 0:
        if is_credit:
            credit = tx_amount
            debit = 0.0
        else:
            debit = tx_amount
            credit = 0.0

    return date_str, desc.strip(), debit, credit, balance


def parse_sbi(pdf, filepath):
    """
    Parse SBI-style statements into a list of transaction dicts.
    """
    print(f"[INFO] Parsing 'SBI' format for {filepath}...")
    txns = []

    # Step 1: Extract text per page
    page_texts = extract_text_by_page(pdf)

    # Step 2: Build line list and merge multi-line blocks
    all_lines = []
    for page_text in page_texts:
        lines = split_into_lines(page_text)
        # Filter out clear header/footer noise early
        lines = [ln for ln in lines if not _is_header_or_footer(ln)]
        all_lines.extend(lines)

    # Optionally merge wrapped lines (simple heuristic)
    merged_lines = concat_wrapped_lines(all_lines)

    # Step 3: Group lines into transaction blocks
    current_block_lines = []
    for line in merged_lines:
        if _looks_like_txn_start(line):
            # If we already have a block, finalize it
            if current_block_lines:
                block_text = " ".join(current_block_lines)
                try:
                    date_str, desc, debit, credit, balance = _extract_amounts_and_desc(block_text)
                    txns.append(
                        {
                            "bank": "SBI",
                            "date": date_str,
                            "description": desc,
                            "debit": debit,
                            "credit": credit,
                            "balance": balance,
                            "category": None,
                        }
                    )
                except Exception as e:
                    print(f"[WARN] Failed to parse SBI transaction block: {block_text[:120]!r} ({e})", file=sys.stderr)
                current_block_lines = []

            # start a new block
            current_block_lines = [line]
        else:
            # continuation of current block, if any
            if current_block_lines:
                current_block_lines.append(line)
            else:
                # stray line with no block; ignore
                continue

    # Flush last block
    if current_block_lines:
        block_text = " ".join(current_block_lines)
        try:
            date_str, desc, debit, credit, balance = _extract_amounts_and_desc(block_text)
            txns.append(
                {
                    "bank": "SBI",
                    "date": date_str,
                    "description": desc,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance,
                    "category": None,
                }
            )
        except Exception as e:
            print(f"[WARN] Failed to parse final SBI block: {block_text[:120]!r} ({e})", file=sys.stderr)

    print(f"[SUCCESS] Parsed {len(txns)} SBI transactions from {filepath}.")
    return txns
