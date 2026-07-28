import re
from typing import List
from models import Match
from scrapers.base import BaseScraper

class VPGScraper(BaseScraper):
    """Scraper for Virtual Pro Gaming (VPG) Malaysia."""

    def __init__(self, base_url: str = "https://virtualprogaming.com", my_path: str = "/team/virtua-cf/matches"):
        super().__init__("VPG MY", base_url)
        self.my_path = my_path
        self.api_base = "https://api.virtualprogaming.com/public"

    def _get_team_slug(self, club_name: str) -> str:
        """Extracts team slug from path or formats from club_name."""
        match = re.search(r'/team/([a-zA-Z0-9_\-]+)', self.my_path)
        if match:
            return match.group(1)
            
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', club_name.strip().lower()).strip('-')
        return slug if slug else "virtua-cf"

    def fetch_matches(self, club_name: str) -> List[Match]:
        self.logger.info(f"Fetching VPG Malaysia schedule for club '{club_name}'...")
        matches: List[Match] = []
        slug = self._get_team_slug(club_name)

        # 1. Primary VPG REST API (https://api.virtualprogaming.com/public/teams/{slug}/matches/)
        api_url = f"{self.api_base}/teams/{slug}/matches/"
        try:
            res = self.session.get(api_url, params={"match_status": "scheduled"}, timeout=(4, 6))
            if res.status_code == 200:
                data = res.json()
                raw_matches = data.get("data", [])
                for item in raw_matches:
                    try:
                        home_team = item.get("home_name", "")
                        away_team = item.get("away_name", "")
                        date_str = item.get("datetime", "")
                        
                        if not (home_team and away_team and date_str):
                            continue

                        match_time = self.parse_datetime(date_str)
                        if not match_time:
                            continue

                        match_id = item.get("id")
                        match_url = f"https://virtualprogaming.com/match/{match_id}" if match_id else f"https://virtualprogaming.com/team/{slug}/matches"
                        competition = "VPG Malaysia Championship"

                        home_logo_raw = item.get("home_logo")
                        home_logo = f"https://vpg-prod-user-uploads.fra1.cdn.digitaloceanspaces.com/{home_logo_raw}" if home_logo_raw else ""
                        
                        away_logo_raw = item.get("away_logo")
                        away_logo = f"https://vpg-prod-user-uploads.fra1.cdn.digitaloceanspaces.com/{away_logo_raw}" if away_logo_raw else ""
                        
                        league_logo_raw = item.get("league_logo") or item.get("community_logo")
                        league_logo = f"https://vpg-prod-user-uploads.fra1.cdn.digitaloceanspaces.com/{league_logo_raw}" if league_logo_raw else "https://virtualprogaming.com/images/vpg-logo.png"

                        matches.append(Match(
                            platform="VPG MY",
                            home_team=home_team,
                            away_team=away_team,
                            match_time=match_time,
                            competition=competition,
                            match_url=match_url,
                            home_logo=home_logo,
                            away_logo=away_logo,
                            league_logo=league_logo
                        ))
                    except Exception as err:
                        self.logger.debug(f"Error parsing VPG API match item: {err}")
        except Exception as e:
            self.logger.warning(f"Error querying VPG API {api_url}: {e}")

        # 2. Fallback to HTML scraping if API returned no matches
        if not matches:
            fixtures_url = f"{self.base_url}/team/{slug}/matches"
            soup = self.fetch_soup(fixtures_url)
            if soup:
                fixture_elements = soup.select(".match-item, .fixture-box, .vpg-match-row, table.fixtures-list tr")
                for el in fixture_elements:
                    try:
                        home_el = el.select_one(".team-home-name, .home, td.home")
                        away_el = el.select_one(".team-away-name, .away, td.away")
                        date_el = el.select_one(".fixture-time, .datetime, td.date")
                        comp_el = el.select_one(".comp-title, .league, td.competition")
                        link_el = el.select_one("a[href*='/match']")

                        if not (home_el and away_el and date_el):
                            continue

                        home_team = home_el.get_text(strip=True)
                        away_team = away_el.get_text(strip=True)

                        date_str = date_el.get_text(strip=True)
                        match_time = self.parse_datetime(date_str)
                        if not match_time:
                            continue

                        competition = comp_el.get_text(strip=True) if comp_el else "VPG Malaysia Championship"
                        match_url = f"{self.base_url}{link_el['href']}" if link_el and link_el.get("href") else fixtures_url

                        matches.append(Match(
                            platform="VPG MY",
                            home_team=home_team,
                            away_team=away_team,
                            match_time=match_time,
                            competition=competition,
                            match_url=match_url
                        ))
                    except Exception as err:
                        self.logger.debug(f"Error parsing VPG MY HTML element: {err}")

        return matches
