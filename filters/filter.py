"""Compatibility wrapper around the integrated scraper pipeline."""

from scraper import filter_url_records as filter_urls
from scraper import filter_url_records_file as filter_urls_file

__all__ = ["filter_urls", "filter_urls_file"]
