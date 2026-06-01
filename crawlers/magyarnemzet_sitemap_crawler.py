"""Magyar Nemzet sitemap crawler

Fetches monthly sitemaps for Magyar Nemzet across the configured RELEVANT_DATE_RANGE
and extracts <loc> and <lastmod> (date only). Saves results to
`crawlers/magyarnemzet_sitemap_urls.json` as a list of objects:

  {"loc": "https://...", "lastmod": "YYYY-MM-DD"}

"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from xml.etree import ElementTree as ET

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from media_outlets import OUTLET_SETTINGS, RELEVANT_DATE_RANGE, DEFAULT_REQUEST_HEADERS

OUT_FILE = Path(__file__).resolve().parents[0] / "magyarnemzet_urls.json"


def iter_months(start: datetime, end: datetime):
    year = start.year
    month = start.month
    while (year, month) <= (end.year, end.month):
        yield (year, month)
        month += 1
        if month > 12:
            month = 1
            year += 1


def build_sitemap_urls(template: str, start: str, end: str) -> List[str]:
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)
    urls = []
    for year, month in iter_months(s, e):
        urls.append(template.format(year=year, month=f"{month:02d}"))
    return urls


def fetch_with_retries(url: str, attempts: int = 4, timeout: int = 15) -> str:
    last_exc = None
    headers = DEFAULT_REQUEST_HEADERS.copy()
    headers.update({"Accept": "application/xml, text/xml, */*;q=0.1"})
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            last_exc = e
            wait = 2 ** attempt
            print(f"  attempt {attempt} failed for {url}, retrying in {wait}s...")
            from time import sleep
            sleep(wait)
    raise last_exc


def parse_sitemap_entries(xml_text: str) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_text)
    entries = []
    for url_node in root.findall('.//{*}url'):
        loc = url_node.find('{*}loc')
        lastmod = url_node.find('{*}lastmod')
        if loc is None or not loc.text:
            continue
        loc_text = loc.text.strip()
        lastmod_text = None
        if lastmod is not None and lastmod.text:
            lastmod_text = lastmod.text.strip()[:10]
        entries.append({"loc": loc_text, "lastmod": lastmod_text})
    return entries


def collect_magyarnemzet_urls(save_path: str = None) -> List[Dict[str, str]]:
    cfg = OUTLET_SETTINGS.get("magyarnemzet")
    if not cfg:
        raise ValueError("Missing magyarnemzet settings in media_outlets.py")
    template = cfg.get("sitemap_url_template")
    if not template:
        raise ValueError("Missing sitemap_url_template for magyarnemzet in media_outlets.py")

    sitemap_urls = build_sitemap_urls(template, RELEVANT_DATE_RANGE[0], RELEVANT_DATE_RANGE[1])

    results = []
    for s in sitemap_urls:
        print('Fetching', s)
        try:
            xml = fetch_with_retries(s)
        except Exception as e:
            print('  failed to fetch', s, e)
            continue
        entries = parse_sitemap_entries(xml)
        print(f'  parsed {len(entries)} entries from {s}')
        results.extend(entries)

    # dedupe by loc, preserve order
    seen = set()
    unique = []
    for e in results:
        if e['loc'] not in seen:
            seen.add(e['loc'])
            unique.append(e)

    out = Path(save_path) if save_path else OUT_FILE
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(unique, fh, ensure_ascii=False, indent=2)

    print(f'Collected {len(unique)} unique entries, saved to {out}')
    return unique


if __name__ == '__main__':
    collect_magyarnemzet_urls()
