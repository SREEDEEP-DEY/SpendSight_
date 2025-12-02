# parsers/pnb.py
import sys
from .utils import clean_amount_if_needed


def parse_pnb(pdf, filepath):
    """
    Parse Punjab National Bank-style statements (your PNB/Federal tabular one).
    """
    print(f"[INFO] Parsing 'PNB' format for {filepath}...")
    txns = []
    table_settings = {"vertical_strategy": "text", "horizontal_strategy": "text"}

    for page in pdf.pages:
        tables = page.extract_tables(table_settings)
        if not tables:
            continue

        current = None
        for row in tables[0]:
            if row and len(row) >= 5:
                # New transaction row
                if row[0] and row[0] != "DATE" and "Continued" not in row[0]:
                    try:
                        if current:
                            txns.append(current)

                        date = row[0].replace("\n", "")
                        desc_raw = (row[2] or "").replace("\n", " ")
                        credit_str, balance_str = row[3], row[4]
                        debit, credit = 0.0, 0.0
                        desc = desc_raw

                        if credit_str and clean_amount_if_needed(credit_str) > 0:
                            credit = clean_amount_if_needed(credit_str)
                        else:
                            # Inline debit at end of description
                            import re
                            m = re.search(r"([\d,]+\.\d{2})\s*$", desc_raw)
                            if m:
                                debit = clean_amount_if_needed(m.group(1))
                                desc = re.sub(r"([\d,]+\.\d{2})\s*$", "", desc_raw).strip()

                        current = {
                            "bank": "PNB",
                            "date": date,
                            "description": desc.strip(),
                            "debit": debit,
                            "credit": credit,
                            "balance": clean_amount_if_needed(balance_str),
                            "category": None,
                        }
                    except Exception as e:
                        print(f"[WARN] Malformed PNB row: {row} ({e})", file=sys.stderr)
                        current = None

                # continuation line
                elif current and (row[0] is None or row[0] == "") and row[2]:
                    current["description"] += " " + row[2].replace("\n", " ")

        if current:
            txns.append(current)

    print(f"[SUCCESS] Parsed {len(txns)} transactions from {filepath}.")
    return txns
