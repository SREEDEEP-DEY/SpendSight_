# regex_engine/upi_utils.py

import re
from typing import Optional, Tuple, Dict

# ----------------------------------------------------
# UPI patterns
# ----------------------------------------------------

# Detect UPI-style transactions
UPI_HINT_RE = re.compile(r"\bUPI[/\-]|/UPI/|VPA\b", re.IGNORECASE)

# Extract VPA handles like something@ybl, zomato@upi, hpcl001@okhdfcbank
VPA_RE = re.compile(r"([A-Za-z0-9.\-]+)@([A-Za-z0-9]+)", re.IGNORECASE)

# Also match UPI transaction IDs (backup if no VPA found)
UPI_ID_RE = re.compile(r"UPI/(\d{12,15})/([^/\s]+)", re.IGNORECASE)


# ----------------------------------------------------
# UPI merchant → category map (India-focused)
# Based on actual patterns from the bank statement
# ----------------------------------------------------
UPI_MERCHANT_MAP: Dict[str, Tuple[str, str]] = {
    # ========================================
    # FOOD & DINING
    # ========================================
    "ZOMATO": ("Dining", "FoodDelivery"),
    "SWIGGY": ("Dining", "FoodDelivery"),
    "DUNZO": ("Dining", "FoodDelivery"),
    "EATFIT": ("Dining", "FoodDelivery"),
    "BOX8": ("Dining", "FoodDelivery"),
    "FAASOS": ("Dining", "FoodDelivery"),
    
    # Restaurants (from statement)
    "HOTEL RAJ": ("Dining", "Restaurant"),
    "HOTEL RAYAT": ("Dining", "Restaurant"),
    "HOTEL SAMMAN": ("Dining", "Restaurant"),
    "GIRIDHAR VEG": ("Dining", "Restaurant"),
    "SAGAR RESTAURANT": ("Dining", "Restaurant"),
    
    # Fast Food Chains
    "KFC": ("Dining", "Restaurant"),
    "MCDONALD": ("Dining", "Restaurant"),
    "DOMINOS": ("Dining", "Restaurant"),
    "PIZZA HUT": ("Dining", "Restaurant"),
    "PIZZAHUT": ("Dining", "Restaurant"),
    
    # Cafes
    "CCD": ("Dining", "Cafe"),
    "CAFECOFFEEDAY": ("Dining", "Cafe"),
    "PUNERI CHAI": ("Dining", "Cafe"),
    
    # Snacks & Quick Bites (from statement)
    "SHETKARI BHOJANALAY": ("Dining", "SnacksAndBeverages"),
    "SHREE SAINATH BHEL": ("Dining", "SnacksAndBeverages"),
    "MEENA SNACKS": ("Dining", "SnacksAndBeverages"),
    "DEEPAK SNACKS": ("Dining", "SnacksAndBeverages"),
    "SAI FOODS": ("Dining", "SnacksAndBeverages"),
    "ANUSHKA BHEL": ("Dining", "SnacksAndBeverages"),
    "BALAJI FAST FOOD": ("Dining", "SnacksAndBeverages"),
    "HARSH TEA": ("Dining", "SnacksAndBeverages"),
    "SONAI DAVANGIRI": ("Dining", "SnacksAndBeverages"),
    
    # ========================================
    # GROCERIES
    # ========================================
    "DMART": ("Groceries", "Supermarket"),
    "BIGBASKET": ("Groceries", "OnlineGroceries"),
    "BBDAILY": ("Groceries", "OnlineGroceries"),
    "BB-": ("Groceries", "OnlineGroceries"),
    "JIOMART": ("Groceries", "Supermarket"),
    "JIO MART": ("Groceries", "Supermarket"),
    "ZEPT": ("Groceries", "OnlineGroceries"),
    "ZEPTO": ("Groceries", "OnlineGroceries"),
    "BLINKIT": ("Groceries", "OnlineGroceries"),
    "NATURESBASKET": ("Groceries", "Supermarket"),
    "SPENCERS": ("Groceries", "Supermarket"),
    "MOREMEGASTORE": ("Groceries", "Supermarket"),
    "STARQUICK": ("Groceries", "Supermarket"),
    
    # Local groceries from statement
    "GURUKRUPA SUPER MARKET": ("Groceries", "LocalShops"),
    "GURUKRUPA": ("Groceries", "LocalShops"),
    "KATRAJ DAIRY": ("Groceries", "LocalShops"),
    "TRUPTI": ("Groceries", "LocalShops"),
    "VISHAL VEGETABLES": ("Groceries", "LocalShops"),
    "COSMOS": ("Groceries", "LocalShops"),
    "PJSB": ("Groceries", "LocalShops"),
    "SHRI AAIJI": ("Groceries", "LocalShops"),
    
    # ========================================
    # SHOPPING
    # ========================================
    "AMAZON": ("Shopping", "Online"),
    "FLIPKART": ("Shopping", "Online"),
    "AJIO": ("Shopping", "Fashion"),
    "MYNTRA": ("Shopping", "Fashion"),
    "TATACLIQ": ("Shopping", "Online"),
    "TATANEU": ("Shopping", "Online"),
    "NYKAA": ("Shopping", "Beauty"),
    "MEESHO": ("Shopping", "Online"),
    "SNAPDEAL": ("Shopping", "Online"),
    "SHOPPERSSTOP": ("Shopping", "Fashion"),
    "LIFESTYLE": ("Shopping", "Fashion"),
    "MAXFASHION": ("Shopping", "Fashion"),
    "CROMA": ("Shopping", "Electronics"),
    "VIJAYSALES": ("Shopping", "Electronics"),
    "RELIANCE DIGITAL": ("Shopping", "Electronics"),
    "REL DIGITAL": ("Shopping", "Electronics"),
    "PANTALOONS": ("Shopping", "Fashion"),
    
    # Local shops from statement
    "BOMBAY STATIONERS": ("Shopping", "Stationery"),
    "IPRINT ENTERPRISES": ("Shopping", "Stationery"),
    "RIBBONS AND BALLOONS": ("Shopping", "Decorations"),
    "NEW MAYUR COLLECTION": ("Shopping", "Fashion"),
    "SUYASH DRESSES": ("Shopping", "Fashion"),
    "SHREE ENTERPRISES": ("Shopping", "GeneralStore"),
    "VIDHATA XEROX": ("Shopping", "Stationery"),
    "JEEVANDEEP STATIONERY": ("Shopping", "Stationery"),
    "PAVAN APPLE STORE": ("Shopping", "Electronics"),
    
    # Medical/Pharmacy
    "SHRUTI MEDICAL": ("Shopping", "Pharmacy"),
    "DHARESHWAR MEDICAL": ("Shopping", "Pharmacy"),
    "SHRIKRISHNA MEDICAL": ("Shopping", "Pharmacy"),
    
    # ========================================
    # TRANSPORT
    # ========================================
    "UBER": ("Transport", "Cab"),
    "OLA": ("Transport", "Cab"),
    "RAPIDO": ("Transport", "BikeTaxi"),
    "MERU": ("Transport", "Cab"),
    "REDBUS": ("Transport", "PublicTransport"),
    "IRCTC": ("Transport", "PublicTransport"),
    
    # ========================================
    # FUEL (from statement)
    # ========================================
    "HPCL": ("Transport", "Fuel"),
    "BPCL": ("Transport", "Fuel"),
    "IOCL": ("Transport", "Fuel"),
    "INDIANOIL": ("Transport", "Fuel"),
    "BHARATPET": ("Transport", "Fuel"),
    "HINDPETRO": ("Transport", "Fuel"),
    
    # ========================================
    # UTILITIES
    # ========================================
    # Mobile/Telecom
    "AIRTEL": ("Utilities", "MobileRecharge"),
    "JIO": ("Utilities", "MobileRecharge"),
    "VODAFONE": ("Utilities", "MobileRecharge"),
    "VI-": ("Utilities", "MobileRecharge"),
    "VI ": ("Utilities", "MobileRecharge"),
    "BSNL": ("Utilities", "MobileRecharge"),
    
    # DTH
    "SUN DIRECT": ("Utilities", "DTH"),
    "TATASKY": ("Utilities", "DTH"),
    "D2H": ("Utilities", "DTH"),
    "DISHTV": ("Utilities", "DTH"),
    
    # Gas
    "HPGAS": ("Utilities", "Gas"),
    "HP GAS": ("Utilities", "Gas"),
    
    # Electricity
    "BESCOM": ("Utilities", "Electricity"),
    "BSES": ("Utilities", "Electricity"),
    "TNEB": ("Utilities", "Electricity"),
    "MSEDCL": ("Utilities", "Electricity"),
    "TORRENTPOWER": ("Utilities", "Electricity"),
    
    # ========================================
    # ENTERTAINMENT
    # ========================================
    "NETFLIX": ("Entertainment", "Streaming"),
    "SPOTIFY": ("Entertainment", "Music"),
    "HOTSTAR": ("Entertainment", "Streaming"),
    "DISNEY": ("Entertainment", "Streaming"),
    "SONYLIV": ("Entertainment", "Streaming"),
    "ZEE5": ("Entertainment", "Streaming"),
    "PRIME VIDEO": ("Entertainment", "Streaming"),
    
    # ========================================
    # WALLETS & PAYMENT GATEWAYS
    # ========================================
    "PAYTM": ("Transfers", "ToBusiness"),
    "PHONEPE": ("Transfers", "ToBusiness"),
    "GOOGLEPAY": ("Transfers", "ToBusiness"),
    "GPAY": ("Transfers", "ToBusiness"),
    "AMAZONPAY": ("Transfers", "ToBusiness"),
    "MOBIKWIK": ("Transfers", "ToBusiness"),
    "FREECHARGE": ("Transfers", "ToBusiness"),
    "RAZORPAY": ("Transfers", "ToBusiness"),
    "BILLDESK": ("Transfers", "ToBusiness"),
    "CASHFREE": ("Transfers", "ToBusiness"),
    "BHARATPEMERCHANT": ("Transfers", "ToBusiness"),
    "BHARATPE": ("Transfers", "ToBusiness"),
    
    # ========================================
    # TRAVEL
    # ========================================
    "MAKEMYTRIP": ("Travel", "FlightTickets"),
    "EASEMYTRIP": ("Travel", "FlightTickets"),
    "YATRA": ("Travel", "FlightTickets"),
    "CLEARTRIP": ("Travel", "FlightTickets"),
    "GOIBIBO": ("Travel", "Accommodation"),
    "OYO": ("Travel", "Accommodation"),
    
    # ========================================
    # GAMING
    # ========================================
    "DREAM11": ("Leisure", "Gaming"),
    "MPL": ("Leisure", "Gaming"),
    "RUMMYCIRCLE": ("Leisure", "Gaming"),
    "GAMING": ("Leisure", "Gaming"),
    
    # ========================================
    # EDUCATION
    # ========================================
    "SIMACES LEARNING": ("Education", "Courses"),
    
    # ========================================
    # INSURANCE
    # ========================================
    "LIC": ("Insurance", "Life"),
    "HDFCLIFE": ("Insurance", "Life"),
    "SBILIFE": ("Insurance", "Life"),
    "ICICIPRULIFE": ("Insurance", "Life"),
    
    # ========================================
    # INVESTMENTS
    # ========================================
    "ZERODHA": ("Investment", "Stocks"),
    "UPSTOX": ("Investment", "Stocks"),
    "GROWW": ("Investment", "Stocks"),
    "ANGEL ONE": ("Investment", "Stocks"),
    
    # ========================================
    # GENERIC SERVICES
    # ========================================
    "BBPS": ("Utilities", "BillPayment"),
    
    # ========================================
    # MISCELLANEOUS
    # ========================================
    "RAJ PAN SHOP": ("Miscellaneous", "PanShop"),
    "MUTAI PAN SHOP": ("Miscellaneous", "PanShop"),
}

