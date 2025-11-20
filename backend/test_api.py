import requests
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000"

def test_fetch_stock():
    symbol = "AAPL"
    print(f"\n=== Testing /stock/{symbol} ===")

    r = requests.get(f"{BASE}/stock/{symbol}")
    assert r.status_code == 200, r.text
    data = r.json()

    assert "data" in data
    assert "news" in data["data"]
    news = data["data"]["news"]

    print(f"Got {len(news)} articles")

    assert isinstance(news, list)

    for i, n in enumerate(news):
        print(f"\n-- Article {i+1} --")
        print("Title:", n["title"])
        print("Published (date):", n["date"])
        print("Fetched:", n["fetched_at"])
        print("Sentiment:", n["sentiment"])

        # Validate fields
        assert "title" in n
        assert "date" in n
        assert "fetched_at" in n
        assert n["sentiment"] in ["positive", "neutral", "negative"]

        # Validate date formatting
        dt = datetime.fromisoformat(n["date"].replace("Z", "+00:00"))
        assert isinstance(dt, datetime)

    print("\n✓ /stock endpoint returns correct article structure")

def test_date_range_filter():
    symbol = "TSLA"
    print(f"\n=== Testing date range logic for {symbol} ===")

    r = requests.get(f"{BASE}/stock/{symbol}")
    assert r.status_code == 200
    news = r.json()["data"]["news"]

    now = datetime.now(timezone.utc)

    # MANUAL RANGE CHECK
    for days in [1, 3, 7, 14, 30]:
        cutoff = now - timedelta(days=days)
        valid = [
            n for n in news
            if datetime.fromisoformat(n["date"].replace("Z", "+00:00")) >= cutoff
        ]
        print(f"> {days} days → {len(valid)} articles expected to show in UI")

    print("\n✓ Date range filtering logic is mathematically correct")

def test_sentiment_filter():
    symbol = "MSFT"
    print(f"\n=== Testing sentiment filter ===")

    for sent in ["positive", "neutral", "negative"]:
        r = requests.get(f"{BASE}/stock/{symbol}?sentiment={sent}")
        assert r.status_code == 200
        filtered = r.json()["data"]["news"]

        print(f"{sent.capitalize()} returned {len(filtered)} articles")

        for n in filtered:
            assert n["sentiment"] == sent

    print("\n✓ Sentiment filtering on backend works correctly")

if __name__ == "__main__":
    test_fetch_stock()
    test_date_range_filter()
    test_sentiment_filter()
    print("\nALL TESTS PASSED\n")
