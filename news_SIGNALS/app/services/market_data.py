import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import logging
from app.services.proxy_manager import proxy_manager

logger = logging.getLogger(__name__)

MARKET_DATA_FILE = "data/market_history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def fetch_usd_lkr():
    """Fetch live USD to LKR exchange rate"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        rate = response.json()["rates"]["LKR"]
        logger.info(f"Fetched USD/LKR rate: {rate}")
        return rate
    except Exception as e:
        logger.error(f"Error fetching USD/LKR rate: {e}")
        return None

def fetch_gold_price():
    """Fetch live 24K gold price per gram in LKR"""
    try:
        url = "https://www.livepriceofgold.com/sri-lanka-gold-price.html"
        resp = proxy_manager.make_request(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for the table cell containing "1 GRAM GOLD 24K"
        row = soup.find(lambda tag: tag.name == "td" and "1 GRAM GOLD 24K" in tag.get_text())
        if not row:
            logger.error("Could not find 24K gram price row")
            return None
        
        # The price should be in the next sibling cell
        price_td = row.find_next_sibling("td")
        price_text = price_td.get_text().strip()
        # Remove commas and parse to float
        price = float(price_text.replace(",", ""))
        logger.info(f"Fetched gold price: {price} LKR/gram")
        return price
    except Exception as e:
        logger.error(f"Error fetching gold price: {e}")
        return None

def fetch_fuel_prices():
    """Fetch live fuel prices from CEYPETCO"""
    try:
        url = "https://ceypetco.gov.lk/marketing-sales/"
        resp = proxy_manager.make_request(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_="price-card")
        
        fuel_data = {}
        
        for card in cards:
            name_tag = card.find("h3", class_="fuel-name")
            price_tag = card.find("div", class_="price-value")
            
            if name_tag and price_tag:
                name = name_tag.get_text(strip=True)
                price_text = price_tag.get_text()
                price = float(price_text.replace("Rs.", "").replace("per Ltr", "").strip())
                fuel_data[name] = price
        
        logger.info(f"Fetched fuel prices: {fuel_data}")
        return fuel_data
    except Exception as e:
        logger.error(f"Error fetching fuel prices: {e}")
        return None

def fetch_inflation():
    """Fetch inflation rate from FRED (Federal Reserve Economic Data)"""
    try:
        from io import StringIO
        import pandas as pd
        
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DDOE02LKA086NWDB"
        resp = proxy_manager.make_request(url, timeout=10)
        resp.raise_for_status()
        
        df = pd.read_csv(StringIO(resp.text))
        # Get the most recent non-null value
        df = df.dropna()
        if not df.empty:
            latest = df.iloc[-1]
            inflation_rate = float(latest.iloc[1])  # Second column is the value
            logger.info(f"Fetched inflation rate: {inflation_rate}%")
            return inflation_rate
        return None
    except Exception as e:
        logger.error(f"Error fetching inflation: {e}")
        return None

def load_market_history():
    """Load historical market data from JSON file"""
    if not os.path.exists(MARKET_DATA_FILE):
        return {
            "usd_lkr": [],
            "gold": [],
            "fuel": [],
            "inflation": []
        }
    
    try:
        with open(MARKET_DATA_FILE, 'r') as f:
            data = json.load(f)
            # Ensure inflation key exists for backward compatibility
            if "inflation" not in data:
                data["inflation"] = []
            return data
    except Exception as e:
        logger.error(f"Error loading market history: {e}")
        return {
            "usd_lkr": [],
            "gold": [],
            "fuel": [],
            "inflation": []
        }

def save_market_history(history):
    """Save historical market data to JSON file"""
    try:
        os.makedirs(os.path.dirname(MARKET_DATA_FILE), exist_ok=True)
        with open(MARKET_DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        logger.info("Market history saved successfully")
    except Exception as e:
        logger.error(f"Error saving market history: {e}")

def update_market_data():
    """Fetch current market data and update history"""
    history = load_market_history()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch USD/LKR
    usd_rate = fetch_usd_lkr()
    if usd_rate:
        # Check if today's data already exists
        if not history["usd_lkr"] or history["usd_lkr"][-1]["date"] != today:
            history["usd_lkr"].append({
                "date": today,
                "value": usd_rate
            })
            # Keep only last 30 days
            history["usd_lkr"] = history["usd_lkr"][-30:]
    
    # Fetch Gold Price
    gold_price = fetch_gold_price()
    if gold_price:
        if not history["gold"] or history["gold"][-1]["date"] != today:
            history["gold"].append({
                "date": today,
                "value": gold_price
            })
            history["gold"] = history["gold"][-30:]
    
    # Fetch Fuel Prices
    fuel_prices = fetch_fuel_prices()
    if fuel_prices:
        if not history["fuel"] or history["fuel"][-1]["date"] != today:
            history["fuel"].append({
                "date": today,
                "values": fuel_prices
            })
            history["fuel"] = history["fuel"][-30:]
    
    # Fetch Inflation Rate
    inflation_rate = fetch_inflation()
    if inflation_rate is not None:
        if not history["inflation"] or history["inflation"][-1]["date"] != today:
            history["inflation"].append({
                "date": today,
                "value": inflation_rate
            })
            history["inflation"] = history["inflation"][-30:]
    
    save_market_history(history)
    return history

def get_usd_lkr_data():
    """Get USD/LKR current and historical data"""
    history = load_market_history()
    current = fetch_usd_lkr()
    
    return {
        "current": current,
        "history": history.get("usd_lkr", [])
    }

def get_gold_data():
    """Get gold price current and historical data"""
    history = load_market_history()
    current = fetch_gold_price()
    
    return {
        "current": current,
        "history": history.get("gold", [])
    }

def get_fuel_data():
    """Get fuel prices current and historical data"""
    history = load_market_history()
    current = fetch_fuel_prices()
    
    return {
        "current": current,
        "history": history.get("fuel", [])
    }

def get_inflation_data():
    """Get inflation rate current and historical data"""
    history = load_market_history()
    current = fetch_inflation()
    
    return {
        "current": current,
        "history": history.get("inflation", [])
    }

def initialize_sample_data():
    """Initialize 30 days of sample historical data for demonstration"""
    import random
    
    history = load_market_history()
    
    # Only initialize if data is empty
    if history["usd_lkr"] or history["gold"] or history["fuel"] or history["inflation"]:
        logger.info("Historical data already exists, skipping sample data initialization")
        return
    
    logger.info("Initializing 30 days of sample market data...")
    
    # Generate 30 days of data
    base_date = datetime.now() - timedelta(days=29)
    
    # USD/LKR - realistic range around 308
    usd_base = 308.0
    for i in range(30):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        # Add realistic daily variation
        variation = random.uniform(-1.0, 1.0)
        value = usd_base + variation + (i * 0.02)
        history["usd_lkr"].append({
            "date": date,
            "value": round(value, 2)
        })
    
    # Gold - realistic range around 41,000-42,000 LKR per gram
    gold_base = 41800.0
    for i in range(30):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        variation = random.uniform(-200, 200)
        value = gold_base + variation + (i * 5)
        history["gold"].append({
            "date": date,
            "value": round(value, 2)
        })
    
    # Fuel - realistic prices (Updated for Dec 2025)
    fuel_base = {
        "Lanka Petrol 92 Octane": 294.0,
        "Lanka Petrol 95 Octane Euro 4": 335.0,
        "Lanka Auto Diesel": 277.0
    }
    
    for i in range(30):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        fuel_values = {}
        for fuel_type, base_price in fuel_base.items():
            # Fuel prices change less frequently
            variation = 0  # Fixed mostly
            value = base_price + variation
            fuel_values[fuel_type] = round(value, 2)
        
        history["fuel"].append({
            "date": date,
            "values": fuel_values
        })
    
    # Inflation (CPI Index) - around 145-150
    inflation_base = 145.0
    for i in range(30):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        variation = random.uniform(-0.1, 0.2)
        value = inflation_base + variation + (i * 0.05)
        history["inflation"].append({
            "date": date,
            "value": round(value, 2)
        })
    
    save_market_history(history)
    logger.info("Sample data initialized successfully")
