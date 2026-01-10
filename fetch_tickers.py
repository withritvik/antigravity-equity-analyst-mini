import csv
import urllib.request
import io
import ssl

# Bypass SSL verification for legacy reasons if needed
ssl._create_default_https_context = ssl._create_unverified_context

NIFTY_URL = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"
SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

def fetch_data(url):
    print(f"Fetching data from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_and_update():
    # --- NIFTY 500 ---
    nifty_content = fetch_data(NIFTY_URL)
    nifty_500 = []
    if nifty_content:
        csv_reader = csv.DictReader(io.StringIO(nifty_content))
        for row in csv_reader:
            symbol = row.get('Symbol', '').strip()
            # Try 'Company Name' or 'Company'
            company = row.get('Company Name', row.get('Company', '')).strip()
            if symbol:
                nifty_500.append(f'    ("{symbol}.NS", "{company}")')

    # --- S&P 500 ---
    sp_content = fetch_data(SP500_URL)
    sp_500 = []
    if sp_content:
        csv_reader = csv.DictReader(io.StringIO(sp_content))
        for row in csv_reader:
            # Columns: Symbol, Security, ...
            symbol = row.get('Symbol', '').strip()
            company = row.get('Security', row.get('Name', '')).strip()
            if symbol:
                sp_500.append(f'    ("{symbol}", "{company}")')

    # Join strings to variables to avoid f-string backslash issues
    nifty_str = ',\n'.join(nifty_500)
    sp500_str = ',\n'.join(sp_500)

    file_content = f"""# Stock Tickers Data (Generated)
# NIFTY 500 (India)
NIFTY_50 = [
{nifty_str}
]

# S&P 500 (USA)
SP_500 = [
{sp500_str}
]
"""
    
    with open('data/tickers.py', 'w', encoding='utf-8') as f:
        f.write(file_content)
    
    print(f"Updated data/tickers.py with {len(nifty_500)} NIFTY and {len(sp_500)} S&P stocks.")

if __name__ == "__main__":
    fetch_and_update()
