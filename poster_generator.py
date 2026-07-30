import os
import re
import io
import logging
from typing import List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont
from models import Match

logger = logging.getLogger("PosterGenerator")

# Color Palette (Virtua CF Signature Midnight Navy & Electric Gold Theme)
BG_NAVY = (11, 23, 35)           # Deep Midnight Navy (#0b1723)
CARD_NAVY = (19, 38, 52)         # Steel Dark Navy (#132634)
TIME_GOLD = (244, 186, 29)       # Electric Virtua Gold (#f4ba1d)
TIME_BOX_TEXT = (11, 23, 35)     # Deep Midnight Navy text on Gold box
GOLD_TEXT = (244, 186, 29)       # Virtua Gold Accent (#f4ba1d)
WHITE_TEXT = (255, 255, 255)     # Pure White
MUTED_TEXT = (140, 165, 175)     # Steel Blue Muted Text (#8ca5af)
ACCENT_GREY = (104, 123, 128)    # Steel Grey

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
    bundled_filename = "ArialBold.ttf" if bold else "Arial.ttf"
    bundled_path = os.path.join(FONTS_DIR, bundled_filename)
    if os.path.exists(bundled_path):
        try:
            return ImageFont.truetype(bundled_path, size=size)
        except Exception:
            pass

    font_paths = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
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

def crop_and_contain_logo(img: Image.Image, default_size: tuple) -> Image.Image:
    """
    Automatically crops surrounding transparent whitespace using alpha channel bounding box getchannel('A').getbbox(),
    then resizes & centers the logo within fixed default_size bounding box maintaining aspect ratio.
    """
    img = img.convert("RGBA")
    
    # 1. Crop out transparent whitespace bounds
    alpha = img.getchannel('A')
    bbox = alpha.getbbox()
    if bbox:
        img = img.crop(bbox)
    elif img.getbbox():
        img = img.crop(img.getbbox())
        
    # 2. Resize within bounding box maintaining aspect ratio
    img.thumbnail(default_size, Image.Resampling.LANCZOS)
    
    # 3. Center on transparent canvas of fixed target bounding box size
    canvas = Image.new("RGBA", default_size, (0, 0, 0, 0))
    offset = ((default_size[0] - img.width) // 2, (default_size[1] - img.height) // 2)
    canvas.paste(img, offset, img)
    return canvas

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
                img = Image.open(local_path)
                return crop_and_contain_logo(img, default_size)
            except Exception:
                pass

    if not url or not url.startswith("http"):
        return create_placeholder_shield(default_size)
        
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            raw_img = Image.open(io.BytesIO(res.content))
            if safe_key:
                try:
                    local_path = os.path.join(LOCAL_IMAGE_CACHE_DIR, f"{safe_key}.png")
                    raw_img.save(local_path, "PNG")
                except Exception:
                    pass

            return crop_and_contain_logo(raw_img, default_size)
    except Exception:
        pass
    return create_placeholder_shield(default_size)

def create_placeholder_shield(size: tuple = (140, 140)) -> Image.Image:
    """Generates default vector shield."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    points = [(w // 2, 4), (w - 6, 16), (w - 10, h - 18), (w // 2, h - 4), (10, h - 18), (6, 16)]
    draw.polygon(points, fill=(19, 38, 52, 255), outline=(244, 186, 29, 255), width=2)
    return img

def draw_halftone_dots(draw: ImageDraw.ImageDraw, bounds: tuple, color: tuple, spacing: int = 16, dot_radius: int = 3):
    """Renders retro halftone dot grid overlay."""
    x0, y0, x1, y1 = bounds
    for x in range(x0, x1, spacing):
        for y in range(y0, y1, spacing):
            draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=color)

def generate_matchday_poster(club_name: str, matches: List[Match], output_path: str = "matchday_poster.png") -> str:
    """
    Generates a 1080x1080 Kickly-style Virtua CF matchday poster matching official Navy & Gold brand identity.
    """
    width = 1080
    height = 1080
    
    poster = Image.new("RGBA", (width, height), BG_NAVY)
    draw = ImageDraw.Draw(poster)
    
    # 1. Background Geometric Graphic Accents (Virtua Gold & Steel Accents)
    draw_halftone_dots(draw, (0, height - 240, 160, height), (104, 123, 128, 40), spacing=16, dot_radius=3)
    draw.polygon([(0, height - 280), (90, height), (0, height)], fill=TIME_GOLD)
    draw.polygon([(0, height - 190), (50, height), (0, height)], fill=(255, 255, 255, 220))
    
    draw.polygon([(width - 200, 0), (width, 0), (width, 240), (width - 120, 240)], fill=TIME_GOLD)
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

    # 1. Top Header: Perfectly Centered ("FIXTURES" + "MATCHDAY SCHEDULE")
    draw.text((width // 2, 38), "F I X T U R E S", fill=WHITE_TEXT, font=font_header, anchor="ma")
    draw.text((width // 2, 112), "MATCHDAY SCHEDULE", fill=MUTED_TEXT, font=font_sub_header, anchor="ma")
    
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
            comp_str = m.competition.upper()
            
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
            
            # Draw Steel Navy Team Boxes & Virtua Gold Center Time Box
            draw.rectangle(left_box_rect, fill=CARD_NAVY)
            draw.rectangle(time_box_rect, fill=TIME_GOLD)
            draw.rectangle(right_box_rect, fill=CARD_NAVY)
            
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
            
            # Center Box Content (Kickoff Time in 12-hour format: Midnight Navy text on Gold box)
            time_hm_12 = m.match_time.strftime("%I:%M").lstrip("0")
            draw.text((bar_x + team_box_w + time_box_w // 2, bar_y + row_height // 2), time_hm_12, fill=TIME_BOX_TEXT, font=font_time, anchor="mm")
            
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
    footer_text = f"{club_name.upper()} OFFICIAL MATCHDAY SCHEDULE"
    draw.text((width // 2, height - 28), footer_text, fill=MUTED_TEXT, font=font_footer, anchor="ma")

    poster.save(output_path, "PNG")
    logger.info(f"Successfully generated updated Kickly poster graphic at {output_path}")
    return output_path
