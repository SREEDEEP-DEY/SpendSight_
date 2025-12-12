# regex_engine/category_rules.py

CATEGORY_REGEX = {
    # FUEL & TRANSPORT
    "Transport.Fuel": [
        r"petrol", r"diesel", r"fuel", r"petroleum",
        r"hpcl", r"bpcl", r"iocl", r"indian oil", r"indianoil",
        r"bharat petroleum", r"hindustan petroleum",
        r"service station", r"petrol pump", r"gas station",
        r"cashless.*fuel", r"fuel.*cashback",
        r"babar petrol", r"shree swami samarth", r"bafna brothers",
        r"mitali service", r"adhoc kankariya", r"shahid.*prakash",
        r"3s service", r"babji petroleum", r"dnyaneshwari petrolink",
        r"kothrud petrol", r"highway petroleum", r"sholapur motor",
        r"samarth service stat"
    ],
    
    # DINING & FOOD
    "Dining.Restaurant": [
        r"restaurant", r"hotel raj", r"hotel rayat", r"msw.*hotel",
        r"girija caterers", r"sagar restaurant", r"sona garden",
        r"dhareshwar restaurant", r"hotel jagdamb", r"mauli dhaba",
        r"shetkari bhojanalay", r"hotel samman", r"giridhar veg"
    ],
    "Dining.FoodDelivery": [
        r"swiggy", r"zomato", r"dunzo", r"eatfit", r"box8", r"faasos"
    ],
    "Dining.SnacksAndBeverages": [
        r"chai", r"tea", r"bhel", r"snacks", r"fast food",
        r"puneri chai", r"shree sainath bhel", r"meena snacks",
        r"deepak snacks", r"shree ramkrushna foods", r"anushka bhel",
        r"davangiri dosa", r"balaji fast food", r"shree uphar gruh"
    ],
    "Dining.Cafe": [
        r"cafe", r"coffee", r"ccd", r"cafecoffeeday", r"starbucks"
    ],
    
    # GROCERIES & DAILY NEEDS
    "Groceries.Supermarket": [
        r"dmart", r"d-mart", r"d mart", r"more megastore", r"reliance fresh",
        r"jiomart", r"jio mart", r"spencers", r"star bazaar",
        r"gurukrupa super market", r"super market", r"katraj dairy",
        r"shri aaiji super market", r"vishal vegetables"
    ],
    "Groceries.OnlineGroceries": [
        r"bigbasket", r"bb daily", r"bb-", r"grofers", r"blinkit",
        r"zepto", r"zept", r"dunzo daily", r"swiggy instamart"
    ],
    "Groceries.LocalShops": [
        r"kirana", r"provision", r"general store",
        r"vidhata xerox and general"
    ],
    
    # SHOPPING
    "Shopping.Online": [
        r"amazon", r"flipkart", r"snapdeal", r"paytm mall",
        r"tatacliq", r"tataneu", r"meesho", r"shopsy"
    ],
    "Shopping.Fashion": [
        r"myntra", r"ajio", r"lifestyle", r"westside",
        r"pantaloons", r"max fashion", r"shoppers stop",
        r"reliance trends", r"new mayur collection"
    ],
    "Shopping.Electronics": [
        r"croma", r"reliance digital", r"rel digital", r"vijay sales",
        r"electronics", r"classic retail outlet"
    ],
    "Shopping.Beauty": [
        r"nykaa", r"purplle", r"sugar cosmetics"
    ],
    "Shopping.Stationery": [
        r"stationery", r"stationers", r"xerox",
        r"bombay stationers", r"iprint enterprises", r"jeevandeep stationery"
    ],
    "Shopping.Pharmacy": [
        r"medical", r"pharmacy", r"chemist", r"medicine",
        r"apollo pharmacy", r"netmeds", r"1mg",
        r"shruti medical", r"dhareshwar medical", r"shrikrishna medical"
    ],
    "Shopping.Decorations": [
        r"balloons", r"ribbons", r"party",
        r"ribbons and balloons"
    ],
    
    # TRANSPORT
    "Transport.Cab": [
        r"uber", r"ola cabs", r"ola", r"rapido", r"meru", r"taxi"
    ],
    "Transport.PublicTransport": [
        r"metro", r"bus", r"railway", r"irctc", r"train ticket",
        r"redbus", r"abhibus"
    ],
    "Transport.BikeTaxi": [
        r"rapido", r"bike taxi"
    ],
    
    # UTILITIES & BILLS
    "Utilities.Electricity": [
        r"electricity", r"power bill", r"bescom", r"msedcl",
        r"torrent power", r"tneb", r"bses"
    ],
    "Utilities.Gas": [
        r"gas bill", r"lpg", r"bharat gas", r"hp gas", r"indane",
        r"hpgas"
    ],
    "Utilities.Water": [
        r"water bill", r"water charges"
    ],
    "Utilities.MobileRecharge": [
        r"mobile recharge", r"prepaid", r"recharge",
        r"airtel", r"jio", r"vodafone", r"vi-", r"bsnl"
    ],
    "Utilities.DTH": [
        r"dth", r"dish tv", r"tata sky", r"sun direct", r"d2h",
        r"dthrcg"
    ],
    "Utilities.Internet": [
        r"broadband", r"wifi", r"internet", r"fiber"
    ],
    
    # ENTERTAINMENT
    "Entertainment.Streaming": [
        r"netflix", r"hotstar", r"prime video", r"disney",
        r"sony liv", r"zee5", r"voot", r"alt balaji"
    ],
    "Entertainment.Music": [
        r"spotify", r"youtube music", r"gaana", r"wynk"
    ],
    
    # HEALTH & FITNESS
    "Healthcare.Consultation": [
        r"doctor", r"clinic", r"hospital", r"medical consultation",
        r"dental", r"dentel",
        r"dr rawle dentel clinic"
    ],
    "Healthcare.Medicine": [
        r"pharmacy", r"medical and general"
    ],
    
    # EDUCATION & LEARNING
    "Education.Courses": [
        r"course", r"training", r"tuition", r"coaching",
        r"simaces learning"
    ],
    
    # PERSONAL CARE
    "PersonalCare.Salon": [
        r"salon", r"barber", r"haircut", r"spa"
    ],
    
    # LEISURE & GAMING
    "Leisure.Gaming": [
        r"dream11", r"mpl", r"rummy", r"fantasy", r"gaming",
        r"dream11online", r"dream11on line"
    ],
    
    # INCOME
    "Income.Salary": [
        r"salary", r"payroll", r"salary credit", r"salarycredit",
        r"credited by employer"
    ],
    "Income.Interest": [
        r"int\.pd", r"int pd", r"interest", r"interest credit"
    ],
    "Income.Refund": [
        r"refund", r"cashback", r"credit.*cashback",
        r"ref\\", r"cashless.*%"
    ],
    "Income.Government": [
        r"nikshay", r"tb pati", r"achpfm"
    ],
    
    # TRANSFERS
    "Transfers.ToPerson": [
        r"neft.*(?:to|credit)", r"imps.*(?:to|credit)",
        r"upi.*(?:person|individual)"
    ],
    "Transfers.ToBusiness": [
        r"phonepe", r"paytm", r"googlepay", r"gpay",
        r"razorpay", r"billdesk", r"cashfree"
    ],
    
    # CASH
    "Cash.ATMWithdrawal": [
        r"atm wdr", r"atmwdr", r"atm withdrawal",
        r"atmwdl", r"nfs/", r"cashnet/"
    ],
    "Cash.ATMDeposit": [
        r"atm dep", r"atm deposit"
    ],
    
    # BANK CHARGES
    "BankCharges.SMS": [
        r"sms.*charge", r"sms chrg", r"smschrg"
    ],
    "BankCharges.BalanceCharge": [
        r"quarterly.*avg.*bal", r"qtrly.*avg.*bal",
        r"minimum balance", r"avg bal charge"
    ],
    "BankCharges.CardFee": [
        r"annual.*card.*fee", r"card.*maintenance",
        r"debit card", r"credit card.*fee",
        r"annual_cardfee"
    ],
    "BankCharges.ATMFee": [
        r"atm.*fee", r"atm.*charge"
    ],
    "BankCharges.Other": [
        r"ca keeping chgs", r"service charge", r"processing fee",
        r"late fine", r"vlp charges"
    ],
    
    # DEBT & LOANS
    "Debt.LoanEMI": [
        r"emi", r"loan", r"hdfc.*loan", r"hdfc l-",
        r"home loan", r"personal loan", r"car loan"
    ],
    
    # INSURANCE
    "Insurance.GovtScheme": [
        r"pmsby", r"pmjjby", r"atal pension"
    ],
    "Insurance.Life": [
        r"lic", r"life insurance", r"term insurance"
    ],
    "Insurance.Health": [
        r"health insurance", r"mediclaim"
    ],
    
    # GOVERNMENT PAYMENTS
    "Government.Tax": [
        r"income tax", r"tds", r"advance tax",
        r"ipay/eshp.*cbdt", r"cbdt"
    ],
    "Government.RTO": [
        r"rto", r"vehicle tax", r"road tax",
        r"ipay/eshp.*mh\d+"
    ],
    "Government.PropertyTax": [
        r"property tax", r"house tax", r"municipal"
    ],
    
    # INVESTMENTS
    "Investment.MutualFunds": [
        r"mutual fund", r"sip", r"systematic investment"
    ],
    "Investment.Stocks": [
        r"zerodha", r"upstox", r"groww", r"angel one"
    ],
    
    # TRAVEL
    "Travel.Accommodation": [
        r"hotel booking", r"oyo", r"treebo", r"goibibo"
    ],
    "Travel.FlightTickets": [
        r"flight", r"airline", r"indigo", r"spicejet",
        r"makemytrip", r"cleartrip", r"easemytrip", r"yatra"
    ],
    
    # MISCELLANEOUS
    "Miscellaneous.PanShop": [
        r"pan shop", r"tobacco"
    ],
    "Miscellaneous.Enterprises": [
        r"enterprise", r"corporation", r"services",
        r"sago corporation", r"excel service centre",
        r"shree enterprises", r"vagad enterprises"
    ],
    "Miscellaneous.Dresses": [
        r"dresses", r"garments", r"suyash dresses"
    ]
}