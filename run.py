"""
Catamaran listing scraper — main entrypoint.
Usage:
  python run.py
  python run.py --make Lagoon
  python run.py --make Lagoon --model 42
  python run.py --limit 3
  python run.py --force
"""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from search import find_listing_urls
from scrape import scrape_listing
from update import merge_listings

console = Console()
DATA_FILE = Path("catamaran_models.json")
GITHUB_URL = "https://raw.githubusercontent.com/ansteysimon/catamaran/main/catamaran_models.json"


def load_models() -> list:
    if DATA_FILE.exists():
        console.print(f"[dim]Loading models from {DATA_FILE}[/dim]")
        return json.loads(DATA_FILE.read_text())
    else:
        import httpx
        console.print(f"[dim]Fetching models from GitHub...[/dim]")
        r = httpx.get(GITHUB_URL, timeout=15)
        r.raise_for_status()
        models = r.json()
        DATA_FILE.write_text(json.dumps(models, indent=2))
        return models


def save_models(models: list):
    DATA_FILE.write_text(json.dumps(models, indent=2))


def filter_models(models, make=None, model=None, force=False):
    filtered = models
    if make:
        filtered = [m for m in filtered if m["make"].lower() == make.lower()]
    if model:
        filtered = [m for m in filtered if str(m["model"]).lower() == model.lower()]
    if not force:
        filtered = [m for m in filtered if len(m.get("listings", [])) == 0]
    return filtered


def print_summary(models):
    table = Table(title="Scrape Summary", show_header=True)
    table.add_column("Make", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Year Range", style="dim")
    table.add_column("Listings", style="green")
    for m in models:
        table.add_row(
            m["make"], str(m["model"]),
            f"{m['year_from']}–{m['year_to']}",
            str(len(m.get("listings", [])))
        )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Catamaran listing scraper")
    parser.add_argument("--make", help="Filter by make (e.g. Lagoon)")
    parser.add_argument("--model", help="Filter by model (e.g. 42)")
    parser.add_argument("--limit", type=int, help="Max number of models to process")
    parser.add_argument("--force", action="store_true", help="Re-scrape already-scraped models")
    args = parser.parse_args()

    console.rule("[bold cyan]⚓ Catamaran Listing Scraper[/bold cyan]")

    models = load_models()
    to_process = filter_models(models, args.make, args.model, args.force)

    if args.limit:
        to_process = to_process[:args.limit]

    if not to_process:
        console.print("[yellow]No models to process. Use --force to re-scrape existing.[/yellow]")
        return

    console.print(f"[cyan]Processing {len(to_process)} model(s)...[/cyan]\n")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=console) as progress:
        task = progress.add_task("Searching...", total=len(to_process))

        for m in to_process:
            label = f"{m['make']} {m['model']}"
            progress.update(task, description=f"[cyan]{label}[/cyan]")

            try:
                # Step 1: find listing URLs via web search
                urls = find_listing_urls(m)
                console.print(f"  [dim]{label}:[/dim] found {len(urls)} URL(s)")

                # Step 2: scrape each listing page
                new_listings = []
                for url in urls:
                    try:
                        listing = scrape_listing(url, m)
                        if listing:
                            new_listings.append(listing)
                    except Exception as e:
                        console.print(f"    [red]✗ scrape failed:[/red] {url[:60]} — {e}")

                # Step 3: merge into model
                idx = next(i for i, x in enumerate(models) if x["make"] == m["make"] and str(x["model"]) == str(m["model"]))
                models[idx] = merge_listings(models[idx], new_listings)
                console.print(f"  [green]✓[/green] {label}: {len(new_listings)} new listing(s) added")

            except Exception as e:
                console.print(f"  [red]✗ {label}: {e}[/red]")

            progress.advance(task)
            save_models(models)  # save after each model

    console.rule()
    print_summary([m for m in models if len(m.get("listings", [])) > 0])
    console.print(f"\n[green]Done. Results saved to {DATA_FILE}[/green]")
    console.print("[dim]Push to GitHub: git add . && git commit -m 'Update listings' && git push[/dim]")


if __name__ == "__main__":
    main()
