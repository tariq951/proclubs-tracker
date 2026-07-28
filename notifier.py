import os
import logging
import re
from itertools import groupby
from typing import List
from discord_webhook import DiscordWebhook, DiscordEmbed
from models import Match

logger = logging.getLogger("Notifier")

# Platform badge colors for Discord Embeds (RGB int)
PLATFORM_COLORS = {
    "VPL MY": 0x3498DB,  # Vibrant Blue
    "VPG MY": 0xE74C3C,  # Crimson Red
    "LPM MY": 0x2ECC71,  # Emerald Green
    "MOCK MY": 0x9B59B6, # Amethyst Purple
}

# Platform color-coded emojis
PLATFORM_EMOJIS = {
    "VPL": "🔴",
    "VPG": "🔵",
    "LPM": "🟡",
}

class DiscordNotifier:
    """Handles creating and sending formatted Discord Embeds for Pro Clubs Malaysia."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url.strip() if webhook_url else ""

    def _get_location_tag(self, match: Match, club_name: str) -> str:
        """Determines [Home] or [Away] tag relative to club_name."""
        norm_club = re.sub(r'\W+', '', club_name.lower())
        norm_home = re.sub(r'\W+', '', match.home_team.lower())
        if norm_club in norm_home:
            return "[Home]"
        return "[Away]"

    def _get_platform_emoji(self, platform: str) -> str:
        """Returns color-coded emoji for platform: 🔴 for VPL, 🔵 for VPG, 🟡 for LPM."""
        p_upper = platform.upper()
        if "VPL" in p_upper:
            return "🔴"
        elif "VPG" in p_upper:
            return "🔵"
        elif "LPM" in p_upper:
            return "🟡"
        return "⚽"

    def _get_date_header(self, match: Match) -> str:
        """Formats date as 'Monday 27/7:'."""
        dt = match.match_time
        day_name = dt.strftime("%A")
        day_num = dt.strftime("%d").lstrip("0")
        month_num = dt.strftime("%m").lstrip("0")
        return f"{day_name} {day_num}/{month_num}:"

    def build_embeds(self, club_name: str, matches: List[Match], chunk_size: int = 15) -> List[DiscordEmbed]:
        """
        Constructs Discord Embeds formatted in a single description block with zero-width spaces (\u200b)
        for precise control over vertical line spacing.
        """
        if not matches:
            embed = DiscordEmbed(
                title=f"{club_name} upcoming fixtures",
                description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nNo upcoming scheduled matches found.",
                color=0x95A5A6
            )
            embed.set_footer(
                text="Pro Clubs Malaysia Schedule Tracker • Page 1/1 (0 Fixtures Total)",
                icon_url="https://cdn-icons-png.flaticon.com/512/861/861512.png"
            )
            embed.set_timestamp()
            return [embed]

        embeds: List[DiscordEmbed] = []
        chunks = [matches[i:i + chunk_size] for i in range(0, len(matches), chunk_size)]
        total_chunks = len(chunks)

        for chunk_idx, chunk in enumerate(chunks, 1):
            title = f"{club_name} upcoming fixtures"
            if total_chunks > 1:
                title += f" (Part {chunk_idx}/{total_chunks})"

            # Group matches in this chunk by match day
            grouped_data = []
            for date_str, group_iter in groupby(chunk, key=self._get_date_header):
                grouped_data.append((date_str, list(group_iter)))

            desc_lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]

            for g_idx, (date_str, day_matches) in enumerate(grouped_data):
                desc_lines.append(f"{date_str}")
                for m_idx, match in enumerate(day_matches):
                    location_tag = self._get_location_tag(match, club_name)
                    platform_emoji = self._get_platform_emoji(match.platform)
                    details_link = f" • [Match Page]({match.match_url})" if match.match_url else ""
                    
                    desc_lines.append(f"{platform_emoji} {match.home_team} vs {match.away_team} {location_tag}")
                    desc_lines.append(f"⏰ {match.discord_time_short}")
                    desc_lines.append(f"🏆 {match.competition}{details_link}")
                    
                    # Single empty line between matches of the same day
                    if m_idx < len(day_matches) - 1:
                        desc_lines.append("")
                        
                # Zero-width space line for visible section gap before next day
                if g_idx < len(grouped_data) - 1:
                    desc_lines.append("\u200b")

            embed_desc = "\n".join(desc_lines)

            embed = DiscordEmbed(
                title=title,
                description=embed_desc,
                color=PLATFORM_COLORS.get(chunk[0].platform, 0x3498DB)
            )

            embed.set_footer(
                text=f"Pro Clubs Malaysia Schedule Tracker • Page {chunk_idx}/{total_chunks} ({len(matches)} Fixtures Total)",
                icon_url="https://cdn-icons-png.flaticon.com/512/861/861512.png"
            )
            embed.set_timestamp()
            embeds.append(embed)

        return embeds

    def build_embed(self, club_name: str, matches: List[Match]) -> DiscordEmbed:
        """Backwards-compatible helper that returns the primary embed."""
        embeds = self.build_embeds(club_name, matches)
        return embeds[0]

    def send_schedule(self, club_name: str, matches: List[Match], poster_path: str = "", dry_run: bool = False) -> bool:
        """Sends the chunked schedule embeds to Discord or prints preview if dry_run."""
        embeds = self.build_embeds(club_name, matches)

        is_placeholder_url = not self.webhook_url or "YOUR_DISCORD_WEBHOOK_URL" in self.webhook_url or not self.webhook_url.startswith("http")

        if dry_run or is_placeholder_url:
            logger.info("=" * 60)
            logger.info(" DRY-RUN / EMBED PREVIEW MODE (Webhook not dispatched to live Discord)")
            logger.info("=" * 60)
            for idx, embed in enumerate(embeds, 1):
                print(f"\n--- DISCORD EMBED PREVIEW [Part {idx}/{len(embeds)} - {club_name}] ---")
                print(f"Title: {embed.title}")
                print(f"Description: {embed.description}")
                print(f"Footer: {embed.footer['text']}")
                if poster_path and os.path.exists(poster_path):
                    print(f"Poster Image Attached: {poster_path}")
                print("-" * 60 + "\n")
            if is_placeholder_url and not dry_run:
                logger.warning("To send real messages to Discord, set DISCORD_WEBHOOK_URL in .env or pass --webhook <URL>")
            return True

        success = True
        for idx, embed in enumerate(embeds, 1):
            try:
                webhook = DiscordWebhook(url=self.webhook_url)
                if poster_path and os.path.exists(poster_path) and idx == 1:
                    filename = os.path.basename(poster_path)
                    embed.set_image(url=f"attachment://{filename}")
                    with open(poster_path, "rb") as f:
                        webhook.add_file(file=f.read(), filename=filename)
                
                webhook.add_embed(embed)
                response = webhook.execute()
                status_code = response.status_code if hasattr(response, 'status_code') else (response[0].status_code if response else 0)
                
                if status_code in (200, 204):
                    logger.info(f"Successfully posted schedule embed part {idx}/{len(embeds)} to Discord webhook! (Status: {status_code})")
                else:
                    logger.error(f"Discord Webhook part {idx} returned status code {status_code}")
                    success = False
            except Exception as e:
                logger.error(f"Failed to post embed part {idx} to Discord webhook: {e}")
                success = False

        return success
