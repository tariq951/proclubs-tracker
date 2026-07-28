import sys
import argparse
import logging
from typing import List

from config import get_config
from models import Match, deduplicate_and_sort_matches, filter_weekly_matchday_fixtures, get_matchday_window
from scrapers import VPLScraper, VPGScraper, LPMScraper, MockScraper, BaseScraper
from notifier import DiscordNotifier

logger = logging.getLogger("MainTracker")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pro Clubs Malaysia Match Tracker - Scrapes VPL MY, VPG MY, and LPM MY schedules, deduplicates, sorts, and posts to Discord."
    )
    parser.add_argument(
        "--club", "-c",
        type=str,
        help="Club name to track (e.g., 'Virtua CF')"
    )
    parser.add_argument(
        "--webhook", "-w",
        type=str,
        help="Discord Webhook URL"
    )
    parser.add_argument(
        "--all-future",
        action="store_true",
        help="Include all upcoming future matches without Mon-Wed matchday window filter"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run scraper and format schedule without sending webhook payload to Discord"
    )
    parser.add_argument(
        "--test-mock",
        action="store_true",
        help="Use mock data generator to verify Malaysia date parsing, sorting, deduplication, and Discord embed formatting"
    )
    parser.add_argument(
        "--include-mock",
        action="store_true",
        help="Include mock test fixtures alongside live scraped fixtures"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    return parser.parse_args()

def print_terminal_schedule(club_name: str, matches: List[Match]):
    """Pretty prints the sorted Malaysia match schedule to terminal stdout."""
    start_win, end_win = get_matchday_window()
    win_str = f"{start_win.strftime('%d %b')} - {end_win.strftime('%d %b %Y')}"
    
    print("\n" + "=" * 80)
    print(f"       🇲🇾 PRO CLUBS MALAYSIA MATCHDAY SCHEDULE ({win_str}): {club_name.upper()}")
    print("=" * 80)
    
    if not matches:
        print(f"  No upcoming matches found across VPL MY, VPG MY, or LPM MY for matchday window ({win_str}).")
    else:
        print(f"{'#':<3} | {'PLATFORM':<8} | {'MATCHUP':<38} | {'KICKOFF TIME (MYT UTC+8)':<26} | {'COMPETITION':<25}")
        print("-" * 105)
        for idx, m in enumerate(matches, 1):
            matchup = f"{m.home_team} vs {m.away_team}"
            time_str = m.match_time.strftime("%Y-%m-%d (%a) %H:%M MYT")
            print(f"{idx:<3} | {m.platform:<8} | {matchup:<38} | {time_str:<26} | {m.competition:<25}")
    print("=" * 80 + "\n")

def run_tracker():
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    cfg = get_config(club_name=args.club, webhook_url=args.webhook)
    club_name = cfg["club_name"]
    webhook_url = cfg["discord_webhook_url"]

    logger.info(f"Starting Pro Clubs Malaysia schedule tracking for club: '{club_name}'")

    raw_matches: List[Match] = []
    
    if args.test_mock:
        scrapers: List[BaseScraper] = [MockScraper()]
    else:
        scrapers: List[BaseScraper] = [
            VPLScraper(base_url=cfg["vpl_base_url"], my_path=cfg["vpl_my_path"]),
            VPGScraper(base_url=cfg["vpg_base_url"], my_path=cfg["vpg_my_path"]),
            LPMScraper(base_url=cfg["lpm_base_url"], my_path=cfg["lpm_my_path"])
        ]
        if args.include_mock:
            scrapers.append(MockScraper())

    for scraper in scrapers:
        try:
            matches = scraper.fetch_matches(club_name)
            logger.info(f"[{scraper.platform_name}] Found {len(matches)} match fixture(s)")
            raw_matches.extend(matches)
        except Exception as e:
            logger.error(f"[{scraper.platform_name}] Scraper encountered an error: {e}")

    logger.info(f"Total raw matches fetched: {len(raw_matches)}")

    # Deduplicate and sort matches chronologically
    sorted_matches = deduplicate_and_sort_matches(raw_matches, club_name=club_name)
    logger.info(f"Total unique matches after deduplication: {len(sorted_matches)}")

    # Filter to Monday-Wednesday matchday window (or all future if --all-future)
    if args.all_future:
        final_matches = sorted_matches
    else:
        final_matches = filter_weekly_matchday_fixtures(sorted_matches)

    logger.info(f"Total matches in matchday window: {len(final_matches)}")

    # Print clean table to terminal
    print_terminal_schedule(club_name, final_matches)

    # Generate Matchday Graphic Poster
    poster_path = ""
    try:
        from logo_cache import logo_cache
        logo_cache.populate_from_vpl_fixtures("15607")
        logo_cache.populate_from_vpl_teams_page()
        
        from poster_generator import generate_matchday_poster
        poster_path = generate_matchday_poster(club_name, final_matches, output_path="matchday_poster.png")
    except Exception as err:
        logger.warning(f"Could not generate graphic poster: {err}")

    # Post Discord Embed + Poster via Webhook
    notifier = DiscordNotifier(webhook_url=webhook_url)
    success = notifier.send_schedule(club_name, final_matches, poster_path=poster_path, dry_run=args.dry_run)
    
    if success:
        logger.info("Malaysia Schedule pipeline completed successfully!")
    else:
        logger.warning("Malaysia Schedule pipeline completed with webhook delivery warnings.")

if __name__ == "__main__":
    run_tracker()
