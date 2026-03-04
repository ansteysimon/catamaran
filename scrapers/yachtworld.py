"""Parser for yachtworld.com listing pages."""

from bs4 import BeautifulSoup
import re


def parse(soup: BeautifulSoup, url: str, model: dict) -> dict:
    data = {}

    # Price
    price_el = soup.select_one("[class*='price']")
    if price_el:
        data["price"] = price_el.get_text(strip=True)

    # Year, length from key specs
    for item in soup.select("[class*='spec'], [class*='detail']"):
        text = item.get_text(" ", strip=True).lower()
        if "year" in text:
            m = re.search(r"\b(19|20)\d{2}\b", text)
            if m:
                data["year"] = int(m.group())
        if "length" in text or "loa" in text:
            m = re.search(r"(\d+\.?\d*)\s*ft", text)
            if m:
                data["length_ft"] = float(m.group(1))

    # Location
    loc = soup.select_one("[class*='location'], [class*='country']")
    if loc:
        data["location"] = loc.get_text(strip=True)

    # Description
    desc = soup.select_one("[class*='description'], [class*='details']")
    if desc:
        data["description"] = desc.get_text(" ", strip=True)

    # Photos
    data["photos"] = [
        img["src"] for img in soup.select("img[src*='yacht']")
        if img.get("src", "").startswith("http")
    ][:5]

    return data or None
