"""Parser for apolloduck.com listing pages."""

from bs4 import BeautifulSoup
import re


def parse(soup: BeautifulSoup, url: str, model: dict) -> dict:
    data = {}

    # Price
    for el in soup.find_all(string=re.compile(r"[£€\$]\s*[\d,]+")):
        data["price"] = el.strip()
        if "£" in el:
            data["currency"] = "GBP"
        elif "€" in el:
            data["currency"] = "EUR"
        break

    # Key details from definition lists or tables
    for el in soup.select("dt, th"):
        label = el.get_text(strip=True).lower()
        sibling = el.find_next_sibling(["dd", "td"])
        if not sibling:
            continue
        val = sibling.get_text(strip=True)
        if "year" in label:
            m = re.search(r"\b(19|20)\d{2}\b", val)
            if m:
                data["year"] = int(m.group())
        elif "loa" in label or "length" in label:
            m = re.search(r"(\d+\.?\d*)", val)
            if m:
                data["length_ft"] = float(m.group(1))
        elif "location" in label or "lying" in label or "berth" in label:
            data["location"] = val

    # Description
    desc = soup.select_one("[class*='desc'], [class*='detail'], article")
    if desc:
        data["description"] = desc.get_text(" ", strip=True)

    # Photos
    data["photos"] = [
        img["src"] for img in soup.select("img")
        if img.get("src", "").startswith("http")
        and any(x in img.get("src", "").lower() for x in ["boat", "yacht", "image", "upload"])
    ][:5]

    return data or None
