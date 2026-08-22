import os
import json
import time
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

API_URL = "https://nseindia.com"
HOME_URL = "https://nseindia.com"

def fetch_nifty_option_chain():
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        print(f"[1/3] Visiting homepage to capture cookies: {HOME_URL}")
        home_response = session.get(HOME_URL, timeout=15)
        print(f"-> Homepage response status: {home_response.status_code}")
        print(f"-> Captured cookies: {session.cookies.get_dict()}")
        
        print("-> Sleeping for 2 seconds to mimic natural user delay...")
        time.sleep(2)
        
        print(f"[2/3] Querying Option Chain API endpoint: {API_URL}")
        response = session.get(API_URL, timeout=15)
        print(f"-> API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Safety check to see if required top-level JSON keys exist
            if "records" in data:
                print("-> SUCCESS: JSON payload downloaded and validated.")
                return data
            else:
                print("-> WARNING: Response is valid JSON but missing the expected 'records' key!")
                print(f"-> Available top-level keys are: {list(data.keys())}")
                return None
        else:
            print(f"-> ERROR: Server rejected the script with status code {response.status_code}")
            return None
            
    except Exception as e:
        print(f"-> CRITICAL EXCEPTION during fetching: {e}")
        return None

def generate_markdown_table(data):
    if not data:
        print("[Skipping Table Generation] No valid payload data provided.")
        return "### ❌ Error: Could not fetch live data from NSE."

    try:
        underlying_value = data["records"]["underlyingValue"]
        timestamp = data["records"]["timestamp"]
        all_records = data["filtered"]["data"]
        
        print(f"--- PARSED MARKET DATA ---")
        print(f"Spot Price: {underlying_value}")
        print(f"NSE Timestamp: {timestamp}")
        print(f"Total Rows Extracted from filtered list: {len(all_records)}")
        print(f"--------------------------")

        markdown = f"### 📊 NIFTY 50 Live Option Chain Data\n"
        markdown += f"**Last Updated (NSE):** {timestamp} | **NIFTY Spot Price:** {underlying_value}\n\n"
        markdown += "| CE OI | CE Change OI | CE LTP | Strike Price | PE LTP | PE Change OI | PE OI |\n"
        markdown += "| :--- | :--- | :--- | :---: | :--- | :--- | :--- |\n"

        # Extract up to 10 rows safely
        display_rows = all_records[:10]
        for row in display_rows:
            strike = row["strikePrice"]
            ce = row.get("CE", {})
            pe = row.get("PE", {})

            markdown += (
                f"| {ce.get('openInterest', 0)} | {ce.get('changeinOpenInterest', 0)} | {ce.get('lastPrice', 0)} "
                f"| **{strike}** "
                f"| {pe.get('lastPrice', 0)} | {pe.get('changeinOpenInterest', 0)} | {pe.get('openInterest', 0)} |\n"
            )
        
        print("-> Markdown string generated successfully.")
        return markdown
    except KeyError as e:
        print(f"-> ERROR: Failed to parse structural data keys: {e}")
        return "### ❌ Error: Market data format mismatch."

def update_readme(new_content):
    readme_path = "README.md"
    start_tag = "<!-- NSE_DATA_START -->"
    end_tag = "<!-- NSE_DATA_END -->"

    print(f"[3/3] Commencing README.md modification updates...")
    
    if not os.path.exists(readme_path):
        print(f"-> README.md not found. Generating a clean template structure.")
        with open(readme_path, "w") as f:
            f.write(f"# NSE Option Chain Tracker\n\n{start_tag}\n{end_tag}")

    with open(readme_path, "r") as f:
        content = f.read()

    if start_tag not in content or end_tag not in content:
        print("-> ERROR: Target placeholder comment tags are completely missing inside README.md!")
        print(f"-> Please ensure your README contains exactly: {start_tag} and {end_tag}")
        return

    # Safer replacement logic using string find/indexing to avoid split array bugs
    try:
        start_idx = content.find(start_tag) + len(start_tag)
        end_idx = content.find(end_tag)
        
        updated_content = content[:start_idx] + f"\n\n{new_content}\n\n" + content[end_idx:]
        
        with open(readme_path, "w") as f:
            f.write(updated_content)
        print("-> SUCCESS: README.md content modified and written to disk.")
    except Exception as e:
        print(f"-> ERROR while attempting string replacement blocks: {e}")

if __name__ == "__main__":
    raw_data = fetch_nifty_option_chain()
    md_table = generate_markdown_table(raw_data)
    update_readme(md_table)
