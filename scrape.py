"""
Downloads and parses individual listing pages.
Tries site-specific parsers first, falls back to generic Claude extraction.
"""

import re
from datetime import date
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from scrapers.yachtworld import parse as parse_yachtworld
from scrapers.rightboat import parse as parse_rightboat
from scrapers.apolloduck import parse as parse_apolloduck
from scrapers.generic import parse as parse_generic

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}

SITE_PARSERS = {
    "yachtworld.com": parse_yachtworld,
    "rightboat.com": parse_rightboat,
    "apolloduck.com": parse_apolloduck,
}

TIMEOUT = 20


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def fetch_page(url: str) -> str:
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=TIMEOUT) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text


def get_parser(url: str):
    host = urlparse(url).netloc.replace("www.", "")
    for site, parser in SITE_PARSERS.items():
        if site in host:
            return parser
    return parse_generic


def scrape_listing(url: str, model: dict) -> dict | None:
    """Download and parse a listing page. Returns a listing dict or None."""
    try:
        html = fetch_page(url)
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")

    soup = BeautifulSoup(html, "lxml")
    parser = get_parser(url)

    try:
        data = parser(soup, url, model)
    except Exception:
        data = parse_generic(soup, url, model)

    if not data:
        return None

    # Normalise and add metadata
    return {
        "url": url,
        "source": urlparse(url).netloc.replace("www.", ""),
        "date_found": date.today().isoformat(),
        "price": _clean_price(data.get("price")),
        "currency": data.get("currency", "EUR"),
        "year": _clean_year(data.get("year"), model),
        "location": data.get("location"),
        "length_ft": data.get("length_ft"),
        "description": data.get("description", "")[:300] if data.get("description") else None,
        "photos": data.get("photos", [])[:5],
    }


def _clean_price(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    digits = re.sub(r"[^\d]", "", str(val))
    return int(digits) if digits else None


def _clean_year(val, model: dict) -> int | None:
    if val is None:
        return None
    try:
        y = int(str(val)[:4])
        if model["year_from"] - 2 <= y <= model["year_to"] + 2:
            return y
    except (ValueError, TypeError):
        pass
    return None
