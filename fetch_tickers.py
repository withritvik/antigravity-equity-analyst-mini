import csv
import urllib.request
import io

URL = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"

def fetch_and_update():
    print(f"Fetching NIFTY 500 list from {URL}...")
    try:
        with urllib.request.urlopen(URL) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    csv_reader = csv.DictReader(io.StringIO(content))
    
    nifty_500 = []
    for row in csv_reader:
        # Columns based on standard NSE CSV: 'Symbol', 'Company Name'
        symbol = row.get('Symbol', '').strip()
        company = row.get('Company Name', '').strip()
        
        if symbol and company:
            nifty_500.append(f'    ("{symbol}.NS", "{company}")')

    # Existing S&P 500 List (Preserving it)
    sp_500_list = """
# Top ~100 S&P 500 Tickers
SP_500 = [
    ("AAPL", "Apple Inc."), ("MSFT", "Microsoft Corp"), 
    ("GOOGL", "Alphabet A"), ("GOOG", "Alphabet C"), 
    ("AMZN", "Amazon.com"), ("NVDA", "NVIDIA Corp"), 
    ("META", "Meta Platforms"), ("TSLA", "Tesla Inc."), 
    ("BRK-B", "Berkshire Hathaway"), ("UNH", "UnitedHealth Group"), 
    ("JNJ", "Johnson & Johnson"), ("XOM", "Exxon Mobil"), 
    ("JPM", "JPMorgan Chase"), ("PG", "Procter & Gamble"), 
    ("V", "Visa Inc."), ("LLY", "Eli Lilly"), 
    ("MA", "Mastercard"), ("HD", "Home Depot"), 
    ("CVX", "Chevron Corp"), ("MRK", "Merck & Co."),
    ("ABBV", "AbbVie Inc."), ("PEP", "PepsiCo"), 
    ("KO", "Coca-Cola"), ("AVGO", "Broadcom Inc."), 
    ("COST", "Costco Wholesale"), ("TMO", "Thermo Fisher"), 
    ("MCD", "McDonald's"), ("CSCO", "Cisco Systems"), 
    ("ACN", "Accenture"), ("ABT", "Abbott Labs"),
    ("CRM", "Salesforce"), ("DIS", "Walt Disney"), 
    ("LIN", "Linde plc"), ("VZ", "Verizon Comm"), 
    ("DHR", "Danaher Corp"), ("WMT", "Walmart Inc."), 
    ("NKE", "Nike Inc."), ("NEE", "NextEra Energy"), 
    ("TXN", "Texas Instruments"), ("PM", "Philip Morris"),
    ("BMY", "Bristol-Myers Squibb"), ("ADBE", "Adobe Inc."), 
    ("CMCSA", "Comcast Corp"), ("NFLX", "Netflix Inc."), 
    ("PFE", "Pfizer Inc."), ("UPS", "UPS"), 
    ("AMD", "AMD"), ("QCOM", "Qualcomm"), 
    ("UNP", "Union Pacific"), ("INTC", "Intel Corp"),
    ("LOW", "Lowe's Cos."), ("HON", "Honeywell Int"), 
    ("BA", "Boeing Co."), ("IBM", "IBM"), 
    ("SPGI", "S&P Global"), ("RTX", "Raytheon Tech"), 
    ("INTU", "Intuit Inc."), ("CAT", "Caterpillar"), 
    ("GS", "Goldman Sachs"), ("AMGN", "Amgen Inc."),
    ("GE", "General Electric"), ("DE", "Deere & Co."), 
    ("MS", "Morgan Stanley"), ("PLD", "Prologis"), 
    ("MDT", "Medtronic"), ("SBUX", "Starbucks"), 
    ("ISRG", "Intuitive Surgical"), ("ELV", "Elevance Health"), 
    ("BLK", "BlackRock"), ("GILD", "Gilead Sciences"),
    ("BKNG", "Booking Holdings"), ("ADI", "Analog Devices"), 
    ("MDLZ", "Mondelez Int"), ("TJX", "TJX Companies"), 
    ("ADP", "ADP"), ("MMC", "Marsh & McLennan"), 
    ("CVS", "CVS Health"), ("AMT", "American Tower"), 
    ("LMT", "Lockheed Martin"), ("VRTX", "Vertex Pharm"),
    ("CI", "Cigna Group"), ("AXP", "American Express"), 
    ("BSX", "Boston Scientific"), ("C", "Citigroup"), 
    ("SYK", "Stryker Corp"), ("UBER", "Uber Tech"), 
    ("T", "AT&T Inc."), ("FI", "Fiserv Inc."), 
    ("CB", "Chubb Ltd"), ("MO", "Altria Group"),
    ("PGR", "Progressive Corp"), ("ZTS", "Zoetis Inc."), 
    ("REGN", "Regeneron Pharm"), ("LRCX", "Lam Research"), 
    ("SO", "Southern Company"), ("SLB", "Schlumberger"), 
    ("BDX", "Becton Dickinson"), ("NOW", "ServiceNow"), 
    ("EQIX", "Equinix Inc."), ("EOG", "EOG Resources")
]
"""

    nifty_str = ',\n'.join(nifty_500)

    file_content = f"""# NIFTY 500 Tickers (Generated)
NIFTY_50 = [
{nifty_str}
]

{sp_500_list}
"""
    
    with open('data/tickers.py', 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    print(f"Successfully wrote {len(nifty_500)} tickers to data/tickers.py")

if __name__ == "__main__":
    fetch_and_update()
