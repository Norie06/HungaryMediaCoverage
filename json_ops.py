"""
Utility for combining and subtracting JSON article files.

Usage examples:
  # Combine multiple files into one
  python json_ops.py combine -i telex.json 444.json 24hu.json -o all_articles.json

  # Subtract one file from another (remove articles that appear in the second file)
  python json_ops.py subtract -i all_articles.json -s bad_articles.json -o clean_articles.json

  # Combine then subtract in one step
  python json_ops.py combine -i telex.json 444.json -o combined.json
  python json_ops.py subtract -i combined.json -s duplicates.json -o final.json
"""

import argparse
import json
from pathlib import Path


def load(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} does not contain a JSON array at the top level.")
    print(f"  [LOAD] {Path(path).name}: {len(data)} articles")
    return data


def save(articles: list[dict], path: str):
    Path(path).write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  [SAVE] {len(articles)} articles → {path}")


def combine(input_paths: list[str], output_path: str, dedupe: bool = True):
    """
    Combine multiple JSON article files into one.
    Deduplicates by URL by default.
    """
    combined = []
    seen_urls = set()

    for path in input_paths:
        articles = load(path)
        for article in articles:
            url = article.get("url")
            if dedupe and url in seen_urls:
                continue
            seen_urls.add(url)
            combined.append(article)

    print(f"\n  [COMBINE] {len(combined)} articles total (dedupe={dedupe})")
    save(combined, output_path)


def subtract(input_path: str, subtract_path: str, output_path: str):
    """
    Remove articles from input that appear in the subtract file.
    Matching is done by URL.
    """
    articles = load(input_path)
    to_remove = load(subtract_path)

    remove_urls = {a.get("url") for a in to_remove}
    kept = [a for a in articles if a.get("url") not in remove_urls]
    removed_count = len(articles) - len(kept)

    print(f"\n  [SUBTRACT] Removed {removed_count} | Kept {len(kept)}")
    save(kept, output_path)


def summary(input_paths: list[str]):
    """
    Print a summary of article counts per outlet for each file.
    """
    from collections import Counter
    for path in input_paths:
        articles = load(path)
        counts = Counter(a.get("outlet", "unknown") for a in articles)
        print(f"\n  {Path(path).name} — {len(articles)} total")
        for outlet, count in sorted(counts.items()):
            print(f"    {outlet}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine or subtract JSON article files.")
    sub = parser.add_subparsers(dest="command", required=True)

    # combine
    p_combine = sub.add_parser("combine", help="Merge multiple JSON files into one.")
    p_combine.add_argument("-i", "--input", nargs="+", required=True, help="Input JSON files.")
    p_combine.add_argument("-o", "--output", required=True, help="Output JSON file.")
    p_combine.add_argument("--no-dedupe", action="store_true", help="Skip URL deduplication.")

    # subtract
    p_subtract = sub.add_parser("subtract", help="Remove articles from input that appear in subtract file.")
    p_subtract.add_argument("-i", "--input", required=True, help="Base JSON file.")
    p_subtract.add_argument("-s", "--subtract", required=True, help="JSON file with articles to remove.")
    p_subtract.add_argument("-o", "--output", required=True, help="Output JSON file.")

    # summary
    p_summary = sub.add_parser("summary", help="Print article counts per outlet.")
    p_summary.add_argument("-i", "--input", nargs="+", required=True, help="Input JSON files.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "combine":
        combine(args.input, args.output, dedupe=not args.no_dedupe)
    elif args.command == "subtract":
        subtract(args.input, args.subtract, args.output)
    elif args.command == "summary":
        summary(args.input)