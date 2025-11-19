# app.py
import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
import requests
from fastapi import FastAPI
from typing import Optional, List

DB_FILE = "cache.db"
CACHE_TTL = timedelta(minutes=15)

app = FastAPI()

# ------------------------
# Initialize DB tables if not exist
# ------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_cache (
            symbol TEXT PRIMARY KEY,
            data TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            symbol TEXT PRIMARY KEY,
            data TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------------
# DB Helpers
# ------------------------
def db_get(symbol: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT data, timestamp FROM stock_cache WHERE symbol = ?", (symbol,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    ts = datetime.fromisoformat(row["timestamp"])
    if datetime.now(timezone.utc) - ts > CACHE_TTL:
        return None
    return json.loads(row["data"])

def db_set(symbol: str, data: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO stock_cache (symbol, data, timestamp)
        VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET 
            data = excluded.data,
            timestamp = excluded.timestamp
    """, (symbol, json.dumps(data), datetime.now(timezone.utc).replace(microsecond=0).isoformat()))
    conn.commit()
    conn.close()

def db_get_news(symbol: str) -> Optional[List[dict]]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT data, timestamp FROM news_cache WHERE symbol = ?", (symbol,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    ts = datetime.fromisoformat(row["timestamp"])
    if datetime.now(timezone.utc) - ts > CACHE_TTL:
        return None
    return json.loads(row["data"])

def db_set_news(symbol: str, data: List[dict]):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO news_cache (symbol, data, timestamp)
        VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET 
            data = excluded.data,
            timestamp = excluded.timestamp
    """, (symbol, json.dumps(data), datetime.now(timezone.utc).replace(microsecond=0).isoformat()))
    conn.commit()
    conn.close()

# ------------------------
# Dummy ML Sentiment Function
# ------------------------
def run_sentiment(headlines: List[str]) -> List[str]:
    # Placeholder logic: classify each headline
    sentiments = []
    for h in headlines:
        if "bad" in h.lower():
            sentiments.append("negative")
        elif "good" in h.lower():
            sentiments.append("positive")
        else:
            sentiments.append("neutral")
    return sentiments

# ------------------------
# API Endpoints
# ------------------------
@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    # 1. Try cache
    cached_stock = db_get(symbol)
    cached_news = db_get_news(symbol)

    if cached_stock and cached_news:
        return {"symbol": symbol, "data": {"stock_info": cached_stock, "news": cached_news}}

    # 2. Fetch stock info
    # Replace YOUR_ALPHA_VANTAGE_KEY with real key in production
    AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "demo")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={AV_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    js = resp.json()["Global Quote"]
    current = float(js["05. price"])
    prev = float(js["08. previous close"])
    stock_data = {"current_price": current, "previous_close": prev, "timestamp": datetime.now(timezone.utc).isoformat()}
    db_set(symbol, stock_data)

    # 3. Fetch news
    # Replace YOUR_NEWSAPI_KEY with real key in production
    NEWS_KEY = os.environ.get("NEWSAPI_KEY", "demo")
    news_url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_KEY}"
    news_resp = requests.get(news_url)
    news_resp.raise_for_status()
    articles = news_resp.json().get("articles", [])
    news_list = [{"title": a["title"], "description": a.get("description", ""), "fetched_at": datetime.now(timezone.utc).isoformat()} for a in articles]
    db_set_news(symbol, news_list)

    return {"symbol": symbol, "data": {"stock_info": stock_data, "news": news_list}}

@app.post("/predict")
def predict_sentiment(payload: dict):
    headlines = payload.get("headlines", [])
    sentiments = run_sentiment(headlines)
    return {"headlines": headlines, "sentiments": sentiments}
