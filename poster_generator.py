import os
import re
import io
import logging
from typing import List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont
from models import Match

logger = logging.getLogger("PosterGenerator")

# Color Palette (Kickly Emerald & Crimson Sports Graphic Theme)
BG_TEAL = (24, 110, 94)          # Deep Emerald Teal (#186e5e)
CARD_BLACK = (12, 16, 23)        # Jet Black (#0c1017)
TIME_MAGENTA = (230, 28, 92)     # Electric Magenta/Crimson (#e61c5c)
GOLD_TEXT = (255, 215, 0)        # Gold Accent (#ffd700)
WHITE_TEXT = (255, 255, 255)     # Pure White
MUTED_TEXT = (195, 230, 220)     # Light Teal Muted Text
CYAN_ACCENT = (56, 189, 248)     # Sky Blue (#38bdf8)

LEAGUE_LOGOS_DIR = os.path.join(os.path.dirname(__file__), "assets", "league_logos")

def load_league_logo_image(platform: str, target_height: int = 22) -> Optional[Image.Image]:
    """Loads local official league logo image (VPL, VPG, LPM) scaled to exact target height (5:5:5 visual ratio)."""
    platform_upper = platform.upper()
    filename = None
    scale_multiplier = 1.0

    if "VPL" in platform_upper:
        filename = "vpl_logo.png"
        scale_multiplier = 1.0
    elif "VPG" in platform_upper:
        filename = "vpg_logo.png"
        scale_multiplier = 0.90  # Finely tune VPG down from 5.5 to 5.0 for exact equal visual volume
    elif "LPM" in platform_upper:
        filename = "lpm_logo.png"
        scale_multiplier = 1.0

    if filename:
        path = os.path.join(LEAGUE_LOGOS_DIR, filename)
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                # Auto-crop transparent padding so all 3 logos scale at equal visual bounds
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                
                adjusted_target_h = int(target_height * scale_multiplier)
                aspect = img.width / img.height
                target_width = int(adjusted_target_h * aspect)
                return img.resize((target_width, adjusted_target_h), Image.Resampling.LANCZOS)
            except Exception:
                pass
    return None

FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

def load_system_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Loads system or bundled truetype font across Mac, Windows, and Linux."""
    # 1. Local bundled project fonts (guarantees identical output across all OS)
    bundled_filename = "ArialBold.ttf" if bold else "Arial.ttf"
    bundled_path = os.path.join(FONTS_DIR, bundled_filename)
    if os.path.exists(bundled_path):
        try:
            return ImageFont.truetype(bundled_path, size=size)
        except Exception:
            pass

    # 2. Windows & Mac System Font Fallbacks
    font_paths = [
        # Windows
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
        # Mac / Unix
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Futura.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()

LOCAL_IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "logo_cache", "images")
os.makedirs(LOCAL_IMAGE_CACHE_DIR, exist_ok=True)

def download_image(url: str, default_size: tuple = (140, 140), team_name: str = "") -> Image.Image:
    """Loads team logo from local disk image cache or downloads & saves to local disk as PNG."""
    safe_key = None
    if team_name:
        safe_key = re.sub(r'[^a-zA-Z0-9]+', '_', team_name.lower().strip())
    elif url:
        safe_key = re.sub(r'[^a-zA-Z0-9]+', '_', url.split('/')[-1])

    if safe_key:
        local_path = os.path.join(LOCAL_IMAGE_CACHE_DIR, f"{safe_key}.png")
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            try:
                img = Image.open(local_path).convert("RGBA")
                img.thumbnail(default_size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", default_size, (0, 0, 0, 0))
                offset = ((default_size[0] - img.width) // 2, (default_size[1] - img.height) // 2)
                canvas.paste(img, offset, img)
                return canvas
            except Exception:
                pass

    if not url or not url.startswith("http"):
        return create_placeholder_shield(default_size)
        
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            raw_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
            if safe_key:
                try:
                    local_path = os.path.join(LOCAL_IMAGE_CACHE_DIR, f"{safe_key}.png")
                    raw_img.save(local_path, "PNG")
                except Exception:
                    pass

            img = raw_img.copy()
            img.thumbnail(default_size, Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", default_size, (0, 0, 0, 0))
            offset = ((default_size[0] - img.width) // 2, (default_size[1] - img.height) // 2)
            canvas.paste(img, offset, img)
            return canvas
    except Exception:
        pass
    return create_placeholder_shield(default_size)

def create_placeholder_shield(size: tuple = (140, 140)) -> Image.Image:
    """Generates default vector shield."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    points = [(w // 2, 4), (w - 6, 16), (w - 10, h - 18), (w // 2, h - 4), (10, h - 18), (6, 16)]
    draw.polygon(points, fill=(30, 41, 59, 255), outline=(100, 116, 139, 255), width=2)
    return img

