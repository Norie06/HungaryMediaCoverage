import json
from pathlib import Path

data = json.loads(Path("mn_articles.json").read_text(encoding="utf-8"))

for article in data[:20]:  # spot check 20 random articles
    print("---")
    print(article.get("title"))
    print(article.get("tags"))
    print(article.get("body", "")[:300])
    print()