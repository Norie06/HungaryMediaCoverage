"""24.hu sitemap crawler

Fetches two sitemap XML files and extracts all <loc> URLs.
Saves results to `crawlers/24hu_sitemap_urls.json`.
"""

import json
from xml.etree import ElementTree as ET
from pathlib import Path
import time
import requests

SITEMAPS = [
    "https://24.hu/app/uploads/sitemap/24.hu_sitemap_0.xml",
    "https://24.hu/app/uploads/sitemap/24.hu_sitemap_1.xml",
]

OUT_FILE = Path(__file__).resolve().parents[0] / "24hu_urls.json"


def fetch_sitemap(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
               "Accept": "application/xml, text/xml, */*;q=0.1",
               "Accept-Language": "en-US,en;q=0.9"}
    last_exc = None
    for attempt in range(1, 6):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_exc = e
            wait = 2 ** attempt
            print(f'  fetch attempt {attempt} failed, retrying in {wait}s...')
            time.sleep(wait)
    # final raise
    raise last_exc


def parse_sitemap(xml_text: str):
    root = ET.fromstring(xml_text)
    urls = []
    for url_node in root.findall('.//{*}url'):
        loc = url_node.find('{*}loc')
        if loc is not None and loc.text:
            urls.append(loc.text.strip())
    return urls


def collect_all(save_path: str = None):
    all_urls = []
    # Prefer local sitemap copies if available
    root_dir = Path(__file__).resolve().parents[1]
    local_dir = root_dir / 'sitemaps' / 'hu24'
    local_candidates = [local_dir / 'hu24_sitemap0.xml', local_dir / 'hu24_sitemap1.xml']
    if any(p.exists() for p in local_candidates):
        print('Using local sitemap files from', local_dir)
        for p in local_candidates:
            if not p.exists():
                print('  missing', p)
                continue
            print('  reading', p)
            xml = p.read_text(encoding='utf-8')
            urls = parse_sitemap(xml)
            print(f'  found {len(urls)} loc entries in {p.name}')
            all_urls.extend(urls)
    else:
        for s in SITEMAPS:
            print('Fetching sitemap', s)
            try:
                xml = fetch_sitemap(s)
            except Exception as e:
                print('  failed to fetch', s, e)
                continue
            urls = parse_sitemap(xml)
            print(f'  found {len(urls)} loc entries')
            all_urls.extend(urls)

    # dedupe, preserve order
    seen = set()
    unique = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    out = Path(save_path) if save_path else OUT_FILE
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(unique, fh, ensure_ascii=False, indent=2)

    print(f'Collected {len(unique)} unique URLs, saved to {out}')
    return unique


if __name__ == '__main__':
    collect_all()
