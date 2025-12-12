# regex_engine/regex_classifier.py (ENHANCED VERSION)

import re
from regex_engine.category_rules import CATEGORY_REGEX
from regex_engine.vendor_rules import VENDOR_REGEX
from regex_engine.vendor_map import VENDOR_CATEGORY_MAP
from regex_engine.upi_utils import classify_upi   


# ----------------------------------------------------
# Description normalizer (ENHANCED)
# ----------------------------------------------------
def normalize_desc(desc: str) -> str:
    if not desc:
        return ""

    d = desc.upper()

    # Normalize whitespace
    d = re.sub(r"\s+", " ", d)

    # Fix common "glued" tokens (EXPANDED)
    glue_fixes = {
        "SALARYCREDIT": "SALARY CREDIT",
        "SMSCHRG": "SMS CHRG",
        "ATMWDR": "ATM WDR",
        "ATMWDL": "ATM WDR",
        "INTERNETBANGALORE": "INTERNET BANGALORE",
        "MOBILERECHARGE": "MOBILE RECHARGE",
        "LATEFINEFEES": "LATE FINE FEES",
        "VLPCHARGES": "VLP CHARGES",
        "TRANSFERTOANIL": "TRANSFER TO ANIL",
        "DMART": "D MART",
        "BIGBASKET": "BIG BASKET",
        "PHONEPE": "PHONE PE",
        "GOOGLEPAY": "GOOGLE PAY",
        "BHARATPET": "BHARAT PETROLEUM",
        "HINDPETRO": "HINDUSTAN PETROLEUM",
        "INDIANOIL": "INDIAN OIL",
    }
    for bad, good in glue_fixes.items():
        d = d.replace(bad, good)

    # Collapse UPI noise (keep more info for debugging)
    d = re.sub(r"UPI/DR/[\w\d/.\-]+/", "UPI/", d)
    d = re.sub(r"UPI/CR/[\w\d/.\-]+/", "UPI/", d)
    d = re.sub(r"UPI/\d{12,}/", "UPI/", d)

    # Strip transaction IDs but keep short numbers
    d = re.sub(r"\b\d{12,}\b", " ", d)

    # Collapse double spaces
    d = re.sub(r"\s{2,}", " ", d).strip()

    return d


# ----------------------------------------------------
# Vendor map helpers (ENHANCED with fuzzy matching)
# ----------------------------------------------------
VENDOR_KEYS = sorted(VENDOR_CATEGORY_MAP.keys(), key=len, reverse=True)


def extract_vendor_from_map(desc_norm: str) -> tuple[str, float] | None:
    """
    Enhanced vendor extraction with partial matching and scoring.
    Returns: (vendor_key, confidence_score) or None
    """
    desc_words = set(desc_norm.split())
    
    # First pass: exact substring match (highest confidence)
    for key in VENDOR_KEYS:
        if key in desc_norm:
            return key, 0.95
    
    # Second pass: word-level matching (medium confidence)
    for key in VENDOR_KEYS:
        key_words = set(key.split())
        # If 80%+ of vendor key words are present
        if key_words and len(key_words & desc_words) / len(key_words) >= 0.8:
            return key, 0.85
    
    # Third pass: partial word matching (lower confidence)
    for key in VENDOR_KEYS:
        key_parts = key.split()
        if len(key_parts) == 1:
            # Single word - check if it's a substring of any word
            if any(key in word for word in desc_words):
                return key, 0.75
        else:
            # Multi-word - check if main part exists
            main_part = key_parts[0]  # Usually brand name is first
            if main_part in desc_norm:
                return key, 0.80
    
    return None


# ----------------------------------------------------
# Extra non-vendor rules (ENHANCED patterns)
# ----------------------------------------------------
SALARY_RE = re.compile(r"\bSALARY\b", re.I)
ATM_WDR_RE = re.compile(r"\bATM\s*WD[RL]?\b", re.I)
SMS_CHG_RE = re.compile(r"\bSMS\b", re.I)
EMI_RE = re.compile(r"\bEMI\b|\bLOAN\b", re.I)
ATM_DEP_RE = re.compile(r"\bATM\s*DEP", re.I)
INT_PD_RE = re.compile(r"\bINT[.\s]*PD\b|\bINTEREST", re.I)
QTR_CHG_RE = re.compile(r"QUARTER|QTRLY|AVG.*BAL", re.I)
ELEC_RE = re.compile(r"\bELECTRIC", re.I)
GAS_RE = re.compile(r"\bGAS\b|\bLPG\b", re.I)
INS_RE = re.compile(r"\bPMSBY\b|\bPMJJBY\b|\bINSURANCE\b", re.I)
MOBILE_RECHARGE_RE = re.compile(r"\bMOBILE\b|\bRECHARGE\b|\bPREPAID\b", re.I)
LATE_FEE_RE = re.compile(r"\bLATE\b|\bFINE\b|\bFEE", re.I)
VLP_CHARGES_RE = re.compile(r"\bVLP\b", re.I)
TRANSFER_RE = re.compile(r"\bNEFT\b|\bIMPS\b|\bRTGS\b", re.I)