# Common Indian names/person indicators (for person detection)
COMMON_INDIAN_NAME_PARTS = {
    "KUMAR", "RAJ", "SINGH", "SHARMA", "VERMA", "GUPTA", "PATEL",
    "ANIL", "SUNIL", "VINOD", "RAJESH", "RAMESH", "MAHESH", "DINESH",
    "PRIYA", "NEHA", "POOJA", "ANJALI", "KAVITA", "SUNITA",
    "MR", "MRS", "MS", "DR", "MISS", "M/S",
    "SAI", "GANESH", "SHIVA", "KRISHNA", "RAMA",
    "PRAKASH", "ASHOK", "VITTHAL", "SUBHASH", "MAHADEO",
    "BHARGAV", "MANDAR", "CHAITALI", "BIPIN", "ASHISH",
    "RUPESH", "SAJAL", "RAVI", "DEOCHAND", "VINAYAK",
    "PRAJAKTA", "KAMALESH", "HRUSHIKESH", "CHHAYA",
    # Add more from the statement
    "PRAMOD", "OMPRAKASH", "SANDEEP", "KAVIRATNA", "MALLESH",
    "PRABHAKAR", "SADHU", "MOTALIB", "VAGAD", "BANGARATAL",
    "WAGHMARE", "GAGANDEEP", "MOHD", "MOHAMMAD", "AMJAD",
    "BABLU", "GAURISHANKAR", "BHAVESH", "CHUNNILAL", "GANESH",
    "VIJAYKUMAR", "DAGADU", "NALAWADE", "AVINASH", "GAUTAM",
    "DNYANESHWAR", "KONDIBA", "MARGALE", "MINA", "SURESH",
    "AKSHAY", "BABANRAO", "PATHARE", "YASHASHREE", "JAYANT",
    "SADAVARTE", "ANAND", "HANUMANT", "JAGTAP", "KIRATAKARVE",
    "MANOHAR", "BUDHKAR", "SADHANA", "REKHA", "SURYAKANT",
    "DHOTRE", "SHITOLE", "KALURAM", "PAWAR", "MANOJ",
    "JAGADE", "NATHURAM", "WADEKAR", "DILIP", "MUDHOLKAR",
    "INAMDAR", "SUVARNA", "PASALKAR", "RAJENDRA", "DINKAR",
    "DAHATONDE", "SALUNKE", "MANDA", "MEHTA", "NATH",
    "KASHYA", "CHOUDHARY", "SUPEKAR", "UTTAM", "VIKAS",
    "PAKHARE", "CHANDRAKANT", "GAWDEY", "RAO", "MUDHOLKAR",
    "SHETE", "POPAT", "KADAM", "KALE", "SHIVAJI",
    "SAPA", "HARIPPYA", "RAJURKAR", "VASANT", "SWATI",
    "MUDSHINGIKAR", "SAKUNDE", "PUJARI", "WAGH", "KAMBLE",
    "ATUL", "YUVARAJ", "SHINDE", "DHAKANE", "GUPTA",
    "KRISHNA", "CHAVAN", "SANJEEVKUMAR", "ANAPPA",
}

