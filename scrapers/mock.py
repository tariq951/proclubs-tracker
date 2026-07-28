from datetime import datetime, timedelta, timezone
from typing import List
from models import Match
from scrapers.base import BaseScraper, MYT_TIMEZONE

class MockScraper(BaseScraper):
    """
    Mock scraper generating realistic Malaysia Pro Clubs fixture data (VPL MY, VPG MY, LPM MY)
    for deterministic local testing, date parsing validation, and deduplication checks.
    """

    def __init__(self):
        super().__init__("MOCK MY", "https://mock.proclubs.my")

    def fetch_matches(self, club_name: str) -> List[Match]:
        self.logger.info(f"Generating mock Malaysia Pro Clubs schedule for '{club_name}'...")
        now = datetime.now(MYT_TIMEZONE)
        
        # Generate dates in MYT (UTC+8) relative to current time
        m1_time = now + timedelta(hours=3, minutes=15)
        m2_time = now + timedelta(days=1, hours=2, minutes=0)
        m3_time = now + timedelta(days=1, hours=2, minutes=5)  # Near duplicate of m2 to test deduplication!
        m4_time = now + timedelta(days=2, hours=4, minutes=30)
        m5_time = now + timedelta(days=3, hours=1, minutes=0)

        raw_fixtures = [
            Match(
                platform="VPL MY",
                home_team=club_name,
                away_team="Harimau Esports MY",
                match_time=m1_time,
                competition="VPL Malaysia Super League",
                match_url="https://www.virtualproleague.com/en/match/101"
            ),
            Match(
                platform="VPG MY",
                home_team="KL City Pro Clubs",
                away_team=club_name,
                match_time=m2_time,
                competition="VPG Malaysia Premiership",
                match_url="https://www.virtualprogaming.com/match/502"
            ),
            # Near duplicate match entry (VPL MY cross-listing of same fixture vs KL City Pro Clubs)
            Match(
                platform="VPL MY",
                home_team="KL City Pro Clubs",
                away_team=club_name,
                match_time=m3_time,
                competition="VPL Malaysia Super Cup",
                match_url="https://www.virtualproleague.com/en/match/102"
            ),
            Match(
                platform="LPM MY",
                home_team=club_name,
                away_team="Selangor Tigers Esports",
                match_time=m4_time,
                competition="LPM Malaysia Cup",
                match_url="https://www.lpmesports.com/match/990"
            ),
            Match(
                platform="VPG MY",
                home_team="Borneo Gaming MY",
                away_team=club_name,
                match_time=m5_time,
                competition="VPG Malaysia Premiership",
                match_url="https://www.virtualprogaming.com/match/503"
            ),
        ]
        
        return raw_fixtures
