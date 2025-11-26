# backend/app.py
import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from model import StockPriceSentimentPredictor
import logging
import certifi

# ------------------------
# Logging
# ------------------------
logging.basicConfig(level=logging.INFO)

# ------------------------
# Environment variables
# ------------------------
API_NEWS_KEY = os.environ.get("NEWS_API_KEY")
API_NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

# ------------------------
# FastAPI setup
# ------------------------
app = FastAPI(title="Stock Sentiment API")

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://quantsent.sonit7cloud.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Pydantic models
# ------------------------
class PredictRequest(BaseModel):
    headlines: List[str]

class NewsArticle(BaseModel):
    title: str
    description: str
    sentiment: str
    date: str

class StockApiResponse(BaseModel):
    results: List[NewsArticle]
    symbol: str
    page: int
    per_page: int
    total_results: int
    current_price: float
    previous_close: float
    timestamp: str

# ------------------------
# Load ML artifacts
# ------------------------
predictor = StockPriceSentimentPredictor(model_type="SVC")
logging.info("Successfully loaded model, vectorizer, and encoder.")

# ------------------------
# Routes
# ------------------------
@app.post("/predict")
def predict_sentiment(req: PredictRequest):
    if not req.headlines:
        raise HTTPException(status_code=400, detail="No headlines provided")
    try:
        sentiments = predictor.predict(req.headlines)
        return {"sentiments": sentiments}
    except Exception as e:
        logging.error(f"Error during sentiment prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}")
def get_stock(
    symbol: str,
    page: int = 1,
    per_page: int = 5,
    sentiment: str = "all",
    range: str = Query("1d", regex="^(1d|3d|7d|30d)$")
):
    """
    Fetch stock price from Yahoo Finance and news from NewsAPI.
    Supports pagination, sentiment filtering, and date range filtering.
    """
    # ------------------------
    # 1. Fetch stock price from Yahoo Finance
    # ------------------------
    try:
        yf_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        resp = requests.get(yf_url, verify=certifi.where(), timeout=10)
        resp.raise_for_status()
        chart_data = resp.json()

        result = chart_data.get("chart", {}).get("result")
        if not result:
            raise ValueError(f"No data found for {symbol} in Yahoo Finance response.")

        meta = result[0].get("meta", {})
        current_price = meta.get("regularMarketPrice")
        previous_close = meta.get("chartPreviousClose")
        latest_timestamp = meta.get("regularMarketTime")

        if current_price is None or previous_close is None or latest_timestamp is None:
            raise ValueError(f"Incomplete price data for {symbol}")

    except Exception as e:
        logging.error(f"Yahoo Finance error for {symbol}: {e}")
        raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}: {e}")

    # ------------------------
    # 2. Fetch news from NewsAPI
    # ------------------------
    try:
        params = {
            "q": symbol,
            "apiKey": API_NEWS_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
        }
        news_resp = requests.get(API_NEWS_ENDPOINT, params=params, timeout=10).json()
        articles = news_resp.get("articles", [])

        headlines = [a.get("title", "") for a in articles]
        sentiments_list = predictor.predict(headlines) if headlines else []

        now = datetime.utcnow()
        cutoff = {
            "1d": now - timedelta(days=1),
            "3d": now - timedelta(days=3),
            "7d": now - timedelta(days=7),
            "30d": now - timedelta(days=30)
        }[range]

        news_list = []
        for idx, article in enumerate(articles):
            s = sentiments_list[idx] if idx < len(sentiments_list) else "neutral"
            published_at = article.get("publishedAt", "")
            article_date = datetime.fromisoformat(published_at.replace("Z", "+00:00")) if published_at else now

            if sentiment != "all" and s != sentiment:
                continue
            if article_date < cutoff:
                continue

            news_list.append(NewsArticle(
                title=article.get("title", ""),
                description=article.get("description", ""),
                sentiment=s,
                date=published_at
            ))

        total_results = len(news_list)
        paginated_news = news_list[(page-1)*per_page : page*per_page]

    except Exception as e:
        logging.error(f"Error fetching news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {e}")

    # ------------------------
    # 3. Build response
    # ------------------------
    response = StockApiResponse(
        results=paginated_news,
        symbol=symbol,
        page=page,
        per_page=per_page,
        total_results=total_results,
        current_price=current_price,
        previous_close=previous_close,
        timestamp=datetime.utcfromtimestamp(latest_timestamp).isoformat() + "Z"
    )

    return response
