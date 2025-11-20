# app.py
import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
from model import StockPriceSentimentPredictor

# ------------------------
# Config & Initialization
# ------------------------
load_dotenv()

DB_FILE = "cache.db"
CACHE_TTL = timedelta(minutes=15)
MODEL_TYPE = "SVC"

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CORS settings
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the sentiment predictor
predictor = StockPriceSentimentPredictor(model_type=MODEL_TYPE)
if predictor.model is None or predictor.vectorizer is None or predictor.encoder is None:
    logging.info("Training sentiment model from dataset...")
    data = predictor.fetch_dataset()
    X, y = predictor.preprocess_data(data)
    predictor.train(X, y)
else:
    logging.info("Loaded existing sentiment model artifacts.")

# ------------------------
# DB Initialization
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
# API Endpoints
# ------------------------
@app.get("/stock/{symbol}")
def get_stock(
    symbol: str,
    sentiment: str = Query("all", regex="^(all|positive|negative|neutral)$")
):
    """Return stock info and news with sentiment and actual published date."""
    # Try cache
    cached_stock = db_get(symbol)
    cached_news = db_get_news(symbol)

    if cached_stock is None or cached_news is None:
        logging.info(f"CACHE MISS: Fetching fresh data for {symbol}")

        # Fetch stock info
        AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY")
        if not AV_KEY:
            raise RuntimeError("Missing ALPHA_VANTAGE_KEY in environment")
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={AV_KEY}"
        resp = requests.get(url)
        resp.raise_for_status()
        js = resp.json()
        if "Global Quote" not in js or not js["Global Quote"]:
            return {"error": f"No stock data available for {symbol}", "raw_response": js}

        quote = js["Global Quote"]
        try:
            current = float(quote["05. price"])
            prev = float(quote["08. previous close"])
        except (KeyError, ValueError):
            return {"error": f"Unexpected data format for {symbol}", "raw_response": js}

        cached_stock = {
            "current_price": current,
            "previous_close": prev,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        db_set(symbol, cached_stock)

        # Fetch news
        NEWS_KEY = os.environ.get("NEWS_API_KEY")
        if not NEWS_KEY:
            raise RuntimeError("Missing NEWS_API_KEY in environment")
        news_url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_KEY}"
        news_resp = requests.get(news_url)
        news_resp.raise_for_status()
        articles = news_resp.json().get("articles", [])

        # Run sentiment prediction
        headlines = [a["title"] for a in articles]
        sentiments = predictor.predict(headlines)

        # Use actual publishedAt date for 'date' field
        news_list = [
            {
                "title": a["title"],
                "description": a.get("description", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "date": a.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                "sentiment": s
            }
            for a, s in zip(articles, sentiments)
        ]
        db_set_news(symbol, news_list)
        cached_news = news_list
    else:
        logging.info(f"CACHE HIT: Returning cached data for {symbol}")

    # Filter by sentiment
    filtered_news = cached_news if sentiment == "all" else [a for a in cached_news if a.get("sentiment") == sentiment]

    return {
        "symbol": symbol,
        "data": {
            "stock_info": cached_stock,
            "news": filtered_news,  # frontend can filter further by date range
            "pagination": {
                "page": 1,
                "per_page": len(filtered_news),
                "total_articles": len(filtered_news),
                "total_pages": 1
            }
        }
    }


@app.post("/predict")
def predict_sentiment(payload: dict):
    headlines = payload.get("headlines", [])
    if not headlines:
        raise HTTPException(status_code=400, detail="No headlines provided.")

    try:
        sentiments = predictor.predict(headlines)
        return {"headlines": headlines, "sentiments": sentiments.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
