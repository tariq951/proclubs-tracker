import unittest
from datetime import datetime, timezone, timedelta
from scrapers.base import MYT_TIMEZONE
from models import Match, deduplicate_and_sort_matches
from scrapers.base import BaseScraper
from scrapers.mock import MockScraper
from scrapers.vpl import VPLScraper
from scrapers.lpm import LPMScraper
from scrapers.vpg import VPGScraper
from notifier import DiscordNotifier

class TestScraper(BaseScraper):
    def fetch_matches(self, club_name: str):
        return []

class TestProClubsMalaysiaTracker(unittest.TestCase):

    def test_date_parsing_myt_timezone(self):
        scraper = TestScraper("TEST MY", "https://test.my")
        
        # Date string without explicit offset should default to MYT (UTC+8)
        dt1 = scraper.parse_datetime("2026-07-28 21:00")
        self.assertIsNotNone(dt1)
        self.assertEqual(dt1.year, 2026)
        self.assertEqual(dt1.month, 7)
        self.assertEqual(dt1.day, 28)
        self.assertEqual(dt1.hour, 21)
        self.assertEqual(dt1.tzinfo, MYT_TIMEZONE)

    def test_deduplication_and_sorting(self):
        now = datetime.now(MYT_TIMEZONE)
        
        m_early = Match(
            platform="VPL MY",
            home_team="Virtua CF",
            away_team="Acousticsss FC",
            match_time=now + timedelta(hours=1),
            competition="S3/26 ROOKIE LEAGUE 2"
        )
        
        m_late = Match(
            platform="VPG MY",
            home_team="Virtua CF",
            away_team="Destaportivo FC",
            match_time=now + timedelta(hours=5),
            competition="VPG Malaysia Premiership"
        )

        # Duplicate of m_early with slightly drifted timestamp (2 minutes difference)
        m_dup = Match(
            platform="LPM MY",
            home_team="Acousticsss FC",
            away_team="Virtua CF",
            match_time=now + timedelta(hours=1, minutes=2),
            competition="LPM Malaysia Cup"
        )

        raw_list = [m_late, m_early, m_dup]
        result = deduplicate_and_sort_matches(raw_list, club_name="Virtua CF")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].home_team, "Virtua CF")
        self.assertEqual(result[0].away_team, "Acousticsss FC")
        self.assertEqual(result[1].away_team, "Destaportivo FC")

    def test_vpl_live_scraper(self):
        vpl = VPLScraper()
        matches = vpl.fetch_matches("Virtua CF")
        self.assertGreater(len(matches), 0, "VPLScraper should fetch fixtures for Virtua CF")
        self.assertIn("Virtua CF", matches[0].home_team + " " + matches[0].away_team)
        self.assertEqual(matches[0].match_time.tzinfo, MYT_TIMEZONE)

    def test_lpm_live_scraper(self):
        lpm = LPMScraper()
        matches = lpm.fetch_matches("Virtua CF")
        self.assertGreater(len(matches), 0, "LPMScraper should fetch fixtures from malaysiaproclub.com")
        self.assertIn("VIRTUA CF", (matches[0].home_team + " " + matches[0].away_team).upper())
        self.assertEqual(matches[0].match_time.tzinfo, MYT_TIMEZONE)

    def test_vpg_live_scraper(self):
        vpg = VPGScraper()
        matches = vpg.fetch_matches("Virtua CF")
        self.assertGreater(len(matches), 0, "VPGScraper should fetch fixtures from virtualprogaming.com API")
        self.assertIn("VIRTUA CF", (matches[0].home_team + " " + matches[0].away_team).upper())
        self.assertEqual(matches[0].match_time.tzinfo, MYT_TIMEZONE)

    def test_discord_embed_formatting_malaysia(self):
        vpl = VPLScraper()
        matches = vpl.fetch_matches("Virtua CF")
        sorted_matches = deduplicate_and_sort_matches(matches, "Virtua CF")
        
        notifier = DiscordNotifier("https://discord.com/api/webhooks/mock/123")
        embed = notifier.build_embed("Virtua CF", sorted_matches)

        self.assertIn("Virtua CF upcoming fixtures", embed.title)
        self.assertIn("Virtua CF", embed.description)

if __name__ == "__main__":
    unittest.main()
