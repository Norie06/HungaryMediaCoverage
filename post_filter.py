import json
import os
from pathlib import Path
from urllib.parse import urlparse

from media_outlets import MAIN_TOPICS

# --- CONFIGURE YOUR FILTERS HERE ---
filters = {
    'date': ('2026-02-21', '2026-04-14'),  # inclusive, set to None to skip
    'outlet_type': None,                    # e.g. 'kesma', 'independent', or None to skip
    'outlet': None,                         # e.g. 'telex', or None to skip
}

input_folder = './articles/by_outlet'

# --- FILTER FUNCTION ---
def _infer_main_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url)
        parts = [p for p in p.path.split('/') if p]
        return parts[0].lower() if parts else ""
    except Exception:
        return ""


def passes_filter(article, filters, outlet_hint: str = ""):
    if filters['date']:
        start, end = filters['date']
        date = article.get('date', '') or ''
        if not (start <= date[:10] <= end):
            return False
    if filters['outlet_type']:
        if article.get('outlet_type') != filters['outlet_type']:
            return False
    if filters['outlet']:
        if article.get('outlet') != filters['outlet']:
            return False

    # Enforce that `main_topic` matches the configured main topics for the outlet
    outlet_name = (article.get('outlet') or outlet_hint or '').strip().lower()
    allowed = MAIN_TOPICS.get(outlet_name) or []
    if allowed:
        allowed_norm = {t.strip().lower() for t in allowed}
        main_topic = (article.get('main_topic') or "").strip().lower()
        if not main_topic:
            # try to infer from URL path (e.g. /kulfold/..., /belfold/...)
            main_topic = _infer_main_from_url(article.get('url', '')).strip().lower()

        if not main_topic or main_topic not in allowed_norm:
            return False

    return True

# --- PROCESS EACH JSON ---
for filename in os.listdir(input_folder):
    if not filename.endswith('.json') or '_filtered' in filename:
        continue

    filepath = os.path.join(input_folder, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # handle both structures
    if isinstance(data, dict):
        outlet_name = data.get('outlet', '')
        articles = data.get('articles', []) if isinstance(data.get('articles', []), list) else []
        is_dict = True
        original_top_level = dict(data)
    elif isinstance(data, list):
        articles = data if isinstance(data, list) else []
        outlet_name = articles[0].get('outlet', '') if articles else ''
        is_dict = False
        original_top_level = None

    original_count = len(articles)
    # pass outlet_name as hint to allow validation when article lacks `outlet`
    filtered_articles = [a for a in articles if passes_filter(a, filters, outlet_hint=outlet_name)]
    filtered_count = len(filtered_articles)

    if filtered_count != original_count:
        if is_dict:
            # preserve other top-level keys, but replace 'articles'
            out_data = dict(original_top_level or {})
            out_data['articles'] = filtered_articles
        else:
            out_data = filtered_articles

        base = filename.replace('.json', '')
        out_filename = f"{base}_filtered.json"
        out_filepath = os.path.join(input_folder, out_filename)

        with open(out_filepath, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)

        print(f"{filename}: {original_count} -> {filtered_count} articles saved to {out_filename}")
    else:
        print(f"{filename}: no changes, skipping")