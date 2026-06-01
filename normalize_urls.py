import json
import re
from pathlib import Path
from urllib.parse import urlparse

from media_outlets import OUTLET_SETTINGS

ROOT = Path(__file__).resolve().parent
URLS_DIR = ROOT / "urls"


def normalize_outlet_name(filename: str) -> str:
    stem = Path(filename).stem
    if stem.endswith("_urls"):
        stem = stem[: -len("_urls")]
    if stem.endswith("_sitemap"):
        stem = stem[: -len("_sitemap")]
    if stem == "444hu":
        return "444"
    if stem == "24hu":
        return "24hu"
    return stem


def normalize_date(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return None
    value = str(value).strip()
    if not value:
        return None
    if len(value) >= 10 and value[:10].count("-") == 2:
        candidate = value[:10]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
            return candidate
    match = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def extract_date_from_url(url: str):
    parsed = urlparse(url)
    path = parsed.path
    match = re.search(r"(\d{4})/(\d{2})/(\d{2})", path)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def infer_main_topic(outlet: str, url: str):
    known_topics = set(OUTLET_SETTINGS.get(outlet, {}).get("main_topics", []))
    parsed = urlparse(url)
    path_segments = [seg for seg in parsed.path.split("/") if seg]

    for segment in path_segments:
        if segment in known_topics:
            return segment.lower()

    generic_prefixes = {"g7", "english", "after", "transtelex", "pr-cikk", "karakter", "eletmod", "techtud", "szepkilatas"}
    if len(path_segments) >= 2 and path_segments[0].lower() in generic_prefixes:
        fallback = path_segments[1].lower()
        if fallback:
            return fallback

    for segment in path_segments:
        if segment.lower() not in {"app", "uploads", "rss", "sitemap", "news", "archivum"}:
            return segment.lower()

    return None


def normalize_entry(outlet: str, entry) -> dict:
    if isinstance(entry, str):
        url = entry
        date = extract_date_from_url(url)
        main_topic = infer_main_topic(outlet, url)
        return {
            "outlet": outlet,
            "date": date,
            "main_topic": main_topic,
            "url": url,
        }

    if not isinstance(entry, dict):
        raise TypeError(f"Unsupported entry type: {type(entry).__name__}")

    url = entry.get("url") or entry.get("loc")
    if not url:
        raise ValueError("Entry is missing url/loc")

    date = normalize_date(entry.get("lastmod")) or extract_date_from_url(url)
    main_topic = entry.get("main_topic")
    if not main_topic:
        main_topic = infer_main_topic(outlet, url)
    else:
        main_topic = str(main_topic).strip().lower()

    return {
        "outlet": outlet,
        "date": date,
        "main_topic": main_topic,
        "url": url,
    }


def normalize_file(filename: str):
    outlet = normalize_outlet_name(filename)
    path = URLS_DIR / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    normalized = [normalize_entry(outlet, entry) for entry in raw]
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    for filename in sorted(URLS_DIR.iterdir()):
        if filename.name.endswith(".json"):
            normalize_file(filename.name)


if __name__ == "__main__":
    main()
