# regex_engine/vendor_rules.py

"""
Fallback vendor detection patterns (used when vendor_map doesn't match).
These are more flexible regex patterns for catching variations.
"""

VENDOR_REGEX = {
    # ============================================
    # FOOD & DINING
    # ============================================
    "Hotel/Restaurant": [
        r"hotel\s+\w+", r"restaurant", r"dhaba", r"caterer",
        r"bhojanalay", r"eatery", r"food.*court"
    ],
    "Snacks/FastFood": [
        r"bhel", r"snacks", r"chai", r"tea\s+stall",
        r"fast\s+food", r"dosa", r"vada", r"pakodi"
    ],
    "FoodDelivery": [
        r"swiggy", r"zomato", r"dunzo", r"food.*delivery"
    ],
    
    # ============================================
    # GROCERIES
    # ============================================
    "Supermarket": [
        r"d[-\s]?mart", r"super\s*market", r"hyper\s*market",
        r"reliance\s+fresh", r"more\s+mega", r"star\s+bazaar"
    ],
    "OnlineGrocery": [
        r"bigbasket", r"bb[-\s]?daily", r"grofers", r"blinkit",
        r"zepto", r"instamart"
    ],
    "LocalGrocery": [
        r"kirana", r"provision", r"dairy", r"vegetables"
    ],
    
    # ============================================
    # SHOPPING
    # ============================================
    "OnlineShopping": [
        r"amazon", r"flipkart", r"myntra", r"ajio",
        r"tatacliq", r"meesho", r"snapdeal"
    ],
    "Fashion": [
        r"trends", r"lifestyle", r"westside", r"pantaloons",
        r"max\s+fashion", r"shoppers\s+stop", r"collection"
    ],
    "Electronics": [
        r"croma", r"reliance\s+digital", r"vijay\s+sales",
        r"retail\s+outlet"
    ],
    "Stationery": [
        r"stationer", r"xerox", r"print", r"paper"
    ],
    "Pharmacy": [
        r"medical", r"pharmacy", r"chemist", r"drug"
    ],
    
    # ============================================
    # FUEL & TRANSPORT
    # ============================================
    "FuelStation": [
        r"petrol", r"petroleum", r"service\s+station",
        r"hpcl", r"bpcl", r"iocl", r"indian\s+oil",
        r"bharat\s+petroleum", r"hindustan\s+petroleum",
        r"fuel", r"pump"
    ],
    "CabService": [
        r"uber", r"ola\s+cab", r"ola(?!\s+electric)", r"taxi",
        r"rapido", r"meru"
    ],
    "AutoService": [
        r"auto\s+centre", r"auto\s+service", r"garage",
        r"service\s+centre"
    ],
    
    # ============================================
    # UTILITIES
    # ============================================
    "MobileRecharge": [
        r"mobile\s+recharge", r"recharge", r"prepaid",
        r"airtel", r"jio(?!mart)", r"vodafone", r"vi[-\s]",
        r"bsnl"
    ],
    "DTH": [
        r"dth", r"dish\s+tv", r"tata\s+sky", r"sun\s+direct",
        r"d2h"
    ],
    "Electricity": [
        r"electricity", r"power\s+bill", r"bescom",
        r"msedcl", r"tneb", r"torrent"
    ],
    "Gas": [
        r"gas\s+bill", r"lpg", r"hp\s+gas", r"bharat\s+gas",
        r"indane"
    ],
    
    # ============================================
    # ENTERTAINMENT
    # ============================================
    "Streaming": [
        r"netflix", r"hotstar", r"prime\s+video", r"disney",
        r"sony\s*liv", r"zee5", r"voot"
    ],
    "Music": [
        r"spotify", r"youtube\s+music", r"gaana", r"wynk"
    ],
    
    # ============================================
    # PAYMENT METHODS
    # ============================================
    "DigitalWallet": [
        r"paytm", r"phonepe", r"googlepay", r"gpay",
        r"mobikwik", r"freecharge", r"amazonpay"
    ],
    "PaymentGateway": [
        r"razorpay", r"billdesk", r"cashfree", r"payu",
        r"ccavenue"
    ],
    
    # ============================================
    # BANKING PATTERNS
    # ============================================
    "BankTransfer": [
        r"neft[-/]", r"imps[-/]", r"rtgs[-/]", r"upi[-/]"
    ],
    "ATM": [
        r"atm\s+wdr", r"atm\s+dep", r"atmwdl", r"atmwdr",
        r"nfs/", r"cashnet/"
    ],
    
    # ============================================
    # GOVERNMENT & OFFICIAL
    # ============================================
    "Government": [
        r"ipay/eshp", r"cbdt", r"income\s+tax", r"rto",
        r"property\s+tax", r"municipal", r"nikshay"
    ],
    
    # ============================================
    # EDUCATION
    # ============================================
    "Education": [
        r"learning", r"academy", r"institute", r"coaching",
        r"tuition", r"training"
    ],
    
    # ============================================
    # HEALTHCARE
    # ============================================
    "Healthcare": [
        r"clinic", r"hospital", r"doctor", r"dr\s+\w+",
        r"dental", r"medical\s+centre"
    ],
    
    # ============================================
    # TRAVEL
    # ============================================
    "Travel": [
        r"makemytrip", r"cleartrip", r"yatra", r"goibibo",
        r"irctc", r"redbus"
    ],
    "Hotel": [
        r"oyo", r"treebo", r"hotel\s+booking"
    ],
    
    # ============================================
    # GAMING & LEISURE
    # ============================================
    "Gaming": [
        r"dream11", r"mpl", r"rummy", r"fantasy",
        r"gaming", r"playstore\s+game"
    ],
    
    # ============================================
    # INSURANCE
    # ============================================
    "Insurance": [
        r"insurance", r"lic\s", r"policy", r"premium",
        r"pmsby", r"pmjjby"
    ],
    
    # ============================================
    # INVESTMENTS
    # ============================================
    "Investment": [
        r"zerodha", r"upstox", r"groww", r"angel\s+one",
        r"mutual\s+fund", r"sip\s+"
    ],
    
    # ============================================
    # MISCELLANEOUS
    # ============================================
    "PanShop": [
        r"pan\s+shop", r"paan", r"tobacco"
    ],
    "GeneralStore": [
        r"general\s+store", r"enterprise", r"corporation",
        r"traders", r"stores"
    ],
}