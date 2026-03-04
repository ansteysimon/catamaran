# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
# Requires ANTHROPIC_API_KEY in environment or .env file
export ANTHROPIC_API_KEY=your_key_here
```

## Running the Scraper

```bash
python run.py                          # scrape all models without listings
python run.py --make Lagoon            # filter by make
python run.py --make Lagoon --model 42 # filter by model
python run.py --limit 3                # process at most 3 models (for testing)
python run.py --force                  # re-scrape already-scraped models
```

## Architecture

**Pipeline**: `run.py` → `search.py` → `scrape.py` → parsers → `update.py` → `search_results.json`

1. **`run.py`** — Orchestrator. Loads `search_results.json` (fetches from GitHub as `catamaran_models.json` if absent), filters models by CLI args, loops through them, saves after each one.
2. **`search.py`** — Uses Claude's `web_search_20250305` tool to return a JSON array of listing URLs for a given model dict.
3. **`scrape.py`** — Downloads each URL with `httpx` (3-attempt retry via tenacity), selects a parser via `SITE_PARSERS` dict, normalises the returned dict into the canonical listing schema.
4. **`scrapers/`** — Site-specific parsers (`yachtworld.py`, `rightboat.py`, `apolloduck.py`) use BeautifulSoup/regex. `generic.py` falls back to Claude (`claude-sonnet-4-20250514`) to extract JSON from page text.
5. **`update.py`** — Merges new listings into a model, deduplicating by URL. Also has `deduplicate()` and `purge_old_listings()` helpers (not called from `run.py` but available for manual use).

### Model object schema

Each entry in `search_results.json` is a model dict with these fields:

```json
{
  "make": "Lagoon",
  "model": "42",
  "year_from": 2005,
  "year_to": 2015,
  "search_query": "Lagoon 42 catamaran for sale",
  "listings": []
}
```

`search_query` is the free-text string passed to web search. `listings` is populated by the scraper.

### Canonical listing schema

Each listing dict stored inside `model["listings"]`:

```
url, source, date_found, price (int), currency, year (int), location, length_ft (float), description (str, ≤300 chars), photos (list, ≤5 URLs)
```

### Adding a new site parser

1. Create `scrapers/<sitename>.py` with a `parse(soup, url, model) -> dict` function returning keys: `price`, `currency`, `year`, `location`, `length_ft`, `description`, `photos`.
2. Register it in `scrape.py`'s `SITE_PARSERS` dict with the domain as the key (no `www.`).

### Claude API usage

- **`search.py`**: Uses `web_search_20250305` tool (requires a Claude account with web search enabled). Model: `claude-sonnet-4-20250514`.
- **`scrapers/generic.py`**: Uses `claude-sonnet-4-20250514` for structured extraction from unknown listing pages.
- Both instantiate `anthropic.Anthropic()` at module level (picks up `ANTHROPIC_API_KEY` from env).

### Other files

- **`models.md`** / **`sites.md`** — scratch notes for makes/models and listing sites to target; not read by the scraper.
- **`search_results.json`** — the local data file (gitignored pattern may differ; push manually when ready).
