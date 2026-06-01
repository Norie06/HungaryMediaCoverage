import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def is_body_valid_heuristic(body: str) -> bool:
    if not body or len(body) < 300:
        return False
    words = body.split()
    if len(words) < 80:
        return False
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.3:
        return False
    return True

def is_body_coherent(tags: list, body: str, threshold: float = 0.3) -> bool:
    if not tags or not body:
        return False
    tag_text = " ".join(tags)
    embeddings = model.encode([tag_text, body[:512]], convert_to_tensor=True)
    score = util.cos_sim(embeddings[0], embeddings[1]).item()
    return score >= threshold

def filter_articles(articles: list, sim_threshold: float = 0.3) -> tuple[list, list]:
    good, bad = [], []
    for article in articles:
        body = article.get("body", "")
        tags = article.get("tags") or []

        # Stage 1 — heuristics
        if not is_body_valid_heuristic(body):
            bad.append({**article, "_filter_reason": "heuristic"})
            continue

        # Stage 2 — semantic similarity
        if not is_body_coherent(tags, body, threshold=sim_threshold):
            bad.append({**article, "_filter_reason": "semantic"})
            continue

        good.append(article)
    return good, bad

data = json.loads(Path("mn_articles.json").read_text(encoding="utf-8"))
good, bad = filter_articles(data)

print(f"Good: {len(good)} | Bad: {len(bad)} | Total: {len(data)}")

# Save both so you can inspect the bad ones
Path("mn_articles_clean.json").write_text(
    json.dumps(good, ensure_ascii=False, indent=2), encoding="utf-8"
)
Path("mn_articles_rejected.json").write_text(
    json.dumps(bad, ensure_ascii=False, indent=2), encoding="utf-8"
)