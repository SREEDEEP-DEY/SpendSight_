# parsers/bob.py
import re
import sys
from .utils import clean_amount_if_needed


def parse_bob(pdf, filepath):
    """
    Parse Bank of Baroda (BOB) format statements.
    """
    print(f"[INFO] Parsing 'BOB' format for {filepath}...")
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
                    "Se-",
                    "rial",
                    "Transac-",
                    "tion",
                    "Value",
                    "Description",
                    "Cheque",
                    "Debit",
                    "Credit",
                    "Balance",
                    "Continued on next",
                    "Continuedonnextpage",
                    "Statement of Account",
                    "AccountHolder:",
                    "AccountNumber:",
                    "GeneratedOn:",
                    "End of statement",
                    "From01-",
                    "From 01-",
                ]
            ):
                continue
            filtered.append(line)

        # Merge lines to form complete transaction strings
        merged = []
        i = 0
        while i < len(filtered):
            line = filtered[i]
            if re.match(r"^\d+\s+\d{2}-\d{2}-", line):
                buffer = line
                i += 1
                while i < len(filtered):
                    next_line = filtered[i]
                    if re.match(r"^\d+\s+\d{2}-\d{2}-", next_line):
                        break
                    buffer += " " + next_line
                    i += 1

                    year_count = len(re.findall(r"\b\d{4}\b", buffer))
                    has_balance = bool(re.search(r"[\d,]+\.\d{2}", buffer))
                    if year_count >= 2 and has_balance:
                        break

                merged.append(buffer.strip())
            else:
                i += 1

        # Parse merged transaction lines
        for line in merged:
            m = re.match(r"^(\d+)\s+(\d{2}-\d{2}-)\s+(\d{2}-\d{2}-)\s+(.+)$", line)
            if not m:
                continue

            serial = m.group(1)
            date1_partial = m.group(2)
            date2_partial = m.group(3)
            rest = m.group(4)

            years = re.findall(r"\b(\d{4})\b", rest)
            if len(years) < 2:
                continue

            year1, year2 = years[0], years[1]
            date1 = date1_partial + year1
            date2 = date2_partial + year2  # currently unused

            rest_clean = rest
            for year in years[:2]:
                rest_clean = rest_clean.replace(year, "", 1)

            tokens = rest_clean.split()

            balance = None
            credit = None
            debit = None
            amounts = []
            desc_tokens = []

            for token in tokens:
                if re.match(r"^[\d,]+\.\d{2}$", token):
                    amounts.append(token)
                elif token == "-":
                    amounts.append(token)
                else:
                    if not amounts or len(amounts) < 3:
                        desc_tokens.append(token)

            if amounts and re.match(r"^[\d,]+\.\d{2}$", amounts[-1]):
                balance = amounts[-1]
                amounts = amounts[:-1]
            else:
                continue

            if amounts:
                credit_token = amounts[-1]
                credit = credit_token if credit_token != "-" else None
                amounts = amounts[:-1]

            if amounts:
                debit_token = amounts[-1]
                debit = debit_token if debit_token != "-" else None
                amounts = amounts[:-1]

            description = " ".join(desc_tokens).strip()

            txns.append(
                {
                    "bank": "BOB",
                    "date": date1,  # use first date as txn date
                    "description": description,
                    "debit": clean_amount_if_needed(debit) if debit else 0.0,
                    "credit": clean_amount_if_needed(credit) if credit else 0.0,
                    "balance": clean_amount_if_needed(balance),
                    "category": None,
                }
            )

    print(f"[SUCCESS] Parsed {len(txns)} transactions from {filepath}.")
    return txns
