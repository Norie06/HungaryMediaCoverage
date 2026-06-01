import json
from pathlib import Path
from collections import Counter

all_tags = Counter()

for file in Path("articles").glob("articles.json"):
    data = json.loads(file.read_text(encoding="utf-8"))
    for article in data:
        tags = article.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(";")]
        for tag in tags:
            if tag:
                all_tags[tag.lower()] += 1

# Print top 100 tags across all outlets
for tag, count in all_tags.most_common(200):
    print(f"{count:>5}  {tag}")