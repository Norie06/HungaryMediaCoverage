"""Shared media outlet configuration for scraping.

This module centralizes outlet-specific selectors, base URLs, sitemaps,
RSS feeds, topic metadata, and other scraping-related constants.
"""

RELEVANT_DATE_RANGE = ("2026-02-21", "2026-04-11")

OUTLET_SETTINGS = {
    "telex": {
        "name": "Telex",
        "base_url": "https://telex.hu",
        "body_selector": "div.article-html-content",
        "outlet_type": "independent",
        "rss_feed": "https://telex.hu/rss",
        "sitemap_url_template": "https://telex.hu/sitemap/{year}/{month}/{day}/news.xml",
        "sitemap_url": "https://telex.hu/sitemap/news.xml",
        "main_topics": [
            "belfold",
            "kulfold",
            "gazdasag",
            "direkt36",
            "ellenorzo",
            "komplex",
            "nevertek",
        ],
        "topic_tag_selectors": "a.tag--meta",
        "text_selector": "div.article-html-content",
        "title_selector": "div.title-section__top h1",
    },
    "444": {
        "name": "444",
        "base_url": "https://444.hu",
        "body_selector": "div.entry-content",
        "outlet_type": "independent",
        "rss_feed": "https://444.hu/feed",
        "archive_url": "https://444.hu/archivum",
        "sitemap_url": "https://444.hu/sitemap-news.xml",
        "main_topic_selector": "div > span._1dy6oyq4k",
        "main_topics": [
            "baleset",
            "belfold",
            "budapest",
            "kulfold",
            "politika",
            "valasztas",
            "gazdasag",
            "egeszsegugy",
            "oktatas",
            "energia",
            "kozlekedes",
            "media",
            "europa",
            "eu",
            "haboru",
            "hadsereg",
            "bunugy",
            "drog",
            "nok elleni eroszak",
        ],
        "topic_tag_selectors": "a._189c837e",
        "text_selector": "div.fkng932",
        "title_selector": "div._1j8zfzf3 > h1 > span > span._1dy6oyq5g",
    },
    "24hu": {
        "name": "24hu",
        "base_url": "https://24.hu",
        "body_selector": "div.article-content",
        "outlet_type": "independent",
        "sitemap_url_template": "https://24.hu/app/uploads/sitemap/24.hu_sitemap_{index}.xml",
        "main_topics": [
            "belfold",
            "kulfold",
            "gazdasag",
            "kozelet",
        ],
        "topic_tag_selectors": "div.m-tag__wrap a",
        "text_selector": ["div.o-post__body", "div.o-post__lead", "h2.m-livePost__postTitle"],
        "title_selector": "h1.o-post__title",
    },
    "origo": {
        "name": "Origo",
        "base_url": "https://origo.hu",
        "body_selector": "div.article-content",
        "outlet_type": "kesma",
        "sitemap_url_template": "https://www.origo.hu/{year}{month}_sitemap.xml",
        "main_topics": [
            "belpol",
            "kulpol",
            "nagyvilag",
            "itthon",
            "gazdasag",
        ],
        "topic_tag_selectors": "div.article-tags a.tag",
        "text_selector": "origo-wysiwyg-box p",
        "title_selector": "h1.article-title",
    },
    "magyarnemzet": {
        "name": "Magyar Nemzet",
        "base_url": "https://magyarnemzet.hu",
        "body_selector": "div.article-content",
        "outlet_type": "kesma",
        "sitemap_url_template": "https://magyarnemzet.hu/{year}{month}_sitemap.xml",
        "main_topics": [
            "belfold",
            "kulfold",
            "gazdasag",
        ],
        "topic_tag_selectors": "mno-tag-list a, div.opinion-info-block a.opinion-label",
        "text_selector": ["app-article-text.is-first"],
        "title_selector": ["h1.article-title", "h1"],
    },
    "mandiner": {
        "name": "Mandiner",
        "base_url": "https://mandiner.hu",
        "body_selector": "div.article-body",
        "outlet_type": "kesma",
        "sitemap_index_url": "https://mandiner.hu/sitemapindex.xml",
        "sitemap_url_template": "https://mandiner.hu/{year}{month}_sitemap.xml",
        "main_topics": [
            "belfold",
            "kulfold",
            "gazdasag",
        ],
        "topic_tag_selectors": "div.trending-topics a.trending-topics-topic",
        "text_selector": "man-wysiwyg-box p",
        "title_selector": "h1.article-page-title",
    },
}

BODY_SELECTORS = {
    outlet: config["body_selector"]
    for outlet, config in OUTLET_SETTINGS.items()
}

OUTLET_TYPE = {
    outlet: config["outlet_type"]
    for outlet, config in OUTLET_SETTINGS.items()
}

MAIN_TOPICS = {
    outlet: config.get("main_topics", [])
    for outlet, config in OUTLET_SETTINGS.items()
}

TOPIC_TAG_SELECTORS = {
    outlet: config.get("topic_tag_selectors", [])
    for outlet, config in OUTLET_SETTINGS.items()
}

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

TEXT_SELECTORS = {
    outlet: config.get("text_selector")
    for outlet, config in OUTLET_SETTINGS.items()
}

TITLE_SELECTORS = {
    outlet: config.get("title_selector")
    for outlet, config in OUTLET_SETTINGS.items()
}

EXCLUDE_SELECTORS = {
    "magyarnemzet": ["div.raw-html-embed"],
    # add other outlets here as needed, e.g.:
    # "origo": ["div.recommendations"],
}

TAGS = []