import re
from .utils import clean_amount_if_needed

DATE_REGEX = re.compile(r"^\d{2}-\d{2}-\d{4}")
AMOUNT_REGEX = re.compile(
    r"(?P<deposit>[\d,]+\.\d{2}|0)\s+"
    r"(?P<withdrawal>[\d,]+\.\d{2}|0)\s+"
    r"(?P<balance>[\d,]+\.\d{2})$"
)

def parse_icici(pdf, filepath):
    print(f"[INFO] Parsing ICICI Bank format for {filepath}...")
    txns = []
    buffer = []

    def flush_buffer(buf):
        """Convert buffered lines into a single transaction dict"""
        if not buf:
            return None
        
        # Join all lines
        text = " ".join(buf)

        # Find amount line
        m = AMOUNT_REGEX.search(text)
        if not m:
            return None

        deposit  = clean_amount_if_needed(m.group("deposit"))
        withdrawal = clean_amount_if_needed(m.group("withdrawal"))
        balance = clean_amount_if_needed(m.group("balance"))

        # Remove amount part from text
        text = AMOUNT_REGEX.sub("", text).strip()

        # First token is date
        date = text[:10]
        particulars = text[10:].strip()

        return {
            "bank": "ICICI",
            "date": date,
            "description": particulars,
            "credit": deposit,
            "debit": withdrawal,
            "balance": balance,
            "category": None,
        }

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # New transaction starts
            if DATE_REGEX.match(line):
                if buffer:
                    txn = flush_buffer(buffer)
                    if txn:
                        txns.append(txn)
                buffer = [line]
            else:
                buffer.append(line)

    # Flush last
    if buffer:
        txn = flush_buffer(buffer)
        if txn:
            txns.append(txn)

    print(f"[SUCCESS] Parsed {len(txns)} transactions from {filepath}.")
    return txns
