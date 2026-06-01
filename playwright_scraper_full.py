"""Playwright-based scraper for JavaScript-heavy websites."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from media_outlets import (
    BODY_SELECTORS, 
    EXCLUDE_SELECTORS,
    OUTLET_TYPE,
    TEXT_SELECTORS,
    TITLE_SELECTORS,
    TOPIC_TAG_SELECTORS
)

ROOT_DIR = Path(__file__).resolve().parent
URLS_DIR = ROOT_DIR / "filtered_urls" / "magyarnemzet"  # Adjust this to target specific outlets or use all subdirs
DEFAULT_OUTPUT = ROOT_DIR / "new_mn_articles.json"


def normalize_topic(value: Optional[str]) -> Optional[str]:
    """Normalize topic string."""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _normalize_selector(selector: object) -> List[str]:
    """Normalize CSS selectors."""
    if selector is None:
        return []
    if isinstance(selector, (list, tuple, set)):
        expanded = []
        for item in selector:
            expanded.extend(_normalize_selector(item))
        return expanded
    if not isinstance(selector, str):
        return []

    text = selector.strip()
    if not text:
        return []

    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]

    return [text]


def _collect_elements(soup: BeautifulSoup, selectors: Optional[Sequence[object]]) -> List:
    """Collect elements from soup using selectors."""
    if not selectors:
        return []

    unique = []
    seen = set()
    for selector in _normalize_selector(selectors):
        try:
            for element in soup.select(selector):
                element_id = id(element)
                if element_id in seen:
                    continue
                seen.add(element_id)
                unique.append(element)
        except Exception:
            continue
    return unique


def _select_texts(soup: BeautifulSoup, selectors: Optional[Sequence[object]], outlet: Optional[str] = None) -> List[str]:
    """Extract text from elements using selectors."""
    texts = []
    for element in _collect_elements(soup, selectors):
        if outlet:
            for exclude_selector in EXCLUDE_SELECTORS.get(outlet, []):
                try:
                    for unwanted in element.select(exclude_selector):
                        unwanted.decompose()
                except Exception:
                    continue
        text = element.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return list(dict.fromkeys(texts))


def parse_article(html: str, url: str, outlet: str) -> Dict[str, object]:
    """Parse article HTML into structured data."""
    soup = BeautifulSoup(html, "html.parser")

    title_selectors = TITLE_SELECTORS.get(outlet) or ["h1"]
    text_selectors = TEXT_SELECTORS.get(outlet) or BODY_SELECTORS.get(outlet) or ["p"]
    body_selectors = text_selectors or BODY_SELECTORS.get(outlet) or ["p"]
    tag_selectors = TOPIC_TAG_SELECTORS.get(outlet) or []

    title = _select_texts(soup, title_selectors)
    date = _select_texts(soup, ["time[datetime]", "time"])

    body_texts = _select_texts(soup, body_selectors, outlet=outlet)
    if body_texts:
        body_text = "\n\n".join(body_texts)
    else:
        paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
        body_text = "\n\n".join([paragraph for paragraph in paragraphs if paragraph])

    tags = _select_texts(soup, tag_selectors, outlet=outlet)
    tags = list(dict.fromkeys([tag for tag in tags if tag])) or None

    excerpt = _select_texts(soup, ["meta[name=description]"]) or (body_text[:300] if body_text else None)

    return {
        "url": url,
        "title": title,
        "date": date,
        "main_topic": None,
        "tags": tags,
        "excerpt": excerpt,
        "body": body_text,
    }


def fetch_page_rendered(url: str, timeout: int = 15000) -> Optional[str]:
    """Fetch and render a single page with Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"    [FAIL] {url} — {type(e).__name__}: {e}")
        return None


