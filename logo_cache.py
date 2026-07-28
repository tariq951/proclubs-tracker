import os
import re
import json
import logging
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("LogoCache")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "logo_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "vpl_logos.json")

class VPLLogoCache:
    """
    Caches and resolves high-quality official team crests/shields from VPL (Virtual Pro League)
    for all Malaysian Pro Clubs (including VPG & LPM fixtures).
    """

    def __init__(self, base_url: str = "https://www.virtualproleague.com"):
        self.base_url = base_url.rstrip("/")
        self.cache: Dict[str, str] = {}
        self.ensure_cache_dir()
        self.load_cache()

    def ensure_cache_dir(self):
        """Creates logo_cache directory if it does not exist."""
        os.makedirs(CACHE_DIR, exist_ok=True)

    def normalize_name(self, team_name: str) -> str:
        """Normalizes team name string for fuzzy key matching."""
        clean = re.sub(r'[^a-zA-Z0-9]+', '', team_name.lower())
        # Strip common trailing tags
        clean = re.sub(r'vfc$|fc$|esports$|club$', '', clean)
        return clean

    def load_cache(self):
        """Loads cached logo mapping from JSON file."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} VPL team logo(s) from cache.")
            except Exception as e:
                logger.warning(f"Failed to load VPL logo cache: {e}")
                self.cache = {}

    def save_cache(self):
        """Saves current logo mapping to JSON file."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} VPL team logo(s) to {CACHE_FILE}.")
        except Exception as e:
            logger.error(f"Failed to save VPL logo cache: {e}")

    def update_logo(self, team_name: str, logo_url: str, save_now: bool = False):
        """Updates team logo in cache if logo_url is valid."""
        if not team_name or not logo_url or "default.png" in logo_url:
            return
            
        norm_key = self.normalize_name(team_name)
        if not norm_key:
            return

        # Convert shield_mini to full-size shield URL if available
        full_logo = logo_url.replace("/shield_mini/", "/shield/")
        if not full_logo.startswith("http"):
            full_logo = f"{self.base_url}/{full_logo.lstrip('/')}"

        self.cache[norm_key] = full_logo
        if save_now:
            self.save_cache()

    def get_logo(self, team_name: str) -> Optional[str]:
        """Look up team logo in VPL cache with fallback normalization and live VPL search fallback."""
        if not team_name:
            return None
            
        norm_key = self.normalize_name(team_name)
        if norm_key in self.cache:
            return self.cache[norm_key]

        # Substring fuzzy search in cache keys
        for key, url in self.cache.items():
            if norm_key in key or key in norm_key:
                return url

        # Live VPL search lookup
        return self.search_and_cache_vpl_logo(team_name)

    def search_and_cache_vpl_logo(self, team_name: str) -> Optional[str]:
        """Queries VPL sidebar search (/search-results?search=...) and fetches team page to harvest official shield."""
        if not team_name:
            return None
            
        norm_key = self.normalize_name(team_name)
        headers = {"User-Agent": "Mozilla/5.0"}
        search_url = f"{self.base_url}/search-results"
        try:
            res = requests.get(search_url, params={"search": team_name}, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                team_links = soup.select("a[href*='/team/']")
                for a in team_links:
                    t_name = a.get_text(strip=True)
                    if not t_name:
                        continue
                    if self.normalize_name(t_name) == norm_key or norm_key in self.normalize_name(t_name):
                        href = a["href"]
                        team_url = f"{self.base_url}{href}" if href.startswith("/") else href
                        
                        t_res = requests.get(team_url, headers=headers, timeout=5)
                        if t_res.status_code == 200:
                            t_soup = BeautifulSoup(t_res.text, "html.parser")
                            # Prioritize main team profile shield (escudo_png / escudo_time_)
                            escudo_img = t_soup.select_one("img.escudo_png") or t_soup.select_one("img[src*='escudo_time_']")
                            if escudo_img and escudo_img.get("src"):
                                img_src = escudo_img["src"]
                                self.update_logo(team_name, img_src, save_now=True)
                                logger.info(f"Live searched & cached VPL shield for '{team_name}': {img_src}")
                                return self.cache.get(norm_key)
                                
                            # Fallback to any non-default shield
                            imgs = [img.get("src") for img in t_soup.select("img") if img.get("src") and ("shield" in img.get("src") or "escudo" in img.get("src"))]
                            for img_src in imgs:
                                if "default" not in img_src and "team_emblem_1784981234" not in img_src:
                                    self.update_logo(team_name, img_src, save_now=True)
                                    logger.info(f"Live searched & cached VPL fallback shield for '{team_name}': {img_src}")
                                    return self.cache.get(norm_key)
        except Exception as e:
            logger.debug(f"Error searching VPL logo for '{team_name}': {e}")

        return None

    def populate_from_vpl_fixtures(self, club_team_id: str = "15607"):
        """Scrapes VPL AJAX tab 6 fixtures to extract official VPL logos for all playing teams."""
        url = f"{self.base_url}/tabs-team-info-6"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            res = requests.get(url, params={"id_time": club_team_id}, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for art in soup.select("article.game-result"):
                    home_el = art.select_one(".game-result-team-first .game-result-team-name")
                    home_img = art.select_one(".game-result-team-first img")
                    
                    away_el = art.select_one(".game-result-team-second .game-result-team-name")
                    away_img = art.select_one(".game-result-team-second img")
                    
                    if home_el and home_img and home_img.get("src"):
                        self.update_logo(home_el.get_text(strip=True), home_img["src"])
                        
                    if away_el and away_img and away_img.get("src"):
                        self.update_logo(away_el.get_text(strip=True), away_img["src"])
                        
                self.save_cache()
        except Exception as e:
            logger.warning(f"Error populating VPL logo cache from fixtures: {e}")

    def populate_from_vpl_teams_page(self):
        """Scrapes VPL Malaysia teams list page to harvest team crests."""
        url = f"{self.base_url}/teams?country=MY"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                # Look for team links with images
                for a in soup.select("a[href*='/team/']"):
                    img = a.select_one("img")
                    title = a.get_text(strip=True) or a.get("title") or ""
                    if title and img and img.get("src"):
                        self.update_logo(title, img["src"])
                self.save_cache()
        except Exception as e:
            logger.warning(f"Error populating VPL logo cache from teams page: {e}")

# Global Cache Singleton
logo_cache = VPLLogoCache()
