# Catamaran Listing Scraper

Searches listing sites for second-hand catamarans, extracts details, and stores results in `catamaran_models.json`.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Search all models (skips already-scraped)
python run.py

# Search a specific make
python run.py --make Lagoon

# Search a specific model
python run.py --make Lagoon --model 42

# Test with just 3 models
python run.py --limit 3

# Force re-scrape everything
python run.py --force
```

## Project Structure

```
catamaran/
├── catamaran_models.json     ← data file (fetched from / pushed to GitHub)
├── run.py                    ← orchestrator
├── search.py                 ← finds listing URLs via Claude web search
├── scrape.py                 ← downloads & parses listing pages
├── update.py                 ← merges results, deduplicates, purges old
├── requirements.txt
└── scrapers/
    ├── yachtworld.py         ← YachtWorld parser
    ├── rightboat.py          ← Rightboat parser
    ├── apolloduck.py         ← Apolloduck parser
    └── generic.py            ← Claude-powered fallback for unknown sites
```

## How It Works

1. `run.py` loads models from `catamaran_models.json` (or fetches from GitHub)
2. For each model, `search.py` asks Claude to search for listing URLs
3. Each URL is downloaded and parsed by the matching site parser
4. Unknown sites fall back to `generic.py` which uses Claude to extract data
5. Results are merged and saved after every model
6. Push updated file to GitHub when done

## Saving Results to GitHub

```bash
git add catamaran_models.json
git commit -m "Update listings $(date +%Y-%m-%d)"
git push
```

## Scheduling (cron)

```bash
# Run every morning at 8am
0 8 * * * cd /path/to/catamaran && python run.py >> run.log 2>&1
```

## Each Listing Contains

```json
{
  "url": "https://...",
  "source": "rightboat.com",
  "date_found": "2026-03-04",
  "price": 195000,
  "currency": "EUR",
  "year": 2019,
  "location": "Palma, Spain",
  "length_ft": 45.0,
  "description": "Well maintained example...",
  "photos": ["https://..."]
}
```
