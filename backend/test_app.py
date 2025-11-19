# test_app.py
import os
import json
import sqlite3
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app import (
    app,
    db_get,
    db_get_news,
    db_set,
    db_set_news,
    run_sentiment,
    CACHE_TTL,
    DB_FILE
)

client = TestClient(app)

# ------------------------
# Helper to clear tables
# ------------------------
def clear_cache_tables():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM stock_cache")
    c.execute("DELETE FROM news_cache")
    conn.commit()
    conn.close()

# ------------------------
# Helper to insert cache with custom timestamp
# ------------------------
def db_set_test(symbol: str, data: dict, table="stock_cache", timestamp=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    ts = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    c.execute(f"""
        INSERT INTO {table} (symbol, data, timestamp)
        VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET 
            data = excluded.data,
            timestamp = excluded.timestamp
    """, (symbol, json.dumps(data), ts))
    conn.commit()
    conn.close()

# ------------------------
# Fixture: clear DB before each test
# ------------------------
@pytest.fixture(autouse=True)
def run_before_tests():
    clear_cache_tables()

# ------------------------
# Cache Expiration Tests
# ------------------------
def test_stock_cache_expiration():
    old_ts = (datetime.now(timezone.utc) - CACHE_TTL - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    symbol = "EXPIRE"
    data = {"price": 42, "timestamp": old_ts}
    db_set_test(symbol, data)
    cached = db_get(symbol)
    assert cached is None  # Should expire

def test_stock_cache_fresh():
    symbol = "FRESH"
    data = {"price": 100}
    db_set_test(symbol, data)
    cached = db_get(symbol)
    assert cached["price"] == 100

def test_news_cache_expiration():
    old_ts = (datetime.now(timezone.utc) - CACHE_TTL - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    symbol = "NEWS_EXPIRE"
    data = [{"title": "Old News"}]
    db_set_test(symbol, data, table="news_cache", timestamp=old_ts)
    cached = db_get_news(symbol)
    assert cached is None  # Should expire

def test_news_cache_fresh():
    symbol = "NEWS_FRESH"
    data = [{"title": "Breaking News"}]
    db_set_test(symbol, data, table="news_cache")
    cached = db_get_news(symbol)
    assert cached[0]["title"] == "Breaking News"

# ------------------------
# Mocked ML Sentiment Test
# ------------------------
@patch("app.run_sentiment", return_value=["positive", "negative"])
def test_run_sentiment_mock(mock_sentiment):
    headlines = ["Good news", "Bad news"]
    sentiments = run_sentiment(headlines)
    # The patched function returns ["positive", "negative"]
    assert sentiments == ["positive", "negative"]

# ------------------------
# Mocked External APIs
# ------------------------
@patch("app.requests.get")
def test_api_stock_mock(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Global Quote": {"05. price": "100", "08. previous close": "90"}
    }
    mock_get.return_value = mock_response

    response = client.get("/stock/FAKE")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["stock_info"]["current_price"] == 100
    assert data["stock_info"]["previous_close"] == 90

@patch("app.requests.get")
def test_api_stock_news_mock(mock_get):
    # Mock AlphaVantage response
    alpha_response = MagicMock()
    alpha_response.status_code = 200
    alpha_response.json.return_value = {
        "Global Quote": {"05. price": "200", "08. previous close": "190"}
    }

    # Mock NewsAPI response
    news_response = MagicMock()
    news_response.status_code = 200
    news_response.json.return_value = {
        "status": "ok",
        "articles": [{"title": "Stock Up", "description": "Great day"}]
    }

    mock_get.side_effect = [alpha_response, news_response]

    response = client.get("/stock/TEST")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["stock_info"]["current_price"] == 200
    assert len(data["news"]) == 1
    assert data["news"][0]["title"] == "Stock Up"

# ------------------------
# API Predict Endpoint
# ------------------------
@patch("app.run_sentiment", return_value=["positive", "negative"])
def test_api_predict_endpoint_mock(mock_sentiment):
    payload = {"headlines": ["Headline 1", "Headline 2"]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["headlines"] == payload["headlines"]
    assert resp_json["sentiments"] == ["positive", "negative"]
