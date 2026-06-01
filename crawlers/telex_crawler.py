"""Telex sitemap crawler.

This script fetches all daily Telex sitemap XML files that fall within the
shared `RELEVANT_DATE_RANGE` and returns all URLs contained in them.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import requests
from xml.etree import ElementTree as ET

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from media_outlets import OUTLET_SETTINGS, RELEVANT_DATE_RANGE, DEFAULT_REQUEST_HEADERS


def build_date_range(start_date: str, end_date: str) -> List[datetime]:
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def build_sitemap_urls(template: str, days: List[datetime]) -> List[str]:
    return [template.format(year=day.year, month=f"{day.month:02d}", day=f"{day.day:02d}") for day in days]


def fetch_sitemap(url: str, timeout: int = 15) -> str:
    last_exc = None
    for attempt in range(1, 6):
        try:
            resp = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            last_exc = e
            wait = 2 ** attempt
            print(f'  fetch attempt {attempt} failed for {url}, retrying in {wait}s...')
            from time import sleep
            sleep(wait)
    raise last_exc


def parse_sitemap_urls(xml_text: str) -> List[str]:
    root = ET.fromstring(xml_text)
    urls = []
    for loc in root.findall(".//{*}loc"):
        if loc.text:
            urls.append(loc.text.strip())
    return urls


def collect_telex_urls() -> List[str]:
    telex = OUTLET_SETTINGS.get("telex")
    if not telex:
        raise ValueError("Telex outlet settings are missing from media_outlets.py")

    template = telex.get("sitemap_url_template")
    if not template:
        raise ValueError("Telex sitemap_url_template missing from media_outlets.py")

    days = build_date_range(*RELEVANT_DATE_RANGE)
    sitemap_urls = build_sitemap_urls(template, days)

    collected_urls = []
    missing = []
    for sitemap_url in sitemap_urls:
        try:
            xml_text = fetch_sitemap(sitemap_url)
        except requests.RequestException as e:
            print('  failed to fetch sitemap:', sitemap_url, e)
            missing.append(sitemap_url)
            continue
        urls = parse_sitemap_urls(xml_text)
        print(f'  parsed {len(urls)} URLs from {sitemap_url}')
        collected_urls.extend(urls)

    if missing:
        print('Missing sitemaps:', len(missing))

    return collected_urls


def main():
    parser = argparse.ArgumentParser(description="Collect Telex article URLs from daily sitemaps.")
    parser.add_argument("--out-file", default="telex_sitemap_urls.json", help="Output JSON file path")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on collected URLs (0 = no limit)")
    args = parser.parse_args()

    urls = collect_telex_urls()
    if args.limit > 0:
        urls = urls[: args.limit]

    with open(args.out_file, "w", encoding="utf-8") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

    print(f"Collected {len(urls)} URLs")
    print(f"Saved {args.out_file}")


if __name__ == "__main__":
    main()
