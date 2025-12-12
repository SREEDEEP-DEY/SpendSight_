import re
from .utils import clean_amount_if_needed

def parse_idbi(pdf, filepath):
    """
    Parse IDBI Bank format statements.
    """
    print(f"[INFO] Parsing IDBI format for {filepath}...")
    txns = []

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Filter out header/footer lines
        filtered = []
        for line in lines:
            if any(
                x in line
                for x in [
                    "Txn Date",
                    "Value Date",
                    "Cheque",
                    "Description",
                    "CR/DR",
                    "Amount",
                    "Balance",
                    "YOUR A/C STATUS",
                    "Transaction Date From",
                    "A/C NO:",
                    "Page",
                    "IDBI Bank Ltd",
                    "Our Toll-free",
                    "Primary Account Holder",
                    "Account Branch",
                    "Account No",
                    "Customer ID",
                    "Statement Summary",
                ]
            ):
                continue
            filtered.append(line)

        # Parse transaction lines
        # Pattern: Date Description Cr./Dr. INR Amount+Date+Time+Serial Balance
        pattern = r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(Cr\.|Dr\.)\s+INR\s+([\d,]+\.\d{2})(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2}\s+(?:AM|PM))(\d+)\s+([\d,]+\.\d{2})\s*$'

        for line in filtered:
            m = re.match(pattern, line)
            if m:
                (
                    value_date,
                    desc,
                    crdr,
                    amount,
                    txn_date,
                    time,
                    serial,
                    balance
                ) = m.groups()

                amt = clean_amount_if_needed(amount)
                bal = clean_amount_if_needed(balance)

                debit = amt if crdr == "Dr." else 0.0
                credit = amt if crdr == "Cr." else 0.0

                txns.append({
                    "bank": "IDBI",
                    "date": txn_date,  # Using transaction date
                    "description": desc.strip(),
                    "debit": debit,
                    "credit": credit,
                    "balance": bal,
                    "category": None
                })

    print(f"[SUCCESS] Parsed {len(txns)} transactions from {filepath}.")
    return txns