import json
import logging
from pathlib import Path
from collections import Counter

try:
    from media_outlets import MAIN_TOPICS
except ImportError:
    MAIN_TOPICS = []

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='scraper_log.txt', 
                    filemode='a')



TAGS = [
    "politics",
    "economy",
    "culture",
    "education",
    "health",
    "technology",
    "society",
]

def load_articles(input_path):
    path = Path(input_path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_relevant_article(article, tags=TAGS):
    topic = article.get("topic") or article.get("main_topic")
    if topic not in MAIN_TOPICS:
        return False

    article_tags = article.get("tags") or []
    if isinstance(article_tags, str):
        article_tags = [article_tags]

    normalized_tags = {tag.strip().lower() for tag in article_tags if isinstance(tag, str)}
    normalized_filter_tags = {tag.strip().lower() for tag in tags}

    return bool(normalized_tags & normalized_filter_tags)


def filter_articles(articles, tags=TAGS):
    return [article for article in articles if is_relevant_article(article, tags)]


def save_filtered_articles(filtered_articles, output_path):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(filtered_articles, handle, ensure_ascii=False, indent=2)


def main(input_path="articles.json", output_path="filtered_articles.json"):
    articles = load_articles(input_path)
    filtered = filter_articles(articles)
    save_filtered_articles(filtered, output_path)
    return filtered


if __name__ == "__main__":
    main()