def scrape_articles_rendered(
    records: Iterable[Mapping[str, object]],
    delay: float = 1.5,
    timeout: int = 15000
) -> List[dict]:
    """Scrape articles using Playwright for JavaScript-rendered content."""
    articles = []
    records = list(records)
    total = len(records)
    failed = 0
    no_body = 0

    print(f"\n[PLAYWRIGHT] Starting — {total} articles to fetch\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for i, record in enumerate(records, 1):
            url = str(record.get("url", "")).strip()
            outlet = str(record.get("outlet", "")).strip().lower()
            
            if not url:
                continue

            if i % 50 == 0 or i == 1:
                print(f"  [{i}/{total}] outlet={outlet}  url={url[:80]}")

            page = browser.new_page()
            try:
                page.goto(url, timeout=timeout)
                page.wait_for_load_state("domcontentloaded")
                html = page.content()
                article = parse_article(html, url, outlet)
                article["outlet"] = str(record.get("outlet", "")).strip()
                article["outlet_type"] = OUTLET_TYPE.get(outlet)
                article["date"] = record.get("date") or article.get("date")
                article["main_topic"] = normalize_topic(record.get("main_topic"))

                if not article.get("body"):
                    no_body += 1
                    print(f"    [WARN] No body extracted: {url}")
                if not article.get("title"):
                    print(f"    [WARN] No title extracted: {url}")
                
                # Log success
                title = (article.get("title") or [""])[0][:60] if article.get("title") else "No title"
                print(f"    [OK] {title}")

                articles.append(article)
            except Exception as e:
                print(f"    [FAIL] {url} — {type(e).__name__}: {e}")
                failed += 1
            finally:
                page.close()
            
            time.sleep(delay)
        
        browser.close()

    print(f"\n[PLAYWRIGHT] Done — {len(articles)} scraped | {failed} failed | {no_body} missing body")
    return articles


def load_url_records(paths: Optional[Sequence[Path]] = None) -> List[dict]:
    """Load URL records from JSON files."""
    if paths is None:
        paths = sorted(URLS_DIR.glob("*.json"))

    records: List[dict] = []
    for path in paths:
        if not path.exists():
            print(f"  [WARN] File not found, skipping: {path}")
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            count = 0
            for entry in raw:
                if not isinstance(entry, dict):
                    continue
                if not entry.get("url"):
                    continue
                records.append(dict(entry))
                count += 1
            print(f"  [LOAD] {path.name}: {count} records")
        except Exception as e:
            print(f"  [ERROR] Failed to load {path.name}: {e}")
    
    return records


def save_articles(articles: List[dict], output_path: str):
    """Save articles to JSON or CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.suffix.lower() == ".csv":
        fieldnames = ["outlet", "outlet_type", "date", "url", "title", "main_topic", "excerpt", "body", "tags"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for article in articles:
                row = dict(article)
                row["tags"] = "; ".join(row.get("tags") or [])
                writer.writerow(row)
        print(f"[SAVE] Written to {path} (CSV, {len(articles)} rows)")
        return

    path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVE] Written to {path} (JSON, {len(articles)} articles)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape article bodies using Playwright for JavaScript-rendered content."
    )
    parser.add_argument("--out-file", default=str(DEFAULT_OUTPUT), help="Output path (.json or .csv).")
    parser.add_argument("--input-dir", default=str(URLS_DIR), help="Directory containing filtered URL JSON files.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on the number of articles to scrape.")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between requests in seconds.")
    parser.add_argument("--timeout", type=int, default=60000, help="Page load timeout in milliseconds (default: 60000).")
    parser.add_argument("--wait-state", choices=["domcontentloaded", "networkidle"], default="domcontentloaded", help="Wait state: domcontentloaded (faster) or networkidle (slower).")
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    print(f"[START] Loading records from {args.input_dir}")

    records = load_url_records(sorted(Path(args.input_dir).glob("*.json")))

    if args.limit and args.limit > 0:
        records = records[:args.limit]
        print(f"  [LIMIT] Capped at {args.limit} records")

    articles = scrape_articles_rendered(records, delay=args.delay, timeout=args.timeout)
    save_articles(articles, args.out_file)
    print(f"\n[DONE] {len(articles)} articles saved to {args.out_file}")


if __name__ == "__main__":
    main()
