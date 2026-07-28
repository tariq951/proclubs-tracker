import re
from typing import List
from models import Match
from scrapers.base import BaseScraper

class LPMScraper(BaseScraper):
    """Scraper for LPM (Liga Proclub Malaysia - malaysiaproclub.com)."""

    def __init__(self, base_url: str = "https://malaysiaproclub.com", my_path: str = "/team/virtua-cf/"):
        super().__init__("LPM MY", base_url)
        self.my_path = my_path

    def _get_team_url(self, club_name: str) -> str:
        """Constructs or formats the team page URL on malaysiaproclub.com."""
        if self.my_path and self.my_path.startswith("http"):
            return self.my_path
        
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', club_name.strip().lower()).strip('-')
        if not slug or slug in ('team', 'virtua-cf'):
            slug = 'virtua-cf'
            
        return f"{self.base_url.rstrip('/')}/team/{slug}/"

    def fetch_matches(self, club_name: str) -> List[Match]:
        self.logger.info(f"Fetching LPM Malaysia schedule for club '{club_name}'...")
        matches: List[Match] = []
        team_url = self._get_team_url(club_name)
        
        soup = self.fetch_soup(team_url)
        if not soup:
            self.logger.warning(f"Could not reach LPM Malaysia page: {team_url}")
            return matches

        # 1. Primary SportsPress event blocks parsing (table.sp-event-blocks)
        table = soup.select_one("table.sp-event-blocks")
        if table:
            rows = table.select("tbody tr.sp-row")
            for row in rows:
                try:
                    time_el = row.select_one("time.sp-event-date")
                    title_el = row.select_one("h4.sp-event-title a")
                    season_el = row.select_one(".sp-event-season")
                    logo_odd = row.select_one(".logo-odd")
                    logo_even = row.select_one(".logo-even")

                    if not time_el or not title_el:
                        continue

                    home_team = logo_odd.get("title") if logo_odd and logo_odd.get("title") else ""
                    away_team = logo_even.get("title") if logo_even and logo_even.get("title") else ""
                    
                    match_title = title_el.get_text(strip=True)
                    if not home_team or not away_team:
                        parts = match_title.split(" vs ")
                        if len(parts) == 2:
                            home_team, away_team = parts[0].strip(), parts[1].strip()

                    date_str = time_el.get("content") or time_el.get("datetime") or time_el.get_text(strip=True)
                    match_time = self.parse_datetime(date_str)
                    if not match_time:
                        continue

                    competition = "LPM Junior A"
                    match_url = title_el.get("href") if title_el and title_el.get("href") else team_url
                    
                    home_img = logo_odd.select_one("img") if logo_odd else None
                    away_img = logo_even.select_one("img") if logo_even else None
                    
                    home_logo = home_img.get("src") if home_img and home_img.get("src") else (logo_odd.get("src") if logo_odd and logo_odd.get("src") else "")
                    away_logo = away_img.get("src") if away_img and away_img.get("src") else (logo_even.get("src") if logo_even and logo_even.get("src") else "")
                    league_logo = "https://malaysiaproclub.com/wp-content/uploads/2023/10/LPM-Logo.png"

                    matches.append(Match(
                        platform="LPM MY",
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
                    self.logger.debug(f"Error parsing LPM MY fixture row: {err}")

        # 2. Generic fallback selector if table.sp-event-blocks wasn't present
        if not matches:
            fixture_elements = soup.select(".lpm-match-card, .fixture-row, .match-detail-row, tr.sp-row")
            for el in fixture_elements:
                try:
                    home_el = el.select_one(".home-name, .team-a, .logo-odd")
                    away_el = el.select_one(".away-name, .team-b, .logo-even")
                    date_el = el.select_one(".match-date-time, .schedule-time, time")
                    comp_el = el.select_one(".league-tag, .tournament-name, .sp-event-season")
                    link_el = el.select_one("a[href*='/event/'], a[href*='/match']")

                    if not (home_el and away_el and date_el):
                        continue

                    home_team = home_el.get("title") if home_el.get("title") else home_el.get_text(strip=True)
                    away_team = away_el.get("title") if away_el.get("title") else away_el.get_text(strip=True)

                    date_str = date_el.get("content") or date_el.get("datetime") or date_el.get_text(strip=True)
                    match_time = self.parse_datetime(date_str)
                    if not match_time:
                        continue

                    competition = "LPM Junior A"
                    match_url = link_el['href'] if link_el and link_el.get('href') else team_url

                    matches.append(Match(
                        platform="LPM MY",
                        home_team=home_team,
                        away_team=away_team,
                        match_time=match_time,
                        competition=competition,
                        match_url=match_url
                    ))
                except Exception as err:
                    self.logger.debug(f"Error parsing LPM MY fallback fixture element: {err}")

        return matches
