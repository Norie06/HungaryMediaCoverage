# Playwright Scraper - Complete Implementation

This document describes the fully-functional Playwright scraper that combines functions from both `scraper.py` and `playwright_scraper.py`.

## File: `playwright_scraper_full.py`

A complete, production-ready scraper that uses Playwright for rendering JavaScript-heavy websites.

## Key Features

### 1. **Core Functions**

#### `scrape_articles_rendered(records, delay=1.5, timeout=15000)`
- Main scraping function using Playwright
- Handles JavaScript-rendered content
- Includes error handling and retry logic
- Progress tracking (shows every 50 articles)
- Parameters:
  - `records`: List of URL records with `url` and `outlet` fields
  - `delay`: Seconds between requests (default: 1.5s)
  - `timeout`: Page load timeout in milliseconds (default: 15000ms)

#### `fetch_page_rendered(url, timeout=15000)`
- Fetches a single page and waits for network idle
- Returns rendered HTML or None on failure
- Useful for standalone page fetches

#### `parse_article(html, url, outlet)`
- Parses HTML into structured article data
- Uses outlet-specific selectors from `media_outlets.py`
- Extracts: title, date, body, tags, excerpt
- Returns dictionary with all article fields

#### `load_url_records(paths=None)`
- Loads URL records from JSON files in `filtered_urls/`
- Validates records and handles errors gracefully
- Returns list of article records

#### `save_articles(articles, output_path)`
- Saves articles to JSON or CSV
- Auto-detects format from file extension
- Creates parent directories if needed

## Usage

### Command Line

**Basic usage (scrape all URLs in filtered_urls/):**
```bash
python playwright_scraper_full.py
```

**Custom output file:**
```bash
python playwright_scraper_full.py --out-file my_articles.json
```

**Limit number of articles:**
```bash
python playwright_scraper_full.py --limit 100
```

**Custom delay between requests:**
```bash
python playwright_scraper_full.py --delay 2.0
```

**Longer timeout for slow pages:**
```bash
python playwright_scraper_full.py --timeout 30000
```

**Export to CSV:**
```bash
python playwright_scraper_full.py --out-file articles.csv
```

**All options combined:**
```bash
python playwright_scraper_full.py \
  --out-file results.json \
  --input-dir filtered_urls/ \
  --limit 50 \
  --delay 2.0 \
  --timeout 20000
```

### Programmatic Usage

```python
from playwright_scraper_full import (
    scrape_articles_rendered,
    load_url_records,
    save_articles
)
from pathlib import Path

# Load URL records
records = load_url_records([Path("filtered_urls/my_urls.json")])

# Scrape with custom settings
articles = scrape_articles_rendered(
    records,
    delay=2.0,        # Wait 2 seconds between requests
    timeout=20000     # 20 second timeout per page
)

# Save results
save_articles(articles, "my_articles.json")
```

## Output Format

### JSON Output
Each article is an object with:
```json
{
  "url": "https://example.com/article",
  "outlet": "telex",
  "outlet_type": "independent",
  "title": ["Article Title"],
  "date": ["2026-05-26"],
  "main_topic": "politika",
  "tags": ["politics", "hungary", "election"],
  "excerpt": "First 300 characters of body...",
  "body": "Full article text..."
}
```

### CSV Output
Headers: `outlet, outlet_type, date, url, title, main_topic, excerpt, body, tags`

Tags are semicolon-separated in CSV format.

## How It Works

### 1. **Loading Records**
- Reads JSON files from `filtered_urls/` directory
- Validates each record has a URL and outlet
- Logs count of records loaded

### 2. **Scraping Process**
- Launches single browser instance (reused for all pages)
- For each URL:
  - Opens new page
  - Navigates to URL
  - Waits for `networkidle` state (JS execution complete)
  - Captures rendered HTML
  - Parses article data
  - Closes page
  - Waits before next request

### 3. **Parsing**
- Uses outlet-specific CSS selectors from `media_outlets.py`
- Extracts: title, date, body text, tags
- Handles excluded elements (e.g., ads, sidebars)
- Normalizes text and removes duplicates

### 4. **Error Handling**
- Catches exceptions for individual pages
- Logs failures with reason
- Continues with next article
- Reports summary: scraped, failed, missing body

## Advantages over Basic HTTP Requests

- **JavaScript Support**: Renders JavaScript-heavy sites
- **Wait States**: Waits for content to load (networkidle)
- **Better Accuracy**: Captures rendered content, not raw HTML
- **Handles Dynamic Content**: Works with SPAs and AJAX content

## Performance Considerations

- Default delay: 1.5 seconds (adjust with `--delay`)
- Single browser instance reused across all pages
- New page per request (isolated context)
- Takes longer than HTTP scraping but more reliable

## Typical Runtime

- 1000 articles: ~25-30 minutes (with 1.5s delay)
- 100 articles: ~2.5-3 minutes

## Dependencies

- `playwright` - Browser automation
- `beautifulsoup4` - HTML parsing
- `requests` - (still used by regular scraper.py)

## Example Workflow

```python
# Script to scrape 50 articles with custom settings
from playwright_scraper_full import scrape_articles_rendered, load_url_records, save_articles
from pathlib import Path

# Load only URLs from telex
records = load_url_records([Path("filtered_urls/telex.json")])

# Scrape with longer timeout for slow pages
articles = scrape_articles_rendered(
    records[:50],           # Only first 50
    delay=2.0,             # Wait 2 seconds between requests
    timeout=25000          # 25 second timeout
)

# Save to custom location
save_articles(articles, "telex_articles.json")
```

## Troubleshooting

### Memory Issues
- Reduce batch size (use `--limit`)
- Increase `--delay` to let memory clear between pages

### Timeout Errors
- Increase `--timeout` value (in milliseconds)
- Check internet connection
- Try specific outlets individually

### Parser Errors
- Check outlet configuration in `media_outlets.py`
- Verify CSS selectors are correct
- Look for selector changes in website design

## Differences from Regular Scraper

| Feature | Regular Scraper | Playwright Scraper |
|---------|-----------------|-------------------|
| Speed | Fast | Slower (JS rendering) |
| JavaScript | ❌ No | ✅ Yes |
| Dynamic Content | ❌ No | ✅ Yes |
| Browser Memory | None | ~100MB per page |
| Selector Support | CSS | CSS (same selectors) |
| Date Range Filter | ✅ Yes | Available in code |
| Error Recovery | Good | Excellent |

## Integration with Existing Pipeline

```python
# Run both scrapers and combine results
import json

# Run regular scraper (fast, static content)
from scraper import build_pipeline
regular_articles = build_pipeline(
    input_paths=["filtered_urls/telex.json"],
    limit=1000
)

# Run Playwright scraper (slower, JS-heavy content)
from playwright_scraper_full import load_url_records, scrape_articles_rendered
pw_records = load_url_records([Path("filtered_urls/444.json")])
pw_articles = scrape_articles_rendered(pw_records, delay=1.5)

# Combine and save
all_articles = regular_articles + pw_articles
with open("all_articles.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)
```
