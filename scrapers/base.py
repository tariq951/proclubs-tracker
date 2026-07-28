import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from models import Match

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Default timezone for Malaysia Pro Clubs (MYT: UTC+8)
MYT_TIMEZONE = timezone(timedelta(hours=8))

class BaseScraper(ABC):
    """Abstract Base Class for all Pro Clubs League Scrapers (Malaysia Region)."""
    
    def __init__(self, platform_name: str, base_url: str):
        self.platform_name = platform_name
        self.base_url = base_url
        self.logger = logging.getLogger(f"Scraper.{platform_name}")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-MY,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        })

    def parse_datetime(self, date_str: str, default_tz: timezone = MYT_TIMEZONE) -> Optional[datetime]:
        """
        Parses arbitrary date strings into a timezone-aware datetime object (defaulting to MYT / UTC+8).
        """
        if not date_str or not date_str.strip():
            return None
            
        try:
            cleaned = date_str.strip()
            dt = date_parser.parse(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=default_tz)
            else:
                dt = dt.astimezone(MYT_TIMEZONE)
            return dt
        except Exception as e:
            self.logger.warning(f"Failed to parse date string '{date_str}': {e}")
            return None

    def fetch_soup(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """Fetches a webpage and returns a BeautifulSoup parsed tree."""
        try:
            res = self.session.get(url, params=params, timeout=(4, 6))
            res.raise_for_status()
            return BeautifulSoup(res.text, "html.parser")
        except Exception as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None

    @abstractmethod
    def fetch_matches(self, club_name: str) -> List[Match]:
        """Scrapes and returns upcoming matches for the specified club."""
        pass
