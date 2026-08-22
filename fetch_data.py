import json
import os
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
        session.get(HOME_URL, timeout=15)
        time.sleep(2)  # Delay to avoid instant block
        response = session.get(API_URL, timeout=15)
        if response.status_code == 200:
            return response.json()
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def generate_markdown_table(data):
    if not data:
        return "### ❌ Error: Could not fetch live data from NSE."

    underlying_value = data["records"]["underlyingValue"]
    timestamp = data["records"]["timestamp"]

    # Pull nearest 5 strikes around ATM for cleaner display
    all_records = data["filtered"]["data"]

    markdown = f"### 📊 NIFTY 50 Live Option Chain Data\n"
    markdown += f"**Last Updated (NSE):** {timestamp} | **NIFTY Spot Price:** {underlying_value}\n\n"
    markdown += "| CE OI | CE Change OI | CE LTP | Strike Price | PE LTP | PE Change OI | PE OI |\n"
    markdown += "| :--- | :--- | :--- | :---: | :--- | :--- | :--- |\n"

    # Take a snippet of the first 10 rows for optimal README scannability
    for row in all_records[:10]:
        strike = row["strikePrice"]
        ce = row.get("CE", {})
        pe = row.get("PE", {})

        markdown += (
            f"| {ce.get('openInterest', 0)} | {ce.get('changeinOpenInterest', 0)} | {ce.get('lastPrice', 0)} "
            f"| **{strike}** "
            f"| {pe.get('lastPrice', 0)} | {pe.get('changeinOpenInterest', 0)} | {pe.get('openInterest', 0)} |\n"
        )

    return markdown


def update_readme(new_content):
    readme_path = "README.md"

    # Ensure the file exists
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write(
                "# NSE Option Chain Tracker\n\n<!-- NSE_DATA_START -->\n<!-- NSE_DATA_END -->"
            )

    with open(readme_path, "r") as f:
        content = f.read()

    start_tag = "<!-- NSE_DATA_START -->"
    end_tag = "<!-- NSE_DATA_END -->"

    if start_tag in content and end_tag in content:
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        updated_content = f"{before}{start_tag}\n\n{new_content}\n\n{end_tag}{after}"

        with open(readme_path, "w") as f:
            f.write(updated_content)
        print("README.md updated successfully!")
    else:
        print("Error: Could not find placeholders in README.md")


if __name__ == "__main__":
    raw_data = fetch_nifty_option_chain()
    md_table = generate_markdown_table(raw_data)
    update_readme(md_table)
