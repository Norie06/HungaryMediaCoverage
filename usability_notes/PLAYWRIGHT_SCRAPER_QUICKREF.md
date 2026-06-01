# Playwright Scraper - Quick Reference

## File: `playwright_scraper_full.py`

A complete, production-ready Playwright-based web scraper for JavaScript-heavy websites.

## Quick Start

### 1. Run from Command Line

```bash
# Scrape all URLs in filtered_urls/
python playwright_scraper_full.py

# Scrape with custom output file
python playwright_scraper_full.py --out-file results.json

# Scrape first 100 articles
python playwright_scraper_full.py --limit 100

# Scrape with 2 second delay between requests
python playwright_scraper_full.py --delay 2.0

# Increase timeout for slow pages
python playwright_scraper_full.py --timeout 30000

# Export to CSV
python playwright_scraper_full.py --out-file articles.csv
```

### 2. Use in Python Code

```python
from playwright_scraper_full import scrape_articles_rendered, load_url_records, save_articles

# Load URL records
records = load_url_records()

# Scrape articles
articles = scrape_articles_rendered(records, delay=1.5, timeout=15000)

# Save to file
save_articles(articles, "articles.json")
```

## Main Functions

### `scrape_articles_rendered(records, delay=1.5, timeout=15000)`
Scrapes articles using Playwright browser automation.
- **records**: List of URL records with `url` and `outlet` fields
- **delay**: Seconds to wait between requests (default: 1.5)
- **timeout**: Page load timeout in milliseconds (default: 15000)
- **Returns**: List of article dictionaries

### `load_url_records(paths=None)`
Loads URL records from JSON files.
- **paths**: Optional list of file paths (default: all files in filtered_urls/)
- **Returns**: List of URL records

### `save_articles(articles, output_path)`
Saves articles to JSON or CSV.
- **articles**: List of article dictionaries
- **output_path**: Output file path (.json or .csv)
- Auto-detects format from file extension

### `fetch_page_rendered(url, timeout=15000)`
Fetches and renders a single page.
- **url**: URL to fetch
- **timeout**: Page load timeout in milliseconds
- **Returns**: Rendered HTML or None on error

### `parse_article(html, url, outlet)`
Parses HTML into article data using outlet-specific selectors.
- **html**: HTML content to parse
- **url**: Article URL
- **outlet**: Outlet name (e.g., "telex", "444")
- **Returns**: Dictionary with article data

## Command Line Options

```
--out-file FILE        Output path (.json or .csv) [default: playwright_articles.json]
--input-dir DIR        Input directory with URL files [default: filtered_urls/]
--limit N              Max number of articles to scrape (0 = unlimited) [default: 0]
--delay SECONDS        Delay between requests [default: 1.5]
--timeout MILLISECONDS Page load timeout [default: 15000]
```

## Output Format

Each article object contains:
- `url`: Article URL
- `outlet`: Media outlet name
- `outlet_type`: Outlet type (independent, kesma)
- `title`: Article title (list)
- `date`: Publication date (list)
- `main_topic`: Main topic/category
- `tags`: Article tags (list)
- `excerpt`: Short text preview
- `body`: Full article text

## Key Advantages

✅ **JavaScript Rendering** - Handles dynamic content  
✅ **Reliable** - Waits for networkidle state  
✅ **Configurable** - Adjustable delays and timeouts  
✅ **Progress Tracking** - Shows scraping status  
✅ **Error Handling** - Continues on failures  
✅ **Flexible Output** - JSON or CSV format  

## Performance

- Typical speed: ~20-30 articles per minute with 1.5s delay
- 1000 articles takes ~25-35 minutes
- Adjustable with `--delay` and `--timeout` options

## Common Use Cases

**Scrape first 50 articles:**
```bash
python playwright_scraper_full.py --limit 50
```

**Slow internet (increase delay and timeout):**
```bash
python playwright_scraper_full.py --delay 3.0 --timeout 30000
```

**Fast internet (decrease delay):**
```bash
python playwright_scraper_full.py --delay 0.5
```

**Export to CSV for Excel:**
```bash
python playwright_scraper_full.py --out-file articles.csv
```

**Scrape specific outlet:**
```python
from pathlib import Path
from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles

records = load_url_records([Path("filtered_urls/telex.json")])
articles = scrape_articles_rendered(records)
save_articles(articles, "telex_only.json")
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Timeout errors | Increase `--timeout` value |
| Too slow | Decrease `--delay` value |
| Memory errors | Use `--limit` to scrape in batches |
| Missing content | Check outlet selectors in `media_outlets.py` |
| URL not found | Verify files in `filtered_urls/` directory |

## Files Included

- `playwright_scraper_full.py` - Main scraper implementation
- `playwright_scraper_examples.py` - 10 example usage patterns
- `PLAYWRIGHT_SCRAPER_README.md` - Detailed documentation
- `PLAYWRIGHT_SCRAPER_QUICKREF.md` - This file

## Next Steps

1. Test with `python playwright_scraper_full.py --limit 10`
2. Adjust `--delay` and `--timeout` based on results
3. Scale up with larger `--limit` values
4. Integrate with pipeline for full workflow

For detailed documentation, see `PLAYWRIGHT_SCRAPER_README.md`  
For code examples, see `playwright_scraper_examples.py`
