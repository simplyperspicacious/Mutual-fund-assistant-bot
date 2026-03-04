import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "phase1_ingestion", "data", "structured", "ppfas_schemes.json")

def test_scraper_json_exists():
    assert os.path.exists(DATA_PATH), f"Scraper output {DATA_PATH} does not exist."

def test_scraper_fund_count():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # We expect exactly 7 PPFAS variants
    assert len(data) == 7, f"Expected 7 mutual funds, but scraper found {len(data)}."

def test_scraper_data_formats():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    valid_riskometers = [
        "Very Low", "Low", "Moderately Low", "Moderate", 
        "Moderately High", "High", "Very High"
    ]
    
    for fund in data:
        name = fund.get("scheme_name", "Unknown")
        
        # 1. Expense Ratio: Must end with '%'
        exp = fund.get("expense_ratio", "")
        # Allow 'Unknown' if the fund legitimately hides it, but otherwise enforce %
        if exp != "Unknown":
            assert re.search(r"%$", exp), f"[{name}] Invalid expense_ratio format: {exp}"
            
        # 2. Riskometer: Must strictly be one of the 7 official SEBI categories
        risk = fund.get("riskometer_category", "")
        assert risk in valid_riskometers, f"[{name}] Invalid riskometer category: {risk}"
        
        # 3. SIP/Lumpsum: Must start with ₹ symbol or be legitimately Not specified
        sip = fund.get("minimum_sip", "")
        if sip != "Not specified":
            assert sip.startswith("₹"), f"[{name}] Invalid SIP currency format (Expected ₹): {sip}"
            
        lump = fund.get("minimum_lumpsum", "")
        if lump != "Not specified":
            assert lump.startswith("₹"), f"[{name}] Invalid Lumpsum currency format (Expected ₹): {lump}"
        
        # 4. Exit Load: Ensure it's not a tiny broken string
        exit_load = fund.get("exit_load", "")
        assert len(exit_load) > 2, f"[{name}] Exit load string is suspiciously short or empty: {exit_load}"