def draw_halftone_dots(draw: ImageDraw.ImageDraw, bounds: tuple, color: tuple, spacing: int = 16, dot_radius: int = 3):
    """Renders retro halftone dot grid overlay."""
    x0, y0, x1, y1 = bounds
    for x in range(x0, x1, spacing):
        for y in range(y0, y1, spacing):
            draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=color)

def generate_matchday_poster(club_name: str, matches: List[Match], output_path: str = "matchday_poster.png") -> str:
    """
    Generates a 1080x1080 Kickly-style matchday poster with 12-hour kickoff times (e.g. 11:00),
    close top-left logo text positioning, and clean official schedule footer.
    """
    width = 1080
    height = 1080
    
    poster = Image.new("RGBA", (width, height), BG_TEAL)
    draw = ImageDraw.Draw(poster)
    
    # 1. Background Geometric Graphic Accents
    draw_halftone_dots(draw, (0, height - 240, 160, height), (255, 255, 255, 30), spacing=16, dot_radius=3)
    draw.polygon([(0, height - 280), (90, height), (0, height)], fill=TIME_MAGENTA)
    draw.polygon([(0, height - 190), (50, height), (0, height)], fill=(255, 255, 255, 220))
    
    draw.polygon([(width - 200, 0), (width, 0), (width, 240), (width - 120, 240)], fill=TIME_MAGENTA)
    draw.polygon([(width - 90, 0), (width, 0), (width, 180)], fill=(255, 255, 255, 230))
    
    chevron_x = width - 110
    chevron_y = height - 180
    for i in range(3):
        cy = chevron_y + i * 40
        draw.polygon([
            (chevron_x, cy + 25), (chevron_x + 35, cy), (chevron_x + 70, cy + 25),
            (chevron_x + 70, cy + 38), (chevron_x + 35, cy + 13), (chevron_x, cy + 38)
        ], fill=(255, 255, 255, 220))

    # Fonts
    font_header = load_system_font(64, bold=True)
    font_sub_header = load_system_font(20, bold=True)
    font_club_name = load_system_font(30, bold=True)
    font_date_comp = load_system_font(16, bold=True)
    font_team = load_system_font(23, bold=True)
    font_time = load_system_font(28, bold=True)
    font_footer = load_system_font(18, bold=True)

    from logo_cache import logo_cache

    # 1. Top Left: Virtua CF Crest (140x140px at X=20) + Tight Text Positioning (gap = 2px)
    logo_w, logo_h = 140, 140
    logo_x, logo_y = 20, 15
    virtua_logo_url = logo_cache.get_logo(club_name)
    virtua_crest = download_image(virtua_logo_url, default_size=(logo_w, logo_h), team_name=club_name)
    poster.paste(virtua_crest, (logo_x, logo_y), virtua_crest)
    
    # Text brought tight to logo (gap = 2px, X = 162px)
    text_x = logo_x + logo_w + 2
    text_y = logo_y + logo_h // 2
    draw.text((text_x, text_y), club_name.upper(), fill=WHITE_TEXT, font=font_club_name, anchor="lm")

    # 2. Top Right Header ("FIXTURES" + "MATCHDAY SCHEDULE") - Centered away from right red graphic shape
    draw.text((width // 2 + 40, 38), "F I X T U R E S", fill=WHITE_TEXT, font=font_header, anchor="ma")
    draw.text((width // 2 + 40, 112), "MATCHDAY SCHEDULE", fill=MUTED_TEXT, font=font_sub_header, anchor="ma")
    
    if not matches:
        draw.text((width // 2, height // 2), f"No upcoming matches for {club_name}", fill=WHITE_TEXT, font=font_team, anchor="ma")
    else:
        num_matches = len(matches)
        row_height = 68
        row_gap = 42
        start_y = 168
        
        norm_club = re.sub(r'\W+', '', club_name.lower())
        
        for idx, m in enumerate(matches, 1):
            y_base = start_y + (idx - 1) * (row_height + row_gap)
            
            # 1. Row Header (Left: Official League Logo + Competition Name, Center: Date)
            date_str = m.match_time.strftime("%a %d %b").upper()
            comp_str = f"{m.competition.upper()} ({m.platform})"
            
            # Center Date Header
            draw.text((width // 2, y_base + 2), date_str, fill=MUTED_TEXT, font=font_date_comp, anchor="ma")
            
            # Left Official League Badge Image (matching text height 22px) + Competition Text
            l_logo = load_league_logo_image(m.platform, target_height=22)
            if l_logo:
                poster.paste(l_logo, (105, y_base - 1), l_logo)
                draw.text((105 + l_logo.width + 10, y_base + 2), comp_str, fill=WHITE_TEXT, font=font_date_comp, anchor="la")
            else:
                draw.text((105, y_base + 2), comp_str, fill=WHITE_TEXT, font=font_date_comp, anchor="la")
                
            # 2. Main Match Bar (3-Part Horizontal Construction)
            bar_y = y_base + 24
            bar_w = 870
            bar_x = (width - bar_w) // 2  # 105px margin
            
            time_box_w = 144
            team_box_w = (bar_w - time_box_w) // 2  # 363px each side
            
            left_box_rect = [(bar_x, bar_y), (bar_x + team_box_w, bar_y + row_height)]
            time_box_rect = [(bar_x + team_box_w, bar_y), (bar_x + team_box_w + time_box_w, bar_y + row_height)]
            right_box_rect = [(bar_x + team_box_w + time_box_w, bar_y), (bar_x + bar_w, bar_y + row_height)]
            
            # Draw Black Team Boxes & Magenta Center Time Box
            draw.rectangle(left_box_rect, fill=CARD_BLACK)
            draw.rectangle(time_box_rect, fill=TIME_MAGENTA)
            draw.rectangle(right_box_rect, fill=CARD_BLACK)
            
            # Resolve Team Crest Logos (52x52px)
            home_logo_url = logo_cache.get_logo(m.home_team) or m.home_logo
            away_logo_url = logo_cache.get_logo(m.away_team) or m.away_logo
            
            h_img = download_image(home_logo_url, default_size=(52, 52), team_name=m.home_team)
            a_img = download_image(away_logo_url, default_size=(52, 52), team_name=m.away_team)
            
            # Left Box Content (Home Team: Logo at Left X=bar_x+12, Name Right-Aligned)
            poster.paste(h_img, (bar_x + 12, bar_y + 8), h_img)
            h_name = m.home_team.upper()
            h_short = h_name if len(h_name) <= 15 else h_name[:13] + ".."
            
            is_home_club = norm_club in re.sub(r'\W+', '', m.home_team.lower())
            h_color = GOLD_TEXT if is_home_club else WHITE_TEXT
            draw.text((bar_x + team_box_w - 18, bar_y + row_height // 2), h_short, fill=h_color, font=font_team, anchor="rm")
            
            # Center Box Content (Kickoff Time in 12-hour format without AM/PM: e.g. 11:00)
            time_hm_12 = m.match_time.strftime("%I:%M").lstrip("0")
            draw.text((bar_x + team_box_w + time_box_w // 2, bar_y + row_height // 2), time_hm_12, fill=WHITE_TEXT, font=font_time, anchor="mm")
            
            # Right Box Content (Away Team: Logo at Right X=bar_x+bar_w-64, Name Left-Aligned)
            a_name = m.away_team.upper()
            a_short = a_name if len(a_name) <= 15 else a_name[:13] + ".."
            is_away_club = norm_club in re.sub(r'\W+', '', m.away_team.lower())
            a_color = GOLD_TEXT if is_away_club else WHITE_TEXT
            draw.text((bar_x + team_box_w + time_box_w + 18, bar_y + row_height // 2), a_short, fill=a_color, font=font_team, anchor="lm")
            poster.paste(a_img, (bar_x + bar_w - 64, bar_y + 8), a_img)

    # 3. Footer Section (2x Size Footer League Logos + Clean Official Schedule Text)
    target_footer_h = 105
    vpl_logo = load_league_logo_image("VPL", target_height=target_footer_h)
    vpg_logo = load_league_logo_image("VPG", target_height=target_footer_h)
    lpm_logo = load_league_logo_image("LPM", target_height=target_footer_h)
    
    footer_logo_y = height - 150
    
    logos = [img for img in [vpl_logo, vpg_logo, lpm_logo] if img]
    if logos:
        spacing = 60
        total_w = sum(img.width for img in logos) + spacing * (len(logos) - 1)
        start_x = (width - total_w) // 2
        
        curr_x = start_x
        for img in logos:
            poster.paste(img, (curr_x, footer_logo_y + (target_footer_h - img.height) // 2), img)
            curr_x += img.width + spacing

    # Clean Official Matchday Schedule Footer Text
    footer_text = "OFFICIAL MATCHDAY SCHEDULE"
    draw.text((width // 2, height - 28), footer_text, fill=MUTED_TEXT, font=font_footer, anchor="ma")

    poster.save(output_path, "PNG")
    logger.info(f"Successfully generated updated Kickly poster graphic at {output_path}")
    return output_path
