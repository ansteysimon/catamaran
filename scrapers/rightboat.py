"""Parser for rightboat.com listing pages."""

from bs4 import BeautifulSoup
import re


def parse(soup: BeautifulSoup, url: str, model: dict) -> dict:
    data = {}

    # Price
    price_el = soup.select_one(".price, [itemprop='price'], [class*='asking']")
    if price_el:
        data["price"] = price_el.get_text(strip=True)
        # Detect currency
        text = price_el.get_text()
        if "£" in text:
            data["currency"] = "GBP"
        elif "€" in text:
            data["currency"] = "EUR"
        elif "$" in text:
            data["currency"] = "USD"

    # Specs table
    for row in soup.select("tr, [class*='spec-row'], [class*='attribute']"):
        cells = row.find_all(["td", "dd", "span"])
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            if "year" in key:
                m = re.search(r"\b(19|20)\d{2}\b", val)
                if m:
                    data["year"] = int(m.group())
            elif "length" in key or "loa" in key:
                m = re.search(r"(\d+\.?\d*)", val)
                if m:
                    data["length_ft"] = float(m.group(1))
            elif "location" in key or "country" in key or "berth" in key:
                data["location"] = val

    # Description
    desc = soup.select_one("[class*='description'], [itemprop='description']")
    if desc:
        data["description"] = desc.get_text(" ", strip=True)

    # Photos
    data["photos"] = list({
        img["src"] for img in soup.select("img")
        if img.get("src", "").startswith("http") and any(
            x in img.get("src", "") for x in ["boat", "yacht", "image", "photo", "media"]
        )
    })[:5]

    return data or None
