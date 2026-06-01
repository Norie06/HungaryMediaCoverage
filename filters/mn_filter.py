#!/usr/bin/env python3
"""Print URLs and the number of "\n\n" occurrences in article bodies.

Default source file is `mn_articles.json` in the same directory, but a
custom path can be provided with --source or MN_SOURCE env var.
"""
import argparse
import json
import os
import sys


def count_double_newlines(text: str) -> int:
    if not isinstance(text, str):
        return 0
    return text.count("\n\n")


def process(path: str, output_path: str = None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Source file not found: {path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in source file: {e}", file=sys.stderr)
        return 3

    # Expecting a list of article objects
    if not isinstance(data, list):
        print("Expected a JSON array of articles", file=sys.stderr)
        return 4

    # Determine output file path
    if output_path is None:
        output_path = "mn_filter_results_2.txt"

    try:
        with open(output_path, "w", encoding="utf-8") as output_file:
            for item in data:
                url = item.get("url") if isinstance(item, dict) else None
                body = item.get("body") if isinstance(item, dict) else None
                count = count_double_newlines(body)
                output_file.write(f"{url}\t{count}\n")
        
        print(f"Results written to {output_path}")
    except IOError as e:
        print(f"Error writing to output file: {e}", file=sys.stderr)
        return 5

    return 0


def main():
    default = os.environ.get("MN_SOURCE", "..\\articles\\mn_articles.json")
    parser = argparse.ArgumentParser(description="Output URL and number of '\\n\\n' in article bodies to a text file")
    parser.add_argument("--source", "-s", default=default, help="Path to JSON source file (default from MN_SOURCE or mn_articles.json)")
    parser.add_argument("--output", "-o", default="mn_filter_results_2.txt", help="Output text file path (default: mn_filter_results_2.txt)")
    args = parser.parse_args()
    sys.exit(process(args.source, args.output) or 0)