# Pre-sort keys to match more specific ones first
UPI_KEYS = sorted(UPI_MERCHANT_MAP.keys(), key=len, reverse=True)


def _looks_like_person(prefix: str) -> bool:
    """
    Enhanced heuristic to detect person names in UPI handles.
    
    Rules:
    1. Contains common Indian name parts
    2. No obvious merchant keywords
    3. Contains spaces or multiple capital letters (like names)
    4. Has title indicators (Mr, Mrs, etc.)
    """
    p = prefix.upper()
    
    # First check: if it matches known merchants, it's not a person
    if any(k in p for k in UPI_KEYS):
        return False
    
    # Check for title indicators
    if any(title in p for title in ["MR ", "MRS ", "MS ", "DR ", "MISS "]):
        return True
    
    # Check for common name parts
    name_parts = p.split()
    if any(part in COMMON_INDIAN_NAME_PARTS for part in name_parts):
        return True
    
    # Check if contains common name substrings
    if any(name in p for name in COMMON_INDIAN_NAME_PARTS):
        return True
    
    # If has multiple words and no digits, likely a person
    if len(name_parts) >= 2 and not any(ch.isdigit() for ch in p):
        return True
    
    # If contains typical person name patterns (FirstName LastName structure)
    if " " in p and len(name_parts) >= 2 and len(name_parts) <= 4:
        # Most person names are 2-4 words
        return True
    
    return False


