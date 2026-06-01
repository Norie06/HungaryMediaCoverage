import base64
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from media_outlets import RELEVANT_DATE_RANGE

BASE = 'https://444.hu'
GRAPHQL_URL = 'https://gateway.ipa.444.hu/api/graphql'
PERSISTED_HASH = 'dca0c81e9c0346f42b76a429fea0d57b95b8368e513aaa588111029eb54f5ea1'


def daterange(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def make_variables(date: datetime, after: str | None = None) -> dict:
    day_start = date.strftime('%Y-%m-%dT00:00:00.000Z')
    day_end = (date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00.000Z')
    return {
        'buckets': {'column': 'SLUG', 'operator': 'IN', 'value': ['444']},
        'categories': None,
        'tags': None,
        'partners': None,
        'authors': None,
        'date': {
            'column': 'PUBLISHED_AT',
            'operator': 'BETWEEN',
            'value': [day_start, day_end],
        },
        'types': ['ARTICLE', 'LIVE_ARTICLE'],
        'formats': None,
        'before': None,
        'after': after,
    }


def fetch_page(session: requests.Session, variables: dict, delay: float) -> dict:
    payload = {
        'operationName': 'fetchContents',
        'variables': variables,
        'extensions': {
            'persistedQuery': {
                'version': 1,
                'sha256Hash': PERSISTED_HASH,
            }
        },
    }
    for attempt in range(1, 5):
        r = session.post(GRAPHQL_URL, json=payload, timeout=20)
        if r.status_code == 429:
            backoff = 5 * attempt
            print(f'  429 rate limited, sleeping {backoff}s...')
            time.sleep(backoff)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError('Max retries exceeded')


def extract_main_topic(html: str) -> str | None:
    soup = BeautifulSoup(html, 'html.parser')
    topic = soup.select_one('div > span._1dy6oyq4k')
    if not topic:
        return None
    text = topic.get_text(strip=True)
    return text.lower() if text else None


def collect_archive_urls(save_path=None, delay=1.5):
    if save_path is None:
        save_path = Path(__file__).resolve().parents[1] / 'urls' / '444hu_urls.json'
    else:
        save_path = Path(save_path)

    start_date = datetime.fromisoformat(RELEVANT_DATE_RANGE[0])
    end_date = datetime.fromisoformat(RELEVANT_DATE_RANGE[1])

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
        'Origin': 'https://444.hu',
        'Referer': 'https://444.hu/',
    })

    seen = set()
    results = []

    for dt in daterange(start_date, end_date):
        print(f'Fetching {dt.date()}')
        after = None

        while True:
            variables = make_variables(dt, after)
            try:
                data = fetch_page(session, variables, delay)
                # TEMP DEBUG
                #import pprint
                #pprint.pprint(data)
                #break  # just inspect one page for now
            except Exception as e:
                print(f'  Error fetching {dt.date()}: {e}')
                break

            # Navigate to the connection — adjust key if needed
            data_root = data.get('data', {})
            if not data_root or not isinstance(data_root, dict):
                print(f'  Unexpected response shape: {list(data.keys())}')
                break

            connection = data_root.get('contents')
            if not connection:
                print(f'  No contents in response, keys: {list(data_root.keys())}')
                break

            edges = connection.get('edges', [])
            page_info = connection.get('pageInfo', {})

            for edge in edges:
                node = edge.get('node', {})
                url = node.get('url')
                if not url or url in seen:
                    continue
                seen.add(url)

                # Fetch topic from article page
                main_topic = None
                for attempt in range(1, 5):
                    try:
                        article_r = session.get(url, timeout=20)
                    except requests.RequestException as e:
                        print(f'  Request error on {url}: {e}')
                        break
                    if article_r.status_code == 429:
                        backoff = 5 * attempt
                        print(f'  429 on {url}, sleeping {backoff}s...')
                        time.sleep(backoff)
                        continue
                    if article_r.status_code != 200:
                        print(f'  HTTP {article_r.status_code} on {url}')
                        break
                    main_topic = extract_main_topic(article_r.text)
                    break

                results.append({'url': url, 'main_topic': main_topic})
                print(f'  + {url}  [{main_topic}]')

            print(f'  Page done: {len(edges)} articles, hasNextPage={page_info.get("hasNextPage")}')

            if not page_info.get('hasNextPage'):
                break

            after = page_info.get('endCursor')
            if not after:
                break

            time.sleep(delay)

        time.sleep(delay)

    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f'Saved {len(results)} items to {save_path}')
    return results


if __name__ == '__main__':
    urls = collect_archive_urls()
    print('Collected', len(urls), 'items')