def classify_with_regex(description: str):
    """
    Enhanced regex classifier with better pattern matching.

    Returns:
        category: str or "PENDING"
        subcategory: str | None
        vendor: str | None
        confidence: float
        meta: dict
    """
    if not description:
        return "PENDING", None, None, 0.0, {"reason": "empty"}

    raw_text = description.strip()
    text_lower = raw_text.lower()
    text_norm = normalize_desc(raw_text)  # UPPERCASED + cleaned
    meta: dict = {}

    category: str | None = None
    subcategory: str | None = None
    vendor: str | None = None
    confidence: float = 0.0

    # ------------------------------------------------
    # 0) UPI-specific extractor (ENHANCED - extract merchant first)
    # ------------------------------------------------
    # First, try to extract UPI merchant and match against vendor map
    if "UPI" in text_norm:
        # Try multiple UPI patterns to extract merchant name
        upi_patterns = [
            r"UPI.*?[-/]([A-Z]{3,}(?:\s+[A-Z]+)?)\b",  # UPI-DR-SWIGGY-PAY
            r"UPI/\d+/([A-Z\s]{3,}?)(?:/|@|\s|$)",     # UPI/036509813258/HOTEL RAJ
            r"([A-Z]{3,}(?:\s+[A-Z]+)?)@(?:ybl|paytm|oksbi|okhdfcbank)",  # SWIGGY@ybl
        ]
        
        for pattern in upi_patterns:
            upi_match = re.search(pattern, text_norm)
            if upi_match:
                upi_merchant = upi_match.group(1).strip()
                # Try to match against vendor map
                for key in VENDOR_KEYS:
                    if key in upi_merchant or upi_merchant in key:
                        cat, subcat = VENDOR_CATEGORY_MAP[key]
                        category = cat
                        subcategory = subcat
                        vendor = key.title()
                        confidence = 0.90
                        meta["matched_rule"] = "upi_vendor"
                        meta["upi_merchant"] = upi_merchant
                        return category, subcategory, vendor, confidence, meta
    
    # Fall back to general UPI classification
    upi_cat, upi_sub, upi_vendor, upi_conf, upi_meta = classify_upi(text_norm)
    if upi_cat is not None and upi_cat != "PENDING":
        # Only return UPI result if it's NOT a generic transfer
        # Let vendor map handle known merchants in UPI transactions
        if upi_cat != "Transfers" or upi_sub != "ToBusiness":
            meta.update(upi_meta)
            meta.setdefault("matched_rule", "upi")
            return upi_cat, upi_sub, upi_vendor, upi_conf, meta

    # ------------------------------------------------
    # 1) Vendor-based classification via vendor_map (ENHANCED)
    # ------------------------------------------------
    vendor_match = extract_vendor_from_map(text_norm)
    if vendor_match:
        vendor_key, vendor_confidence = vendor_match
        cat, subcat = VENDOR_CATEGORY_MAP[vendor_key]

        category = cat
        subcategory = subcat
        vendor = vendor_key.title()
        confidence = vendor_confidence
        meta["matched_rule"] = "vendor_map"
        meta["vendor_key"] = vendor_key
        
        # Return immediately for high-confidence vendor matches
        if confidence >= 0.85:
            return category, subcategory, vendor, confidence, meta

    # ------------------------------------------------
    # 2) Non-vendor semantic rules (ENHANCED)
    # ------------------------------------------------
    # EMI Detection (EARLY - before other rules)
    if re.search(r"\bEMIPAYMENT\b", text_norm, re.I) or re.search(r"\bHDFC[-\s]*LOAN\b", text_norm, re.I):
        category = "Debt"
        subcategory = "LoanEMI"
        vendor = vendor or "HDFC Loan"
        confidence = 0.95
        meta["matched_rule"] = "emi"
        return category, subcategory, vendor, confidence, meta
    
    if SALARY_RE.search(text_norm) or "CREDIT" in text_norm and "SALARY" in text_norm:
        category = "Income"
        subcategory = "Salary"
        vendor = vendor or "Employer"
        confidence = 0.98
        meta["matched_rule"] = "salary"
        return category, subcategory, vendor, confidence, meta

    elif EMI_RE.search(text_norm):
        category = "Debt"
        subcategory = "LoanEMI"
        vendor = vendor or "LoanProvider"
        confidence = 0.90
        meta["matched_rule"] = "emi"
        return category, subcategory, vendor, confidence, meta

    elif ATM_WDR_RE.search(text_norm):
        category = "Cash"
        subcategory = "ATMWithdrawal"
        vendor = vendor or "ATM"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "atm_wdr"

    elif ATM_DEP_RE.search(text_norm):
        category = "Cash"
        subcategory = "ATMDeposit"
        vendor = vendor or "ATM"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "atm_dep"

    elif INT_PD_RE.search(text_norm):
        category = "Income"
        subcategory = "Interest"
        vendor = vendor or "BankInterest"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "interest"

    elif QTR_CHG_RE.search(text_norm):
        category = "BankCharges"
        subcategory = "BalanceCharge"
        vendor = vendor or "BankFee"
        confidence = max(confidence, 0.85)
        meta["matched_rule"] = "qtr_charge"

    elif SMS_CHG_RE.search(text_norm):
        category = "BankCharges"
        subcategory = "SMS"
        vendor = vendor or "BankFee"
        confidence = max(confidence, 0.85)
        meta["matched_rule"] = "sms_charge"

    elif ELEC_RE.search(text_norm):
        category = "Utilities"
        subcategory = "Electricity"
        vendor = vendor or "ElectricityBoard"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "electricity"

    elif GAS_RE.search(text_norm):
        category = "Utilities"
        subcategory = "Gas"
        vendor = vendor or "GasProvider"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "gas"

    elif INS_RE.search(text_norm):
        category = "Insurance"
        subcategory = "GovtScheme"
        vendor = vendor or "GovtInsurance"
        confidence = max(confidence, 0.90)
        meta["matched_rule"] = "govt_insurance"

    elif TRANSFER_RE.search(text_norm) and not category:
        category = "Transfers"
        subcategory = "ToPerson"
        vendor = vendor or "BankTransfer"
        confidence = max(confidence, 0.70)
        meta["matched_rule"] = "bank_transfer"

    # ------------------------------------------------
    # 2.5) POS Transaction Handling (BEFORE category regex)
    # ------------------------------------------------
    if not category and re.search(r"\b(?:VISA|IDBV|MASTER|RUPAY)[-\s]*POS\b", text_norm, re.I):
        # Extract merchant name from POS transaction
        pos_match = re.search(r"POS/([^/\s]+(?:\s+[^/\s]+){0,3})", text_norm, re.I)
        if pos_match:
            pos_merchant = pos_match.group(1).strip()
            # Try to match against vendor map
            for key in VENDOR_KEYS:
                if key in pos_merchant:
                    cat, subcat = VENDOR_CATEGORY_MAP[key]
                    category = cat
                    subcategory = subcat
                    vendor = key.title()
                    confidence = 0.85
                    meta["matched_rule"] = "pos_vendor"
                    meta["pos_merchant"] = pos_merchant
                    return category, subcategory, vendor, confidence, meta

    # ------------------------------------------------
    # 3) Fallback to CATEGORY_REGEX (ENHANCED)
    # ------------------------------------------------
    if category is None:
        for cat_label, patterns in CATEGORY_REGEX.items():
            for pat in patterns:
                # Try both normalized and lower case
                if re.search(pat, text_lower, re.I) or re.search(pat, text_norm, re.I):
                    parts = cat_label.split(".")
                    category = parts[0]
                    subcategory = parts[1] if len(parts) > 1 else None
                    confidence = max(confidence, 0.80)
                    meta["matched_rule"] = "category_regex"
                    meta["category_hit"] = pat
                    break
            if category:
                break

    # ------------------------------------------------
    # 4) Fallback vendor detection using VENDOR_REGEX (ENHANCED)
    # ------------------------------------------------
    if vendor is None:
        for vendor_name, patterns in VENDOR_REGEX.items():
            for pat in patterns:
                # More flexible matching
                if re.search(pat, text_lower, re.I) or re.search(pat, text_norm, re.I):
                    vendor = vendor_name
                    meta["vendor_hit"] = pat
                    meta["matched_rule"] = meta.get("matched_rule", "vendor_regex")
                    if category is None:
                        category = "Uncategorized"
                    confidence = max(confidence, 0.70)
                    break
            if vendor:
                break

    # ------------------------------------------------
    # 5) Enhanced keyword detection for common patterns
    # ------------------------------------------------
    if category is None:
        keywords_map = {
            "RESTAURANT": ("Dining", "Restaurant", 0.75),
            "HOTEL": ("Dining", "Restaurant", 0.75),
            "CAFE": ("Dining", "Cafe", 0.75),
            "PETROL": ("Transport", "Fuel", 0.80),
            "PETROLEUM": ("Transport", "Fuel", 0.80),
            "GROCERY": ("Groceries", "LocalShops", 0.75),
            "SUPERMARKET": ("Groceries", "Supermarket", 0.75),
            "MEDICAL": ("Shopping", "Pharmacy", 0.75),
            "PHARMACY": ("Shopping", "Pharmacy", 0.75),
            "TAXI": ("Transport", "Cab", 0.75),
            "CAB": ("Transport", "Cab", 0.75),
        }
        
        for keyword, (cat, subcat, conf) in keywords_map.items():
            if keyword in text_norm:
                category = cat
                subcategory = subcat
                confidence = max(confidence, conf)
                meta["matched_rule"] = "keyword_detection"
                meta["keyword"] = keyword
                break

    # ------------------------------------------------
    # 6) Final fallback → PENDING for MiniLM / LLM
    # ------------------------------------------------
    if category is None:
        category = "PENDING"
        subcategory = None
        confidence = 0.0
        meta.setdefault("reason", "no_regex_match")
        meta["text_norm"] = text_norm  # For debugging

    return category, subcategory, vendor, confidence, meta