def classify_upi(text_norm: str) -> Tuple[Optional[str], Optional[str], Optional[str], float, Dict]:
    """
    Enhanced UPI transaction classifier based on actual bank statement patterns.
    
    Args:
        text_norm: uppercased, cleaned description (e.g. from normalize_desc())
    
    Returns:
        (category, subcategory, vendor, confidence, meta)
        If not a UPI transaction, returns (None, None, None, 0.0, {}).
    """
    # Quick check: if there's no UPI hint at all, bail out
    if not UPI_HINT_RE.search(text_norm):
        return None, None, None, 0.0, {}
    
    meta: Dict = {"matched_rule": "upi"}
    
    # Try to find a VPA handle in the text
    m = VPA_RE.search(text_norm)
    if m:
        handle_prefix = m.group(1).upper()
        handle_domain = m.group(2).upper()
        full_handle = f"{handle_prefix}@{handle_domain}"
        meta["handle"] = full_handle
        meta["handle_prefix"] = handle_prefix
        meta["handle_domain"] = handle_domain
        
        # 1) Try merchant keyword map (most specific)
        for key in UPI_KEYS:
            if key in handle_prefix:
                category, subcat = UPI_MERCHANT_MAP[key]
                meta["matched_merchant_key"] = key
                return category, subcat, handle_prefix.title(), 0.90, meta
        
        # 2) Check if it looks like a person
        if _looks_like_person(handle_prefix):
            return "Transfers", "ToPerson", handle_prefix.title(), 0.80, {
                **meta,
                "reason": "upi_person_detected",
            }
        
        # 3) Otherwise, generic business transfer
        return "Transfers", "ToBusiness", handle_prefix.title(), 0.70, {
            **meta,
            "reason": "upi_business_generic",
        }
    
    # If no VPA found, try to extract from UPI transaction ID pattern
    m_id = UPI_ID_RE.search(text_norm)
    if m_id:
        txn_id = m_id.group(1)
        merchant_hint = m_id.group(2).upper()
        meta["transaction_id"] = txn_id
        meta["merchant_hint"] = merchant_hint
        
        # Try to match merchant hint
        for key in UPI_KEYS:
            if key in merchant_hint:
                category, subcat = UPI_MERCHANT_MAP[key]
                meta["matched_merchant_key"] = key
                return category, subcat, merchant_hint.title(), 0.85, meta
        
        # Check if merchant hint looks like a person
        if _looks_like_person(merchant_hint):
            return "Transfers", "ToPerson", merchant_hint.title(), 0.75, {
                **meta,
                "reason": "upi_person_from_id",
            }
        
        # Generic business
        return "Transfers", "ToBusiness", merchant_hint.title(), 0.65, {
            **meta,
            "reason": "upi_business_from_id",
        }
    
    # If we detected UPI but couldn't extract details, mark as pending
    return "PENDING", "UPI", None, 0.30, {
        **meta,
        "reason": "upi_detected_but_no_details",
    }