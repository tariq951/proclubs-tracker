import re
from typing import List
from models import Match
from scrapers.base import BaseScraper

class VPLScraper(BaseScraper):
    """Scraper for Virtual Pro League (VPL) Malaysia - Virtua CF."""
    
    def __init__(self, base_url: str = "https://www.virtualproleague.com", my_path: str = "/team/15607/virtua-cf"):
        super().__init__("VPL MY", base_url)
        self.my_path = my_path

    def _extract_team_id(self, club_name: str) -> str:
        """Extracts team ID from path or defaults to 15607 for Virtua CF / Virtual CF."""
        match = re.search(r'/team/(\d+)', self.my_path)
        if match:
            return match.group(1)
        
        norm_club = re.sub(r'\W+', '', club_name.lower())
        if 'virtua' in norm_club or 'virtual' in norm_club:
            return "15607"
        return "15607"

    def fetch_matches(self, club_name: str) -> List[Match]:
        self.logger.info(f"Fetching VPL Malaysia schedule for club '{club_name}'...")
        matches: List[Match] = []
        
        team_id = self._extract_team_id(club_name)
        
        # 1. Primary VPL AJAX Calendar endpoint (tabs-team-info-6)
        calendar_url = f"{self.base_url}/tabs-team-info-6"
        soup = self.fetch_soup(calendar_url, params={"id_time": team_id})
        
        if soup:
            articles = soup.select("article.game-result")
            for art in articles:
                try:
                    home_el = art.select_one(".game-result-team-first .game-result-team-name")
                    away_el = art.select_one(".game-result-team-second .game-result-team-name")
                    time_el = art.select_one("time")
                    comp_el = art.select_one(".game-result-details span")
                    link_el = art.select_one("a[href*='/match-info/']")

                    if not (home_el and away_el and time_el):
                        continue

                    home_team = home_el.get_text(strip=True)
                    away_team = away_el.get_text(strip=True)
                    
                    date_str = time_el.get("datetime") or time_el.get_text(strip=True)
                    match_time = self.parse_datetime(date_str)
                    if not match_time:
                        continue

                    raw_comp = comp_el.get_text(strip=True) if comp_el else ""
                    competition = "VPL Rookie League 2" if ("rookie" in raw_comp.lower() or not raw_comp) else raw_comp
                    match_url = f"{self.base_url}{link_el['href']}" if link_el and link_el.get("href") else f"{self.base_url}{self.my_path}"

                    home_img = art.select_one(".game-result-team-first img")
                    away_img = art.select_one(".game-result-team-second img")
                    comp_img = art.select_one(".game-result-details img")

                    home_logo = f"{self.base_url}/{home_img['src'].lstrip('/')}" if home_img and home_img.get("src") else ""
                    away_logo = f"{self.base_url}/{away_img['src'].lstrip('/')}" if away_img and away_img.get("src") else ""
                    league_logo = f"{self.base_url}/{comp_img['src'].lstrip('/')}" if comp_img and comp_img.get("src") else f"{self.base_url}/images/vpl_logo.png"

                    matches.append(Match(
                        platform="VPL MY",
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
                    self.logger.debug(f"Error parsing VPL MY article fixture: {err}")

        # 2. Fallback to generic page search if no matches returned from tab 6
        if not matches:
            urls = [
                (f"{self.base_url}{self.my_path}", None),
                (f"{self.base_url}/en/search", {"q": club_name, "type": "teams", "country": "MY"})
            ]

            for url, params in urls:
                soup = self.fetch_soup(url, params=params)
                if not soup:
                    continue

                fixture_elements = soup.select(".fixture-item, tr.fixture-row, .match-card, .table-matches tbody tr")
                for el in fixture_elements:
                    try:
                        home_el = el.select_one(".home-team, .team-home, td:nth-child(2)")
                        away_el = el.select_one(".away-team, .team-away, td:nth-child(4)")
                        date_el = el.select_one(".match-date, .date, .time, td:nth-child(1)")
                        comp_el = el.select_one(".competition, .league-name, .badge-league")
                        link_el = el.select_one("a[href*='/match/']")

                        if not (home_el and away_el and date_el):
                            continue

                        home_team = home_el.get_text(strip=True)
                        away_team = away_el.get_text(strip=True)
                        
                        date_str = date_el.get_text(strip=True)
                        match_time = self.parse_datetime(date_str)
                        if not match_time:
                            continue

                        competition = "VPL Rookie League 2"
                        match_url = f"{self.base_url}{link_el['href']}" if link_el and link_el.get("href") else f"{self.base_url}{self.my_path}"

                        matches.append(Match(
                            platform="VPL MY",
                            home_team=home_team,
                            away_team=away_team,
                            match_time=match_time,
                            competition=competition,
                            match_url=match_url
                        ))
                    except Exception as err:
                        self.logger.debug(f"Error parsing VPL MY generic fixture element: {err}")

                if matches:
                    break

        return matches
