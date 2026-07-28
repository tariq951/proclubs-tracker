import os
import asyncio
import logging
import discord
from discord import app_commands
from dotenv import load_dotenv

from config import get_config
from models import deduplicate_and_sort_matches, filter_weekly_matchday_fixtures, get_matchday_window
from scrapers import VPLScraper, VPGScraper, LPMScraper
from notifier import DiscordNotifier

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DiscordBot")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

def to_discord_py_embed(webhook_embed) -> discord.Embed:
    """Converts a discord_webhook.DiscordEmbed into a native discord.Embed object."""
    py_embed = discord.Embed(
        title=webhook_embed.title,
        description=webhook_embed.description,
        color=webhook_embed.color
    )
    for f in webhook_embed.fields:
        py_embed.add_field(name=f.get('name', ''), value=f.get('value', ''), inline=f.get('inline', False))
        
    if webhook_embed.footer:
        text = webhook_embed.footer.get('text', '')
        icon_url = webhook_embed.footer.get('icon_url', '')
        py_embed.set_footer(text=text, icon_url=icon_url)
        
    return py_embed

def run_single_scraper(scraper, club_name: str):
    """Runs a single scraper safely in a thread."""
    try:
        return scraper.fetch_matches(club_name)
    except Exception as e:
        logger.error(f"[{scraper.platform_name}] Scraper error: {e}")
        return []

def fetch_scraped_matches(club_name: str):
    """Synchronous worker function that runs all scrapers in parallel threads."""
    cfg = get_config()
    scrapers = [
        VPLScraper(base_url=cfg["vpl_base_url"], my_path=cfg["vpl_my_path"]),
        VPGScraper(base_url=cfg["vpg_base_url"], my_path=cfg["vpg_my_path"]),
        LPMScraper(base_url=cfg["lpm_base_url"], my_path=cfg["lpm_my_path"])
    ]

    from concurrent.futures import ThreadPoolExecutor
    raw_matches = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_single_scraper, s, club_name) for s in scrapers]
        for f in futures:
            try:
                raw_matches.extend(f.result(timeout=8))
            except Exception as err:
                logger.error(f"Scraper thread exception: {err}")

    sorted_matches = deduplicate_and_sort_matches(raw_matches, club_name=club_name)
    return filter_weekly_matchday_fixtures(sorted_matches)

class ScheduleBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Synced Slash Commands across all servers!")

client = ScheduleBot()

@client.event
async def on_ready():
    logger.info(f"Bot logged in as {client.user} (ID: {client.user.id})")

@client.tree.command(name="schedule", description="Scrape & post Virtua CF matchday schedule (Mon-Wed) across VPL, VPG, and LPM.")
async def schedule_command(interaction: discord.Interaction):
    """Slash command trigger for running Virtua CF schedule tracker on demand in Discord."""
    # Send immediate defer ACK to Discord so interaction status transitions to 'Thinking' immediately
    await interaction.response.defer(thinking=True)
    
    try:
        cfg = get_config()
        club_name = cfg["club_name"]
        
        # Run parallelized scraping in worker thread pool with 12s overall timeout limit
        final_matches = await asyncio.wait_for(
            asyncio.to_thread(fetch_scraped_matches, club_name),
            timeout=12.0
        )

        start_win, end_win = get_matchday_window()
        win_str = f"{start_win.strftime('%d %b')} – {end_win.strftime('%d %b %Y')}"

        # Build webhook embeds and convert to discord.py native embeds
        notifier = DiscordNotifier(webhook_url="")
        webhook_embeds = notifier.build_embeds(club_name, final_matches)
        py_embeds = [to_discord_py_embed(e) for e in webhook_embeds]

        # Generate Matchday Graphic Poster
        poster_file = None
        try:
            from poster_generator import generate_matchday_poster
            poster_path = generate_matchday_poster(club_name, final_matches, output_path="matchday_poster.png")
            if os.path.exists(poster_path):
                poster_file = discord.File(poster_path, filename="matchday_poster.png")
        except Exception as err:
            logger.warning(f"Could not generate graphic poster in bot: {err}")

        # Respond in Discord channel
        if py_embeds:
            if poster_file:
                py_embeds[0].set_image(url="attachment://matchday_poster.png")
                await interaction.followup.send(embed=py_embeds[0], file=poster_file)
            else:
                await interaction.followup.send(embed=py_embeds[0])
                
            for embed in py_embeds[1:]:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"No scheduled matches found for **{club_name}** in the matchday window ({win_str}).")
            
    except asyncio.TimeoutError:
        logger.error("Scraping execution timed out after 12s")
        await interaction.followup.send("⚠️ Match scraping took longer than 12s. Please try `/schedule` again.")
    except Exception as e:
        logger.error(f"Error executing /schedule slash command: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Failed to fetch match schedule: `{e}`")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN is missing in .env")
        print("Please set DISCORD_BOT_TOKEN=your_bot_token in your .env file to run bot.py")
    else:
        client.run(DISCORD_BOT_TOKEN)
