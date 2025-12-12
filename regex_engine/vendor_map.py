# regex_engine/vendor_map.py

VENDOR_CATEGORY_MAP = {
    # ============================================
    # FOOD & DINING
    # ============================================
    # Food Delivery
    "ZOMATO": ("Dining", "FoodDelivery"),
    "SWIGGY": ("Dining", "FoodDelivery"),
    "DUNZO": ("Dining", "FoodDelivery"),
    "EATFIT": ("Dining", "FoodDelivery"),
    "BOX8": ("Dining", "FoodDelivery"),
    "FAASOS": ("Dining", "FoodDelivery"),
    
    # Restaurants
    "HOTEL RAJ": ("Dining", "Restaurant"),
    "HOTEL RAYAT": ("Dining", "Restaurant"),
    "MSW(HOTEL RAJ": ("Dining", "Restaurant"),
    "GIRIJA CATERERS": ("Dining", "Restaurant"),
    "SAGAR RESTAURANT": ("Dining", "Restaurant"),
    "SONA GARDEN RESTAURANT": ("Dining", "Restaurant"),
    "DHARESHWAR RESTAURANT": ("Dining", "Restaurant"),
    "HOTEL JAGDAMB": ("Dining", "Restaurant"),
    "MAULI DHABA": ("Dining", "Restaurant"),
    "SHETKARI BHOJANALAY": ("Dining", "Restaurant"),
    "HOTEL SAMMAN": ("Dining", "Restaurant"),
    "GIRIDHAR VEG RESTURANT": ("Dining", "Restaurant"),
    "KFC": ("Dining", "Restaurant"),
    "MCDONALD": ("Dining", "Restaurant"),
    "DOMINOS": ("Dining", "Restaurant"),
    "PIZZA HUT": ("Dining", "Restaurant"),
    "PIZZAHUT": ("Dining", "Restaurant"),
    
    # Cafes
    "CCD": ("Dining", "Cafe"),
    "CAFECOFFEEDAY": ("Dining", "Cafe"),
    "CAFE COFFEE DAY": ("Dining", "Cafe"),
    "PUNERI CHAI": ("Dining", "Cafe"),
    "HARSH TEA": ("Dining", "Cafe"),
    
    # Snacks & Quick Bites
    "SHREE SAINATH BHEL": ("Dining", "SnacksAndBeverages"),
    "MEENA SNACKS CENTRE": ("Dining", "SnacksAndBeverages"),
    "DEEPAK SNACKS": ("Dining", "SnacksAndBeverages"),
    "DEEPAK SNACKS CENTER": ("Dining", "SnacksAndBeverages"),
    "SHREE RAMKRUSHNA FOODS": ("Dining", "SnacksAndBeverages"),
    "ANUSHKA BHEL PAKODI CENTER": ("Dining", "SnacksAndBeverages"),
    "SONAI DAVANGIRI DOSA": ("Dining", "SnacksAndBeverages"),
    "BALAJI FAST FOOD": ("Dining", "SnacksAndBeverages"),
    "SHREE UPHAR GRUH": ("Dining", "SnacksAndBeverages"),
    "JAGDAMBA SNACKS": ("Dining", "SnacksAndBeverages"),
    "SAI FOODS": ("Dining", "SnacksAndBeverages"),
    
    # Pan/Tobacco Shops
    "RAJ PAN SHOP": ("Miscellaneous", "PanShop"),
    "MUTAI PAN SHOP": ("Miscellaneous", "PanShop"),
    
    # ============================================
    # GROCERIES & DAILY NEEDS
    # ============================================
    # Supermarkets
    "DMART": ("Groceries", "Supermarket"),
    "D MART NANDED CITY": ("Groceries", "Supermarket"),
    "JIOMART": ("Groceries", "Supermarket"),
    "JIO MART": ("Groceries", "Supermarket"),
    "NATURESBASKET": ("Groceries", "Supermarket"),
    "SPENCERS": ("Groceries", "Supermarket"),
    "MOREMEGASTORE": ("Groceries", "Supermarket"),
    "STARQUICK": ("Groceries", "Supermarket"),
    "RELIANCE FRESH": ("Groceries", "Supermarket"),
    
    # Online Groceries
    "BIGBASKET": ("Groceries", "OnlineGroceries"),
    "BBDAILY": ("Groceries", "OnlineGroceries"),
    "BB-": ("Groceries", "OnlineGroceries"),
    "ZEPT": ("Groceries", "OnlineGroceries"),
    "ZEPTO": ("Groceries", "OnlineGroceries"),
    "BLINKIT": ("Groceries", "OnlineGroceries"),
    "GROFERS": ("Groceries", "OnlineGroceries"),
    "SWIGGY INSTAMART": ("Groceries", "OnlineGroceries"),
    "DUNZO DAILY": ("Groceries", "OnlineGroceries"),
    
    # Local Groceries
    "GURUKRUPA SUPER MARKET": ("Groceries", "LocalShops"),
    "SHRI AAIJI SUPER MARKET": ("Groceries", "LocalShops"),
    "KATRAJ DAIRY": ("Groceries", "LocalShops"),
    "VISHAL VEGETABLES": ("Groceries", "LocalShops"),
    "TRUPTI": ("Groceries", "LocalShops"),
    "COSMOS": ("Groceries", "LocalShops"),
    
    # ============================================
    # SHOPPING
    # ============================================
    # Online Shopping
    "AMAZON": ("Shopping", "Online"),
    "AMAZON.IN": ("Shopping", "Online"),
    "FLIPKART": ("Shopping", "Online"),
    "MYNTRA": ("Shopping", "Fashion"),
    "AJIO": ("Shopping", "Fashion"),
    "TATACLIQ": ("Shopping", "Online"),
    "TATANEU": ("Shopping", "Online"),
    "NYKAA": ("Shopping", "Beauty"),
    "MEESHO": ("Shopping", "Online"),
    "SNAPDEAL": ("Shopping", "Online"),
    
    # Fashion & Apparel
    "SHOPPERSSTOP": ("Shopping", "Fashion"),
    "SHOPPERS STOP": ("Shopping", "Fashion"),
    "LIFESTYLE": ("Shopping", "Fashion"),
    "MAXFASHION": ("Shopping", "Fashion"),
    "MAX FASHION": ("Shopping", "Fashion"),
    "RELIANCE TRENDS": ("Shopping", "Fashion"),
    "PANTALOONS": ("Shopping", "Fashion"),
    "WESTSIDE": ("Shopping", "Fashion"),
    "NEW MAYUR COLLECTION": ("Shopping", "Fashion"),
    "SUYASH DRESSES": ("Shopping", "Fashion"),
    
    # Electronics
    "CROMA": ("Shopping", "Electronics"),
    "VIJAYSALES": ("Shopping", "Electronics"),
    "RELIANCE DIGITAL": ("Shopping", "Electronics"),
    "REL DIGITAL": ("Shopping", "Electronics"),
    "CLASSIC RETAIL OUTLET": ("Shopping", "Electronics"),
    
    # Stationery
    "BOMBAY STATIONERS": ("Shopping", "Stationery"),
    "JEEVANDEEP STATIONERY": ("Shopping", "Stationery"),
    "IPRINT ENTERPRISES": ("Shopping", "Stationery"),
    "VIDHATA XEROX AND GENERAL STORE": ("Shopping", "Stationery"),
    
    # Medical/Pharmacy
    "SHRUTI MEDICAL": ("Shopping", "Pharmacy"),
    "SHRUTI MEDICAL AND GEN": ("Shopping", "Pharmacy"),
    "DHARESHWAR MEDICAL": ("Shopping", "Pharmacy"),
    "SHRIKRISHNA MEDICAL AND GENERAL": ("Shopping", "Pharmacy"),
    "APOLLO PHARMACY": ("Shopping", "Pharmacy"),
    "NETMEDS": ("Shopping", "Pharmacy"),
    "1MG": ("Shopping", "Pharmacy"),
    
    # Party/Decorations
    "RIBBONS AND BALLOONS": ("Shopping", "Decorations"),
    "RIBBONS AND BALLOONS DSK": ("Shopping", "Decorations"),
    
    # General Stores
    "SHITAL VAIBHAV BHANDAR": ("Shopping", "GeneralStore"),
    "R S ENTERPRISE": ("Shopping", "GeneralStore"),
    "SHREE ENTERPRISES": ("Shopping", "GeneralStore"),
    "RK": ("Shopping", "GeneralStore"),
    
    # ============================================
    # FUEL & TRANSPORT
    # ============================================
    # Fuel Stations
    "HPCL": ("Transport", "Fuel"),
    "BPCL": ("Transport", "Fuel"),
    "IOCL": ("Transport", "Fuel"),
    "INDIANOIL": ("Transport", "Fuel"),
    "INDIAN OIL": ("Transport", "Fuel"),
    "BHARATPET": ("Transport", "Fuel"),
    "BHARAT PETROLEUM": ("Transport", "Fuel"),
    "HINDPETRO": ("Transport", "Fuel"),
    "HINDUSTAN PETROLEUM": ("Transport", "Fuel"),
    "3S SERVICE STATION": ("Transport", "Fuel"),
    "THREE S SERVICE": ("Transport", "Fuel"),
    "BABAR PETROL PUMP": ("Transport", "Fuel"),
    "BAFNA BROTHERS": ("Transport", "Fuel"),
    "MITALI SERVICE": ("Transport", "Fuel"),
    "ADHOC KANKARIYA SERVIC": ("Transport", "Fuel"),
    "ADHOC KANKARIYA SERVICE": ("Transport", "Fuel"),
    "SHAHID LT COL PRAKASH": ("Transport", "Fuel"),
    "BABJI PETROLEUM": ("Transport", "Fuel"),
    "DNYANESHWARI PETROLINK": ("Transport", "Fuel"),
    "KOTHRUD PETROL CIRCLE": ("Transport", "Fuel"),
    "KOTHRUD PETROL": ("Transport", "Fuel"),
    "HIGHWAY PETROLEUM CENT": ("Transport", "Fuel"),
    "SHOLAPUR MOTOR STORES": ("Transport", "Fuel"),
    "SHOLAPUR": ("Transport", "Fuel"),
    "SAMARTH SERVICE STAT": ("Transport", "Fuel"),
    "INDUSTRIAL SERVICE STA": ("Transport", "Fuel"),
    "SHRI SWAMI SAMARTH EN": ("Transport", "Fuel"),
    "BPCL SHREE SWAMI SHANK": ("Transport", "Fuel"),
    "BPCL MITALI SERVICE S": ("Transport", "Fuel"),
    "IOCL BAFNA BROTHERS": ("Transport", "Fuel"),
    
    # Cab Services
    "UBER": ("Transport", "Cab"),
    "OLA": ("Transport", "Cab"),
    "OLA CABS": ("Transport", "Cab"),
    "RAPIDO": ("Transport", "BikeTaxi"),
    "MERU": ("Transport", "Cab"),
    
    # Public Transport
    "REDBUS": ("Transport", "PublicTransport"),
    "IRCTC": ("Transport", "PublicTransport"),
    
    # Auto/Vehicle Services
    "FAMOUS AUTO CENTRE": ("Transport", "AutoService"),
    "EXCEL SERVICE CENTRE": ("Transport", "AutoService"),
    
    # ============================================
    # UTILITIES & BILLS
    # ============================================
    # Mobile/DTH/Telecom
    "AIRTEL": ("Utilities", "MobileRecharge"),
    "JIO": ("Utilities", "MobileRecharge"),
    "VODAFONE": ("Utilities", "MobileRecharge"),
    "VI-": ("Utilities", "MobileRecharge"),
    "VI ": ("Utilities", "MobileRecharge"),
    "BSNL": ("Utilities", "MobileRecharge"),
    "SUN DIRECT": ("Utilities", "DTH"),
    "TATASKY": ("Utilities", "DTH"),
    "TATA SKY": ("Utilities", "DTH"),
    "D2H": ("Utilities", "DTH"),
    "DISHTV": ("Utilities", "DTH"),
    "DISH TV": ("Utilities", "DTH"),
    "DTHRCG": ("Utilities", "DTH"),
    
    # Gas
    "HPGAS": ("Utilities", "Gas"),
    "HP GAS": ("Utilities", "Gas"),
    "BHARAT GAS": ("Utilities", "Gas"),
    "INDANE": ("Utilities", "Gas"),
    
    # Electricity
    "BESCOM": ("Utilities", "Electricity"),
    "BSES": ("Utilities", "Electricity"),
    "TNEB": ("Utilities", "Electricity"),
    "MSEDCL": ("Utilities", "Electricity"),
    "TORRENTPOWER": ("Utilities", "Electricity"),
    "TORRENT POWER": ("Utilities", "Electricity"),
    
    # BBPS (Bharat Bill Payment System)
    "BBPS": ("Utilities", "BillPayment"),
    
    # ============================================
    # ENTERTAINMENT & STREAMING
    # ============================================
    "NETFLIX": ("Entertainment", "Streaming"),
    "SPOTIFY": ("Entertainment", "Music"),
    "HOTSTAR": ("Entertainment", "Streaming"),
    "DISNEY": ("Entertainment", "Streaming"),
    "SONYLIV": ("Entertainment", "Streaming"),
    "SONY LIV": ("Entertainment", "Streaming"),
    "ZEE5": ("Entertainment", "Streaming"),
    "PRIME VIDEO": ("Entertainment", "Streaming"),
    "AMAZON PRIME": ("Entertainment", "Streaming"),
    "VOOT": ("Entertainment", "Streaming"),
    "ALT BALAJI": ("Entertainment", "Streaming"),
    
    # ============================================
    # PAYMENT WALLETS & GATEWAYS
    # ============================================
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
    "BHARATPE MERCHANT": ("Transfers", "ToBusiness"),
    
    # ============================================
    # TRAVEL & BOOKING
    # ============================================
    "MAKEMYTRIP": ("Travel", "FlightTickets"),
    "EASEMYTRIP": ("Travel", "FlightTickets"),
    "YATRA": ("Travel", "FlightTickets"),
    "CLEARTRIP": ("Travel", "FlightTickets"),
    "GOIBIBO": ("Travel", "Accommodation"),
    "OYO": ("Travel", "Accommodation"),
    "TREEBO": ("Travel", "Accommodation"),
    
    # ============================================
    # GAMING & FANTASY
    # ============================================
    "DREAM11": ("Leisure", "Gaming"),
    "DREAM11ONLINE": ("Leisure", "Gaming"),
    "DREAM11ON LINE": ("Leisure", "Gaming"),
    "MPL": ("Leisure", "Gaming"),
    "RUMMYCIRCLE": ("Leisure", "Gaming"),
    
    # ============================================
    # EDUCATION & SERVICES
    # ============================================
    "SIMACES LEARNING LLP": ("Education", "Courses"),
    "SIMACES LEARNING": ("Education", "Courses"),
    "RESILIENT INNOVATIONS": ("Education", "TechServices"),
    
    # ============================================
    # HEALTHCARE
    # ============================================
    "DR RAWLE DENTEL CLINIC": ("Healthcare", "Consultation"),
    "DR RAWLE DENTAL CLINIC": ("Healthcare", "Consultation"),
    
    # ============================================
    # INCOME
    # ============================================
    "SALARY CREDIT": ("Income", "Salary"),
    "SALARYCREDIT": ("Income", "Salary"),
    "INT.PD": ("Income", "Interest"),
    "INT PD": ("Income", "Interest"),
    "INTEREST": ("Income", "Interest"),
    "NIKSHAY TB PATI": ("Income", "Government"),
    "ACHPFM-NIKSHAY TB PATI": ("Income", "Government"),
    
    # ============================================
    # LOANS & EMI
    # ============================================
    "EMI PAYMENT": ("Debt", "LoanEMI"),
    "HDFC-LOAN": ("Debt", "LoanEMI"),
    "HDFC L-": ("Debt", "LoanEMI"),
    
    # ============================================
    # ATM & CASH
    # ============================================
    "ATM WDR": ("Cash", "ATMWithdrawal"),
    "ATMWDR": ("Cash", "ATMWithdrawal"),
    "ATMWDL": ("Cash", "ATMWithdrawal"),
    "ATM DEP": ("Cash", "ATMDeposit"),
    "ATMDEPOSIT": ("Cash", "ATMDeposit"),
    
    # ============================================
    # BANK CHARGES
    # ============================================
    "QUARTERLY AVG BAL CHARGE": ("BankCharges", "BalanceCharge"),
    "QTRLY AVG BAL CHARGE": ("BankCharges", "BalanceCharge"),
    "SMS CHRG": ("BankCharges", "SMS"),
    "SMS CHARGES": ("BankCharges", "SMS"),
    "SMS_CHARGE": ("BankCharges", "SMS"),
    "CA KEEPING CHGS": ("BankCharges", "Other"),
    "ANNUAL_CARDFEE": ("BankCharges", "CardFee"),
    "ANNUAL CARD FEE": ("BankCharges", "CardFee"),
    "LATE FINE FEES": ("BankCharges", "LateFee"),
    "VLP CHARGES": ("BankCharges", "Other"),
    
    # ============================================
    # INSURANCE
    # ============================================
    "PMSBY": ("Insurance", "GovtScheme"),
    "PMJJBY": ("Insurance", "GovtScheme"),
    "LIC": ("Insurance", "Life"),
    "HDFCLIFE": ("Insurance", "Life"),
    "SBILIFE": ("Insurance", "Life"),
    "ICICIPRULIFE": ("Insurance", "Life"),
    
    # ============================================
    # INVESTMENTS
    # ============================================
    "ZERODHA": ("Investment", "Stocks"),
    "UPSTOX": ("Investment", "Stocks"),
    "GROWW": ("Investment", "Stocks"),
    "ANGEL ONE": ("Investment", "Stocks"),
}