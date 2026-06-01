import json
import re
import sys
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

media_outlets = {
    "telex": {
        "url_pattern": "telex.hu",
        "title": "h1",
        "body": "article, .article-body, .content-body",
        "tags": [
            ".article__tags a",
            ".tags a",
            "a[href*='/cimke/']",
            "meta[name='keywords']",
            "meta[property='article:tag']",
        ],
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def find_outlet_config(url: str):
    url_lower = url.lower()
    for name, config in media_outlets.items():
        pattern = config.get("url_pattern")
        if pattern and pattern in url_lower:
            return config
    return None


def normalize_tag(value: str) -> Optional[str]:
    text = value.strip()
    if not text:
        return None
    text = re.sub(r"[\u200b\u200c\u200d]+", "", text)
    text = re.sub(r"\s+", " ", text)
    if not text:
        return None
    return text if text.startswith("#") else f"#{text}"


def extract_tags(soup: BeautifulSoup, config) -> List[str]:
    raw_tags: List[str] = []
    selectors = config.get("tags", [])
    if isinstance(selectors, str):
        selectors = [selectors]

    for selector in selectors:
        if selector.startswith("meta"):
            element = soup.select_one(selector)
            if element and element.has_attr("content"):
                for item in re.split(r",\s*", element["content"]):
                    tag = normalize_tag(item)
                    if tag:
                        raw_tags.append(tag)
            continue

        for element in soup.select(selector):
            if element.name == "meta":
                content = element.get("content", "")
                for item in re.split(r",\s*", content):
                    tag = normalize_tag(item)
                    if tag:
                        raw_tags.append(tag)
                continue

            text = element.get_text(separator=" ", strip=True)
            if not text:
                continue
            pieces = re.split(r"\s*[,/]+\s*", text)
            for piece in pieces:
                tag = normalize_tag(piece)
                if tag:
                    raw_tags.append(tag)

    if not raw_tags:
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            for item in re.split(r",\s*", meta_keywords["content"]):
                tag = normalize_tag(item)
                if tag:
                    raw_tags.append(tag)

    seen = set()
    tags = []
    for tag in raw_tags:
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def extract_title(soup: BeautifulSoup, config) -> str:
    title_selector = config.get("title", "h1")
    title_element = soup.select_one(title_selector)
    if title_element:
        return title_element.get_text(separator=" ", strip=True)
    return soup.title.get_text(separator=" ", strip=True) if soup.title else ""


def extract_body(soup: BeautifulSoup, config) -> str:
    body_selector = config.get("body", "article")
    body_element = soup.select_one(body_selector)
    if not body_element:
        return ""

    paragraphs = []
    for element in body_element.find_all(["p", "h2", "h3", "li"]):
        text = element.get_text(separator=" ", strip=True)
        if text:
            paragraphs.append(text)

    if paragraphs:
        return "\n\n".join(paragraphs)
    return body_element.get_text(separator=" ", strip=True)


def scrape_telex_url(url: str) -> dict:
    config = find_outlet_config(url)
    if config is None:
        raise ValueError("No media outlet configuration found for this URL")

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    return {
        "url": url,
        "title": extract_title(soup, config),
        "tags": extract_tags(soup, config),
        "body": extract_body(soup, config),
    }


def main(urls: List[str]):
    results = []
    for url in urls:
        try:
            results.append(scrape_telex_url(url))
        except Exception as exc:
            results.append({"url": url, "error": str(exc)})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python telex_scraper.py <telex-url> [<telex-url> ...]")
        sys.exit(1)

    main(sys.argv[1:])
