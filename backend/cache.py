# backend/cache.py
import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")
CACHE_TTL_MINUTES = 10  # cache expiration time


# ------------------------------------------------------
# Initialize database
# ------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS price_cache (
        symbol TEXT PRIMARY KEY,
        price REAL NOT NULL,
        previous_close REAL NOT NULL,
        timestamp TEXT NOT NULL,
        cached_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


# ------------------------------------------------------
# Save stock price to cache
# ------------------------------------------------------
def save_cached_price(symbol: str, price: float, previous_close: float, timestamp: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute("""
    INSERT INTO price_cache (symbol, price, previous_close, timestamp, cached_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(symbol)
    DO UPDATE SET
        price = excluded.price,
        previous_close = excluded.previous_close,
        timestamp = excluded.timestamp,
        cached_at = excluded.cached_at
    """, (symbol, price, previous_close, timestamp, now))

    conn.commit()
    conn.close()


# ------------------------------------------------------
# Fetch cached price if not expired
# ------------------------------------------------------
def get_cached_price(symbol: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT price, previous_close, timestamp, cached_at FROM price_cache WHERE symbol = ?", (symbol,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    price, previous_close, timestamp, cached_at = row

    cached_time = datetime.fromisoformat(cached_at)
    now = datetime.utcnow()

    # If cache expired, remove and return None
    if now - cached_time > timedelta(minutes=CACHE_TTL_MINUTES):
        cur.execute("DELETE FROM price_cache WHERE symbol = ?", (symbol,))
        conn.commit()
        conn.close()
        return None

    conn.close()

    return {
        "price": price,
        "previous_close": previous_close,
        "timestamp": timestamp
    }


# ------------------------------------------------------
# Optional: Clean up expired cache entries
# ------------------------------------------------------
def clear_expired_entries():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cutoff = datetime.utcnow() - timedelta(minutes=CACHE_TTL_MINUTES)

    cur.execute("DELETE FROM price_cache WHERE cached_at < ?", (cutoff.isoformat(),))
    conn.commit()
    conn.close()
