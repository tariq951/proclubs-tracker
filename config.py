import os
from datetime import timezone, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

DEFAULT_CLUB_NAME = os.getenv("CLUB_NAME", "Virtua CF")
DEFAULT_DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1531212399141589002/08HvXgtYhUhXxjNz3Tdso4VD1gJXu5-_KHkjHslGew2b4nomVQ4jm12oOTO9_MEt5pUI"
)

# Malaysia Regional Settings (MYT is UTC+8)
MALAYSIA_TZ = timezone(timedelta(hours=8))

# Regional URL defaults for VPL Malaysia, VPG Malaysia, and LPM Malaysia
VPL_BASE_URL = os.getenv("VPL_BASE_URL", "https://www.virtualproleague.com")
VPL_MY_PATH = os.getenv("VPL_MY_PATH", "/team/15607/virtua-cf")

VPG_BASE_URL = os.getenv("VPG_BASE_URL", "https://virtualprogaming.com")
VPG_MY_PATH = os.getenv("VPG_MY_PATH", "/team/virtua-cf/matches")

LPM_BASE_URL = os.getenv("LPM_BASE_URL", "https://malaysiaproclub.com")
LPM_MY_PATH = os.getenv("LPM_MY_PATH", "/team/virtua-cf/")

def get_config(club_name: str = None, webhook_url: str = None) -> Dict[str, Any]:
    """Retrieve runtime configuration for Malaysia Pro Clubs tracking."""
    final_club = club_name if club_name else os.getenv("CLUB_NAME", DEFAULT_CLUB_NAME)
    final_webhook = webhook_url if webhook_url else os.getenv("DISCORD_WEBHOOK_URL", DEFAULT_DISCORD_WEBHOOK_URL)
    
    return {
        "club_name": final_club,
        "discord_webhook_url": final_webhook,
        "region": "Malaysia",
        "timezone": MALAYSIA_TZ,
        "vpl_base_url": VPL_BASE_URL,
        "vpl_my_path": VPL_MY_PATH,
        "vpg_base_url": VPG_BASE_URL,
        "vpg_my_path": VPG_MY_PATH,
        "lpm_base_url": LPM_BASE_URL,
        "lpm_my_path": LPM_MY_PATH
    }
