import os
import json
import time
from playwright.sync_api import sync_playwright

def fetch_nifty_option_chain_via_browser():
    print("[1/3] Launching Headless Browser via Playwright...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()
        
        # Dictionary container to hold the single active data payload
        payload_container = {"json_data": None}

        # Intercept background network responses
        def handle_response(response):
            if "api/option-chain-indices?symbol=NIFTY" in response.url:
                print(f"-> Target network request intercepted! HTTP Status: {response.status_code}")
                if response.status_code == 200:
                    try:
                        payload_container["json_data"] = response.json()
                        print("-> Successfully loaded JSON payload into context.")
                    except Exception as e:
                        print(f"-> Failed to parse network stream as JSON: {e}")

        page.on("response", handle_response)

        try:
            target_url = "https://nseindia.com"
            print(f"-> Navigating browser to web page: {target_url}")
            
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            print("-> Waiting for background API streams to complete...")
            time.sleep(6)  # Generous window for cloud latency
            
            return payload_container["json_data"]
                
        except Exception as e:
            print(f"-> CRITICAL EXCEPTION during browser session: {e}")
            return None
        finally:
            context.close()
            browser.close()

def generate_markdown_table(data):
    if not data or "records" not in data:
        print("[Skipping Table Generation] No valid payload dictionary provided.")
        return "### ❌ Error: Could not fetch live data from NSE due to Akamai structural blocks."

    try:
        underlying_value = data["records"]["underlyingValue"]
        timestamp = data["records"]["timestamp"]
        all_records = data["filtered"]["data"]
        
        print(f"--- PARSED MARKET DATA ---")
        print(f"Spot Price: {underlying_value}")
        print(f"NSE Timestamp: {timestamp}")
        print(f"Total Rows Extracted: {len(all_records)}")
        print(f"--------------------------")

        markdown = f"### 📊 NIFTY 50 Live Option Chain Data\n"
        markdown += f"**Last Updated (NSE):** {timestamp} | **NIFTY Spot Price:** {underlying_value}\n\n"
        markdown += "| CE OI | CE Change OI | CE LTP | Strike Price | PE LTP | PE Change OI | PE OI |\n"
        markdown += "| :--- | :--- | :--- | :---: | :--- | :--- | :--- |\n"

        for row in all_records[:12]:  # Shows 12 key rows surrounding ATM strike
            strike = row["strikePrice"]
            ce = row.get("CE", {})
            pe = row.get("PE", {})

            markdown += (
                f"| {ce.get('openInterest', 0)} | {ce.get('changeinOpenInterest', 0)} | {ce.get('lastPrice', 0)} "
                f"| **{strike}** "
                f"| {pe.get('lastPrice', 0)} | {pe.get('changeinOpenInterest', 0)} | {pe.get('openInterest', 0)} |\n"
            )
        return markdown
    except KeyError as e:
        print(f"-> ERROR: Structural format keys changed: {e}")
        return "### ❌ Error: Market data format mismatch."

def update_readme(new_content):
    readme_path = "README.md"
    start_tag = "<!-- NSE_DATA_START -->"
    end_tag = "<!-- NSE_DATA_END -->"

    print(f"[3/3] Commencing README.md modification updates...")
    
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write(f"# NSE Option Chain Tracker\n\n{start_tag}\n{end_tag}")

    with open(readme_path, "r") as f:
        content = f.read()

    if start_tag not in content or end_tag not in content:
        print("-> ERROR: Target placeholder comment tags are missing in README.md!")
        return

    start_idx = content.find(start_tag) + len(start_tag)
    end_idx = content.find(end_tag)
    updated_content = content[:start_idx] + f"\n\n{new_content}\n\n" + content[end_idx:]
    
    with open(readme_path, "w") as f:
        f.write(updated_content)
    print("-> SUCCESS: README.md updated successfully with fresh tables.")

if __name__ == "__main__":
    raw_data = fetch_nifty_option_chain_via_browser()
    md_table = generate_markdown_table(raw_data)
    update_readme(md_table)
