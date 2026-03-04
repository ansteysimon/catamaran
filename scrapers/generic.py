"""
Generic fallback parser — uses Claude to extract structured data
from any listing page it hasn't seen before.
"""

import json
import anthropic
from bs4 import BeautifulSoup

client = anthropic.Anthropic()

SYSTEM = """Extract boat listing details from HTML text. 
Return ONLY a JSON object with these fields (use null if not found):
{
  "price": "string with currency symbol e.g. £45,000",
  "currency": "GBP|EUR|USD",
  "year": integer,
  "location": "string",
  "length_ft": float,
  "description": "first 200 chars of listing description"
}
No markdown, no explanation, just raw JSON."""


def parse(soup: BeautifulSoup, url: str, model: dict) -> dict:
    # Extract just the visible text to keep tokens low
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)[:3000]  # limit tokens

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Extract listing details from this page text:\n\n{text}"
            }]
        )
        raw = response.content[0].text.strip()
        # Strip any accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return {}
