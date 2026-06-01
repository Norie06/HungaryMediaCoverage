"""Example usage scripts for the Playwright scraper."""

# ============================================================================
# Example 1: Basic Usage - Scrape all URLs in filtered_urls/
# ============================================================================

def example_basic():
    """Scrape all URLs using default settings."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    
    records = load_url_records()  # Auto-loads from filtered_urls/
    articles = scrape_articles_rendered(records)
    save_articles(articles, "playwright_articles.json")


# ============================================================================
# Example 2: Scrape with Custom Settings
# ============================================================================

def example_custom_settings():
    """Scrape with custom delay, timeout, and limit."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from pathlib import Path
    
    records = load_url_records()
    
    # Limit to first 50 articles, with 2 second delay
    articles = scrape_articles_rendered(
        records[:50],
        delay=2.0,           # 2 seconds between requests
        timeout=20000        # 20 second page load timeout
    )
    
    save_articles(articles, "first_50_articles.json")
    print(f"Scraped {len(articles)} articles")


# ============================================================================
# Example 3: Scrape Specific Outlet Only
# ============================================================================

def example_specific_outlet():
    """Scrape articles from a specific outlet."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from pathlib import Path
    
    # Load only telex articles
    records = load_url_records([Path("filtered_urls/telex.json")])
    
    articles = scrape_articles_rendered(records, delay=1.5)
    save_articles(articles, "telex_articles.json")


# ============================================================================
# Example 4: Fetch and Parse Single Page
# ============================================================================

def example_single_page():
    """Fetch and parse a single article."""
    from playwright_scraper_full import fetch_page_rendered, parse_article
    
    url = "https://telex.hu/belfold/2026/04/11/example-article"
    html = fetch_page_rendered(url, timeout=20000)
    
    if html:
        article = parse_article(html, url, "telex")
        print(f"Title: {article['title']}")
        print(f"Tags: {article['tags']}")
        print(f"Body length: {len(article['body']) if article['body'] else 0} chars")


# ============================================================================
# Example 5: Combine Multiple Outlets
# ============================================================================

def example_multiple_outlets():
    """Scrape multiple outlets and combine results."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from pathlib import Path
    
    all_articles = []
    outlets = ["telex", "444", "24hu"]
    
    for outlet in outlets:
        print(f"\n=== Scraping {outlet} ===")
        path = Path(f"filtered_urls/{outlet}.json")
        if path.exists():
            records = load_url_records([path])
            articles = scrape_articles_rendered(records, delay=1.5)
            all_articles.extend(articles)
            print(f"Scraped {len(articles)} from {outlet}")
    
    save_articles(all_articles, "all_outlets_combined.json")
    print(f"\nTotal: {len(all_articles)} articles")


# ============================================================================
# Example 6: Export to CSV
# ============================================================================

def example_export_csv():
    """Scrape and export to CSV format."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    
    records = load_url_records()
    articles = scrape_articles_rendered(records)
    
    # Automatically detects CSV format from .csv extension
    save_articles(articles, "articles.csv")


# ============================================================================
# Example 7: Scrape with Progress Monitoring
# ============================================================================

def example_with_monitoring():
    """Scrape with custom progress tracking."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    import json
    
    records = load_url_records()
    
    # Scrape articles
    articles = scrape_articles_rendered(
        records[:100],
        delay=1.5,
        timeout=15000
    )
    
    # Show statistics
    outlets = {}
    for article in articles:
        outlet = article.get("outlet", "unknown")
        outlets[outlet] = outlets.get(outlet, 0) + 1
    
    print("\nArticles by outlet:")
    for outlet, count in sorted(outlets.items()):
        print(f"  {outlet}: {count}")
    
    save_articles(articles, "articles_with_stats.json")


# ============================================================================
# Example 8: Error Recovery - Retry Failed URLs
# ============================================================================

def example_retry_failed():
    """Retry failed URLs with different settings."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from pathlib import Path
    import json
    
    records = load_url_records()
    
    # First attempt with default settings
    print("First attempt with default settings...")
    articles = scrape_articles_rendered(records, delay=1.5, timeout=15000)
    
    # Log failed URLs for retry
    failed_urls = []  # Would be populated by modifications to scraper
    
    if failed_urls:
        print(f"\nRetrying {len(failed_urls)} failed URLs with longer timeout...")
        retry_records = [r for r in records if r.get("url") in failed_urls]
        retry_articles = scrape_articles_rendered(retry_records, delay=3.0, timeout=30000)
        articles.extend(retry_articles)
    
    save_articles(articles, "articles_with_retries.json")


# ============================================================================
# Example 9: Batch Processing
# ============================================================================

def example_batch_processing():
    """Process articles in batches."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from pathlib import Path
    import json
    
    records = load_url_records()
    batch_size = 100
    total_batches = (len(records) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = min((batch_num + 1) * batch_size, len(records))
        batch_records = records[start:end]
        
        print(f"\nProcessing batch {batch_num + 1}/{total_batches} ({len(batch_records)} articles)")
        
        articles = scrape_articles_rendered(batch_records, delay=1.5)
        output_file = f"articles_batch_{batch_num + 1:03d}.json"
        save_articles(articles, output_file)


# ============================================================================
# Example 10: Integration with Regular Scraper
# ============================================================================

def example_combined_scrapers():
    """Use both regular HTTP scraper and Playwright for different outlets."""
    from playwright_scraper_full import load_url_records, scrape_articles_rendered, save_articles
    from scraper import scrape_articles as http_scrape
    from pathlib import Path
    import json
    
    # Fast outlets with static HTML - use regular scraper
    print("Scraping static outlets with HTTP...")
    static_records = load_url_records([Path("filtered_urls/telex.json")])
    static_articles = http_scrape(static_records, delay=1.0)
    
    # JavaScript-heavy outlets - use Playwright
    print("\nScraping dynamic outlets with Playwright...")
    dynamic_records = load_url_records([Path("filtered_urls/444.json")])
    dynamic_articles = scrape_articles_rendered(dynamic_records, delay=1.5)
    
    # Combine and save
    all_articles = static_articles + dynamic_articles
    save_articles(all_articles, "combined_scraped_articles.json")
    
    print(f"\nTotal: {len(all_articles)} articles")
    print(f"  - HTTP: {len(static_articles)}")
    print(f"  - Playwright: {len(dynamic_articles)}")


# ============================================================================
# Run examples (uncomment to execute)
# ============================================================================

if __name__ == "__main__":
    print("Available examples:")
    print("  1. example_basic()")
    print("  2. example_custom_settings()")
    print("  3. example_specific_outlet()")
    print("  4. example_single_page()")
    print("  5. example_multiple_outlets()")
    print("  6. example_export_csv()")
    print("  7. example_with_monitoring()")
    print("  8. example_retry_failed()")
    print("  9. example_batch_processing()")
    print("  10. example_combined_scrapers()")
    print("\nTo run: from playwright_scraper_examples import example_basic; example_basic()")
