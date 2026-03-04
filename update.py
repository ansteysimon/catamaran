"""
Merges new listings into a model dict, deduplicating by URL.
"""

from datetime import date


def merge_listings(model: dict, new_listings: list[dict]) -> dict:
    """Add new listings to model, skipping duplicates by URL."""
    existing_urls = {l["url"] for l in model.get("listings", [])}
    added = [l for l in new_listings if l["url"] not in existing_urls]
    model.setdefault("listings", []).extend(added)
    model["last_searched"] = date.today().isoformat()
    return model


def deduplicate(model: dict) -> dict:
    """Remove duplicate URLs from a model's listings, keeping the most recent."""
    seen = {}
    for listing in model.get("listings", []):
        url = listing["url"]
        if url not in seen or listing.get("date_found", "") > seen[url].get("date_found", ""):
            seen[url] = listing
    model["listings"] = list(seen.values())
    return model


def purge_old_listings(model: dict, days: int = 90) -> dict:
    """Remove listings older than N days."""
    from datetime import datetime, timedelta
    cutoff = (datetime.today() - timedelta(days=days)).date().isoformat()
    model["listings"] = [
        l for l in model.get("listings", [])
        if l.get("date_found", "9999") >= cutoff
    ]
    return model
