import argparse
import json
from datetime import datetime
from pathlib import Path

from media_outlets import RELEVANT_DATE_RANGE, MAIN_TOPICS


# --- Core filter logic ---

def is_relevant(article: dict) -> bool:
    """
    Check if an article passes both:
    - date range filter
    - topic filter (based on outlet)
    """
    # --- Date filtering ---
    start_str, end_str = RELEVANT_DATE_RANGE
    start = datetime.fromisoformat(start_str)
    end = datetime.fromisoformat(end_str)

    try:
        article_date = datetime.fromisoformat(article["date"])
    except Exception:
        return False

    if not (start <= article_date <= end):
        return False

    # --- Topic filtering ---
    outlet = article.get("outlet")
    topic = article.get("main_topic")

    if not outlet or not topic:
        return False

    allowed_topics = MAIN_TOPICS.get(outlet, [])

    return topic in allowed_topics


# --- File processing ---

def filter_file(input_path: Path, output_path: Path):
    """
    Load a JSON file, filter articles, save result.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered = [article for article in data if is_relevant(article)]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"{input_path.name}: {len(filtered)} / {len(data)} kept")


def filter_all(input_dir: Path, output_dir: Path, outlet: str = None, file: str = None):
    """
    Process *_urls.json files in input_dir.
    Optionally restrict to a single outlet name or a specific filename.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if file:
        # Single file explicitly specified
        input_path = Path(file)
        if not input_path.is_absolute():
            input_path = input_dir / input_path
        if not input_path.exists():
            print(f"[ERROR] File not found: {input_path}")
            return
        filter_file(input_path, output_dir / input_path.name)
        return

    for input_path in sorted(input_dir.glob("*_urls.json")):
        # If --outlet is given, skip files that don't match <outlet>_urls.json
        if outlet and input_path.name != f"{outlet}_urls.json":
            continue
        filter_file(input_path, output_dir / input_path.name)


# --- CLI entry point ---

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter scraped URL JSON files by date range and topic."
    )
    parser.add_argument("input_dir", help="Directory containing *_urls.json files.")
    parser.add_argument("output_dir", help="Directory to write filtered output files.")
    parser.add_argument(
        "--outlet",
        default=None,
        help="Only process this outlet (e.g. --outlet magyarnemzet). "
             "Expects a file named <outlet>_urls.json in input_dir.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Process a single specific file instead of scanning input_dir "
             "(e.g. --file magyarnemzet_urls.json). Path relative to input_dir "
             "or absolute.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    filter_all(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        outlet=args.outlet,
        file=args.file,
    )