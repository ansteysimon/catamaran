"""
Uses Claude with web_search tool to find listing URLs for a given catamaran model.
"""

import json
import anthropic

client = anthropic.Anthropic()

LISTING_SITES = [
    "yachtworld.co.uk",
    "boats.com",
    "rightboat.com",
    "apolloduck.com",
    "boattrader.com",
    "ybw.com",
    "ancasta.com",
    "multihullsolutions.co.uk",
    "catamaransite.com",
    "sailboatlistings.com",
]

_SITE_CONSTRAINTS = " OR ".join(f"site:{s}" for s in LISTING_SITES)

SYSTEM_PROMPT = f"""You are a marine listing researcher. Use web_search to find second-hand catamaran listings.
Return ONLY a JSON array of URL strings — actual listing pages, not search result pages.
No markdown, no explanation, just a raw JSON array like: ["https://...", "https://..."]
Only include URLs from these sites: {", ".join(LISTING_SITES)}. Maximum 10 URLs."""


def find_listing_urls(model: dict) -> list[str]:
    """Search for listing URLs for a given model dict."""
    query = (
        f'{model["search_query"]} '
        f'year:{model["year_from"]}-{model["year_to"]} '
        f'{_SITE_CONSTRAINTS}'
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": f"Find second-hand listings for: {query}"}],
    )

    # Extract text from response
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    # Parse JSON array from response
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []

    try:
        urls = json.loads(text[start:end + 1])
        return [u for u in urls if isinstance(u, str) and any(s in u for s in LISTING_SITES)]
    except json.JSONDecodeError:
        return []
