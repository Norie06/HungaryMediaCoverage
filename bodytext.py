"""Backward-compatible wrapper around the integrated scraper pipeline."""

from pathlib import Path

from scraper import build_pipeline, save_articles


def main() -> None:
    articles = build_pipeline()
    output_path = Path(__file__).resolve().parent / "hungarian_articles.csv"
    save_articles(articles, str(output_path))
    print(f"Collected {len(articles)} articles")


if __name__ == "__main__":
    main()
