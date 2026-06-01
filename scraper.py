"""Pipeline scraper for normalized URLs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_outlets import BODY_SELECTORS, DEFAULT_REQUEST_HEADERS, EXCLUDE_SELECTORS, MAIN_TOPICS, OUTLET_TYPE, RELEVANT_DATE_RANGE, TEXT_SELECTORS, TITLE_SELECTORS, TOPIC_TAG_SELECTORS

ROOT_DIR = Path(__file__).resolve().parent
URLS_DIR = ROOT_DIR / "filtered_urls"
DEFAULT_OUTPUT = ROOT_DIR / "test_articles.json"
DateRange = Tuple[str, str]


def parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None
    if len(text) >= 10 and text[:10].count("-") == 2:
        text = text[:10]

    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_topic(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def normalize_topic_specs(relevant_topics: Optional[Mapping[str, Iterable[str]]]) -> Dict[str, set]:
    if relevant_topics is None:
        return {outlet: set(topics) for outlet, topics in MAIN_TOPICS.items()}

    normalized: Dict[str, set] = {}
    for outlet, topics in relevant_topics.items():
        if isinstance(topics, str):
            topics = [topics]
        normalized[str(outlet).strip().lower()] = {
            normalize_topic(topic) for topic in topics if normalize_topic(topic)
        }
    return normalized


def load_url_records(paths: Optional[Sequence[Path]] = None) -> List[dict]:
    if paths is None:
        paths = sorted(URLS_DIR.glob("*.json"))

    records: List[dict] = []
    for path in paths:
        if not path.exists():
            print(f"  [WARN] File not found, skipping: {path}")
            continue
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
    return records


def filter_url_records(
    records: Iterable[Mapping[str, object]],
    date_range: Optional[DateRange] = None,
    relevant_topics: Optional[Mapping[str, Iterable[str]]] = None,
    allow_missing_topic: bool = False,
) -> List[dict]:
    start, end = date_range or RELEVANT_DATE_RANGE
    start_date = parse_date(start)
    end_date = parse_date(end)
    allowed_topics = normalize_topic_specs(relevant_topics)

    filtered: List[dict] = []
    skipped_date = 0
    skipped_topic = 0
    skipped_outlet = 0

    for record in records:
        outlet = str(record.get("outlet", "")).strip().lower()
        record_date = parse_date(record.get("date"))
        main_topic = normalize_topic(record.get("main_topic"))

        if start_date and record_date and record_date < start_date:
            skipped_date += 1
            continue
        if end_date and record_date and record_date > end_date:
            skipped_date += 1
            continue

        if main_topic is None and not allow_missing_topic:
            skipped_topic += 1
            continue

        if outlet in allowed_topics:
            if main_topic and main_topic not in allowed_topics[outlet]:
                skipped_topic += 1
                continue
        elif relevant_topics is not None:
            skipped_outlet += 1
            continue

        filtered.append(dict(record))

    print(f"  [FILTER] {len(filtered)} kept | {skipped_date} skipped by date | {skipped_topic} skipped by topic | {skipped_outlet} skipped by outlet")
    return filtered


def filter_url_records_file(input_path: str, output_path: Optional[str] = None, **kwargs) -> List[dict]:
    records = load_url_records([Path(input_path)])
    filtered = filter_url_records(records, **kwargs)
    if output_path:
        Path(output_path).write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
    return filtered


def normalize_url(href: str, base_url: str) -> Optional[str]:
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return None


def extract_links_from_listing(html: str, base_url: str, allowed_domains: Optional[List[str]] = None) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = normalize_url(anchor["href"], base_url)
        if not href:
            continue
        if allowed_domains and not any(domain in href for domain in allowed_domains):
            continue
        links.append(href.split("#", 1)[0])

    seen = set()
    unique = []
    for url in links:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def parse_sitemap_urls(xml_content: str) -> List[str]:
    soup = BeautifulSoup(xml_content, "xml")
    return [loc.text.strip() for loc in soup.find_all("loc") if loc.text.strip()]


def extract_date_from_url(url: str, date_pattern: Optional[re.Pattern] = None) -> Optional[datetime]:
    if date_pattern is None:
        date_pattern = re.compile(r"(\d{4})/(\d{2})/(\d{2})")
    match = date_pattern.search(url)
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return datetime(int(year), int(month), int(day))
    except ValueError:
        return None


def filter_urls_by_date(urls: List[str], start_date: datetime, end_date: datetime, date_pattern: Optional[re.Pattern] = None) -> List[str]:
    filtered = []
    for url in urls:
        article_date = extract_date_from_url(url, date_pattern)
        if article_date and start_date <= article_date <= end_date:
            filtered.append(url)
    return filtered


def is_article_page(html: str, article_markers: Optional[List[str]] = None) -> bool:
    if article_markers is None:
        article_markers = ["<article", "<h1", "<time", "<meta property=\"og:type\" content=\"article\""]
    html_lower = html.lower()
    return any(marker in html_lower for marker in article_markers)


def _normalize_selector(selector: object) -> List[str]:
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

    tokens = [token.strip() for token in re.split(r"\s+", text) if token.strip()]
    if tokens and all(token.startswith("#") and len(token) > 1 for token in tokens):
        return [f".{token[1:]}" for token in tokens]

    return [text]


def _collect_elements(soup: BeautifulSoup, selectors: Optional[Sequence[object]]) -> List[BeautifulSoup]:
    if not selectors:
        return []

    unique = []
    seen = set()
    for selector in _normalize_selector(selectors):
        for element in soup.select(selector):
            element_id = id(element)
            if element_id in seen:
                continue
            seen.add(element_id)
            unique.append(element)
    return unique


def _select_texts(soup: BeautifulSoup, selectors: Optional[Sequence[object]], outlet: Optional[str] = None) -> List[str]:
    texts = []
    for element in _collect_elements(soup, selectors):
        # Remove excluded sub-elements for this outlet before extracting text
        if outlet:
            for exclude_selector in EXCLUDE_SELECTORS.get(outlet, []):
                for unwanted in element.select(exclude_selector):
                    unwanted.decompose()
        text = element.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return list(dict.fromkeys(texts))


def _select_texts(soup: BeautifulSoup, selectors: Optional[Sequence[object]], outlet: Optional[str] = None) -> List[str]:
    texts = []
    for element in _collect_elements(soup, selectors):
        if outlet:
            for exclude_selector in EXCLUDE_SELECTORS.get(outlet, []):
                for unwanted in element.select(exclude_selector):
                    unwanted.decompose()
        text = element.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return list(dict.fromkeys(texts))


def parse_article(html: str, url: str, outlet: str) -> Dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")

    title_selectors = TITLE_SELECTORS.get(outlet) or ["h1"]
    text_selectors = TEXT_SELECTORS.get(outlet) or BODY_SELECTORS.get(outlet) or ["p"]
    body_selectors = text_selectors or BODY_SELECTORS.get(outlet) or ["p"]
    tag_selectors = TOPIC_TAG_SELECTORS.get(outlet) or []

    title = _select_texts(soup, title_selectors)
    date = _select_texts(soup, ["time[datetime]", "time"])

    body_texts = body_texts = _select_texts(soup, body_selectors, outlet=outlet)
    if body_texts:
        body_text = "\n\n".join(body_texts)
    else:
        paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
        body_text = "\n\n".join([paragraph for paragraph in paragraphs if paragraph])

    tags = tags = _select_texts(soup, tag_selectors, outlet=outlet)
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


def fetch_page(url: str, session: requests.Session, timeout: int = 15) -> Optional[str]:
    for attempt in range(3):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if attempt == 2:
                print(f"    [FAIL] {url} — {type(e).__name__}: {e}")
                return None
            time.sleep(0.5 * (2 ** attempt))

    return None


def build_session(headers: Optional[Mapping[str, str]] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_REQUEST_HEADERS)
    if headers:
        session.headers.update(headers)
    return session


def scrape_articles(
    records: Iterable[Mapping[str, object]],
    delay: float = 1.0,
    timeout: int = 15,
    headers: Optional[Mapping[str, str]] = None,
) -> List[dict]:
    session = build_session(headers)
    articles: List[dict] = []
    records = list(records)
    total = len(records)
    failed = 0
    no_body = 0

    print(f"\n[SCRAPE] Starting — {total} articles to fetch\n")

    for i, record in enumerate(records, 1):
        url = str(record.get("url", "")).strip()
        outlet = str(record.get("outlet", "")).strip().lower()
        if not url:
            continue

        if i % 50 == 0 or i == 1:
            elapsed_per = ""
            print(f"  [{i}/{total}] outlet={outlet}  url={url[:80]}")

        html = fetch_page(url, session, timeout=timeout)
        if not html:
            failed += 1
            continue

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

        articles.append(article)
        time.sleep(delay)

    print(f"\n[SCRAPE] Done — {len(articles)} scraped | {failed} failed | {no_body} missing body")
    return articles


def save_articles(articles: List[dict], output_path: str):
    path = Path(output_path)
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


def build_pipeline(
    input_paths: Optional[Sequence[str]] = None,
    date_range: Optional[DateRange] = None,
    relevant_topics: Optional[Mapping[str, Iterable[str]]] = None,
    allow_missing_topic: bool = False,
    delay: float = 1.0,
    timeout: int = 15,
    headers: Optional[Mapping[str, str]] = None,
) -> List[dict]:
    records = load_url_records([Path(path) for path in input_paths] if input_paths else None)
    filtered = filter_url_records(
        records,
        date_range=date_range,
        relevant_topics=relevant_topics,
        allow_missing_topic=allow_missing_topic,
    )
    return scrape_articles(filtered, delay=delay, timeout=timeout, headers=headers)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape article bodies from filtered URL JSON files.")
    parser.add_argument("--out-file", default=str(DEFAULT_OUTPUT), help="Output path (.json or .csv).")
    parser.add_argument("--input-dir", default=str(URLS_DIR), help="Directory containing filtered URL JSON files.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on the number of articles to scrape.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"[START] Loading records from {args.input_dir}")

    records = load_url_records(sorted(Path(args.input_dir).glob("*.json")))

    if args.limit and args.limit > 0:
        records = records[:args.limit]
        print(f"  [LIMIT] Capped at {args.limit} records")

    articles = scrape_articles(records, delay=args.delay, timeout=args.timeout)
    save_articles(articles, args.out_file)
    print(f"\n[DONE] {len(articles)} articles saved to {args.out_file}")


if __name__ == "__main__":
    main()