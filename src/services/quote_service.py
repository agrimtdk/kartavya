"""
Daily Quote Service Module for kartavya (Phase 5).

Fetches a daily random productivity/inspirational quote from a public API,
caches it locally in data/daily_quote.json per calendar day, and provides
robust offline fallbacks so the application NEVER fails due to network issues.
"""

import os
import json
import html
import urllib.request
from datetime import date
import logging


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DAILY_QUOTE_FILE = os.path.join(DATA_DIR, "daily_quote.json")

FALLBACK_QUOTES = [
    {"quote": "Make today count. Own your time.", "author": "kartavya"},
    {"quote": "Correct what you can. Learn from what you can't.", "author": "Toni Morrison"},
    {"quote": "It always seems impossible until it's done.", "author": "Nelson Mandela"},
    {"quote": "Small daily improvements over time lead to stunning results.", "author": "Robin Sharma"},
    {"quote": "Focus on being productive instead of busy.", "author": "Tim Ferriss"},
    {"quote": "Done is better than perfect.", "author": "Sheryl Sandberg"},
    {"quote": "Action is the foundational key to all success.", "author": "Pablo Picasso"},
    {"quote": "You don't have to be great to start, but you have to start to be great.", "author": "Zig Ziglar"},
    {"quote": "Quality means doing it right when no one is looking.", "author": "Henry Ford"},
    {"quote": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
]


def _get_local_fallback_quote(today_iso: str) -> dict:
    """Selects a deterministic fallback quote based on today's date ordinal."""
    try:
        d_obj = date.fromisoformat(today_iso)
        idx = d_obj.toordinal() % len(FALLBACK_QUOTES)
    except Exception:
        idx = 0
    return FALLBACK_QUOTES[idx]


def _fetch_from_api() -> dict | None:
    """Attempts to fetch a quote from public APIs with a 3.0 second timeout."""
    # 1. Primary: ZenQuotes daily quote API
    try:
        req = urllib.request.Request(
            "https://zenquotes.io/api/today",
            headers={"User-Agent": "kartavya-app/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0 and "q" in data[0] and "a" in data[0]:
                q_text = html.escape(str(data[0]["q"]).strip())
                a_text = html.escape(str(data[0]["a"]).strip())
                return {"quote": q_text, "author": a_text}
    except Exception as e:
        logger.warning(f"ZenQuotes API failed: {e}")

    # 2. Secondary: DummyJSON random quotes API
    try:
        req = urllib.request.Request(
            "https://dummyjson.com/quotes/random",
            headers={"User-Agent": "kartavya-app/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "quote" in data and "author" in data:
                q_text = html.escape(str(data["quote"]).strip())
                a_text = html.escape(str(data["author"]).strip())
                return {"quote": q_text, "author": a_text}
    except Exception as e:
        logger.warning(f"DummyJSON API failed: {e}")

    return None



def get_daily_quote(today_ref: date | None = None) -> dict:
    """
    Returns the daily quote dict {"quote": str, "author": str}.
    Caches quote locally per calendar day in data/daily_quote.json.
    Never raises an exception or blocks execution.
    """
    d_obj = today_ref or date.today()
    today_iso = d_obj.isoformat()

    # 1. Check local cached file
    if os.path.exists(DAILY_QUOTE_FILE):
        try:
            with open(DAILY_QUOTE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, dict) and cached.get("date") == today_iso:
                if "quote" in cached and "author" in cached:
                    return {"quote": cached["quote"], "author": cached["author"]}
        except Exception as e:
            logger.warning(f"Failed to read daily_quote.json: {e}")

    # 2. Fetch fresh quote from API
    fetched = _fetch_from_api()
    if not fetched:
        fetched = _get_local_fallback_quote(today_iso)

    # 3. Cache fetched quote locally for today
    payload = {
        "date": today_iso,
        "quote": fetched["quote"],
        "author": fetched["author"],
    }
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DAILY_QUOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to cache daily quote: {e}")

    return fetched
