import io
import logging
import re
from pathlib import Path
from typing import Optional, Tuple
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from src.config import config
from src.core.models import CollectionMeta, PnLResult

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"


def clean_text(text: str) -> str:
    """Strips emojis and unsupported unicode to ensure clean typography without missing glyph boxes."""
    cleaned = re.sub(r"[^\x20-\x7E]+", "", text).strip()
    return cleaned if cleaned else "User"


def get_space_grotesk(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    """
    Loads Space Grotesk font with specific weight:
    - 'extrabold' / 'bold' -> SpaceGrotesk-Bold.ttf
    - 'semibold' -> SpaceGrotesk-SemiBold.ttf
    - 'medium' -> SpaceGrotesk-Medium.ttf
    - 'regular' -> SpaceGrotesk-Regular.ttf
    """
    weight_map = {
        "extrabold": "SpaceGrotesk-Bold.ttf",
        "bold": "SpaceGrotesk-Bold.ttf",
        "semibold": "SpaceGrotesk-SemiBold.ttf",
        "medium": "SpaceGrotesk-Medium.ttf",
        "regular": "SpaceGrotesk-Regular.ttf",
    }
    fname = weight_map.get(weight.lower(), "SpaceGrotesk-Bold.ttf")
    path = FONTS_DIR / fname
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    return ImageFont.load_default()


def get_jetbrains_mono(size: int, weight: str = "medium") -> ImageFont.FreeTypeFont:
    """
    Loads JetBrains Mono font for addresses, contracts, and hash data:
    - 'bold' -> JetBrainsMono-Bold.ttf
    - 'medium' -> JetBrainsMono-Medium.ttf
    - 'regular' -> JetBrainsMono-Regular.ttf
    """
    weight_map = {
        "bold": "JetBrainsMono-Bold.ttf",
        "medium": "JetBrainsMono-Medium.ttf",
        "regular": "JetBrainsMono-Regular.ttf",
    }
    fname = weight_map.get(weight.lower(), "JetBrainsMono-Medium.ttf")
    path = FONTS_DIR / fname
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_tracked_text(
    draw: ImageDraw.Draw,
    xy: Tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    letter_spacing: float = 0.0,
) -> float:
    """Draws text with generous letter spacing (tracking) for uppercase labels."""
    x, y = xy
    curr_x = x
    for char in text:
        draw.text((curr_x, y), char, font=font, fill=fill)
        bbox = font.getbbox(char)
        char_w = (bbox[2] - bbox[0]) if bbox else 8
        curr_x += char_w + letter_spacing
    return curr_x - x


async def download_image(url: str) -> Optional[Image.Image]:
    """Downloads an image asynchronously and converts to RGBA."""
    if not url:
        return None
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    return Image.open(io.BytesIO(content)).convert("RGBA")
    except Exception as e:
        logger.warning("Could not download avatar from %s: %s", url, e)
    return None


def make_squircle_avatar(
    raw_img: Optional[Image.Image] = None,
    size: int = 50,
    radius: int = 14,
    fallback_letter: str = "U",
) -> Image.Image:
    """Creates a high-contrast rounded-corner squircle avatar."""
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if raw_img:
        resized = ImageOps.fit(raw_img, (size, size), method=Image.Resampling.LANCZOS)
        output.paste(resized, (0, 0), mask=mask)
    else:
        draw = ImageDraw.Draw(output)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(24, 28, 36))
        font = get_space_grotesk(int(size * 0.45), weight="bold")
        draw.text((size // 2 - 6, size // 2 - 12), fallback_letter, fill=(200, 210, 225), font=font)

    # Subtle modern border
    draw_border = ImageDraw.Draw(output)
    draw_border.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, outline=(65, 75, 90), width=1)
    return output


def draw_arrow_triangle(
    draw: ImageDraw.Draw,
    cx: float,
    cy: float,
    size: float = 11,
    is_up: bool = True,
    color: Tuple[int, int, int] = (47, 230, 149),
):
    """Draws a crisp geometric upward (profit) or downward (loss) triangle."""
    half_w = size * 0.55
    half_h = size * 0.50
    if is_up:
        pts = [
            (cx, cy - half_h),
            (cx + half_w, cy + half_h),
            (cx - half_w, cy + half_h),
        ]
    else:
        pts = [
            (cx, cy + half_h),
            (cx + half_w, cy - half_h),
            (cx - half_w, cy - half_h),
        ]
    draw.polygon(pts, fill=color)


def draw_eth_diamond(
    draw: ImageDraw.Draw,
    cx: float,
    cy: float,
    size: float = 14,
    color: Tuple[int, int, int] = (255, 255, 255),
):
    """Draws a crisp geometric Ethereum diamond glyph."""
    half_h = size * 0.60
    half_w = size * 0.38
    pts = [
        (cx, cy - half_h),
        (cx + half_w, cy),
        (cx, cy + half_h),
        (cx - half_w, cy),
    ]
    draw.polygon(pts, fill=color)


def draw_hero_pnl_with_glow(
    image: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    is_profit: bool,
):
    """
    Renders prominent hero PnL with a subtle, luxury fintech neon glow.
    """
    x, y = xy
    glow_rgb = (47, 230, 149) if is_profit else (255, 69, 58)

    # Create an overlay for the subtle neon glow
    glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Multi-pass soft glow
    for offset in [1, 2, 3, 4]:
        alpha = int(28 / offset)
        glow_draw.text((x - offset, y), text, font=font, fill=(*glow_rgb, alpha))
        glow_draw.text((x + offset, y), text, font=font, fill=(*glow_rgb, alpha))
        glow_draw.text((x, y - offset), text, font=font, fill=(*glow_rgb, alpha))
        glow_draw.text((x, y + offset), text, font=font, fill=(*glow_rgb, alpha))

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=2.5))
    image.paste(glow_layer, (0, 0), mask=glow_layer)

    # Crisp text on top
    main_draw = ImageDraw.Draw(image)
    main_draw.text((x, y), text, font=font, fill=text_color)


async def render_pnl_card(
    pnl: PnLResult,
    collection: CollectionMeta,
) -> io.BytesIO:
    """
    Renders high-end Web3/Fintech NFT PnL card utilizing the entire canvas width.
    Features top Discord user profile & chain badge, side-by-side Collection & Hero PnL,
    full-width 4-column performance bar, and https://discord.gg/OBSIDIAN footer.
    """
    width, height = 1024, 576

    template_candidates = [
        TEMPLATES_DIR / "obsidian_template.png",
        TEMPLATES_DIR / "pnltemp.png",
        config.PROFIT_TEMPLATE_PATH if pnl.is_profit else config.LOSS_TEMPLATE_PATH,
    ]

    base_card: Optional[Image.Image] = None
    for cand in template_candidates:
        if cand.exists():
            try:
                loaded = Image.open(cand).convert("RGBA")
                if loaded.size != (width, height):
                    loaded = loaded.resize((width, height), Image.Resampling.LANCZOS)
                base_card = loaded
                break
            except Exception as e:
                logger.warning("Error loading template %s: %s", cand, e)

    if base_card is None:
        base_card = Image.new("RGBA", (width, height), (10, 12, 16, 255))

    draw = ImageDraw.Draw(base_card)

    # Premium Fintech Colors
    accent_color = (47, 230, 149) if pnl.is_profit else (255, 69, 58)
    white = (255, 255, 255)
    gray_label = (140, 148, 162)
    sep_color = (40, 48, 62)

    # --- 1. TOP HEADER (DISCORD USER ONLY & CHAIN BADGE) ---
    clean_username = clean_text(pnl.display_user)

    avatar_raw = None
    if pnl.user_avatar_url:
        avatar_raw = await download_image(pnl.user_avatar_url)
    elif collection.image_url:
        avatar_raw = await download_image(collection.image_url)

    first_letter = (clean_username[:1] if clean_username else "U").upper()
    avatar = make_squircle_avatar(avatar_raw, size=52, radius=14, fallback_letter=first_letter)
    base_card.paste(avatar, (52, 44), mask=avatar)

    # Username in Space Grotesk Bold (No ETH address below it!)
    font_user = get_space_grotesk(24, weight="bold")
    draw.text((118, 56), clean_username, fill=white, font=font_user)

    # Right: Network badge
    chain_name = (pnl.chain or "Ethereum").upper()
    font_badge = get_jetbrains_mono(12, weight="bold")
    badge_bbox = font_badge.getbbox(chain_name)
    badge_w = (badge_bbox[2] - badge_bbox[0]) if badge_bbox else 60
    bx, by = 972 - badge_w - 24, 52
    draw.rounded_rectangle([bx, by, 972, by + 28], radius=6, fill=(22, 26, 35), outline=(50, 60, 75), width=1)
    draw.text((bx + 12, by + 6), chain_name, fill=(180, 190, 205), font=font_badge)

    # --- 2. MAIN SPLIT SECTION (COLLECTION LEFT, HERO PNL RIGHT) ---
    # Left Side: COLLECTION
    font_col_lbl = get_space_grotesk(13, weight="medium")
    draw_tracked_text(draw, (52, 134), "COLLECTION", font_col_lbl, gray_label, letter_spacing=2.5)

    # Collection PFP Avatar
    col_img_raw = None
    if collection.image_url:
        col_img_raw = await download_image(collection.image_url)

    col_name = clean_text(collection.name or "NFT Collection")
    first_col_letter = (col_name[:1] if col_name else "N").upper()
    col_avatar = make_squircle_avatar(col_img_raw, size=48, radius=12, fallback_letter=first_col_letter)
    base_card.paste(col_avatar, (52, 162), mask=col_avatar)

    # Collection Name right beside the PFP
    font_size = 40 if len(col_name) <= 14 else (32 if len(col_name) <= 20 else 24)
    font_col_name = get_space_grotesk(font_size, weight="extrabold")
    draw.text((112, 164), col_name, fill=white, font=font_col_name)

    # Right Side: PNL HERO
    pnl_x = 640
    font_pnl_lbl = get_space_grotesk(13, weight="medium")
    draw_tracked_text(draw, (pnl_x, 134), "PNL", font_pnl_lbl, accent_color, letter_spacing=3.0)

    font_pnl_val = get_space_grotesk(54, weight="bold")
    draw_hero_pnl_with_glow(base_card, (pnl_x, 160), pnl.formatted_usd_pnl, font_pnl_val, accent_color, pnl.is_profit)

    # Subline right below PnL: ( ▲ 1383%  |  +0.221 ♦ )
    font_pnl_sub = get_space_grotesk(18, weight="semibold")
    roi_str = f"{abs(pnl.roi_percentage):.0f}%"
    native_str = pnl.formatted_native_pnl

    draw.text((pnl_x, 228), "(", fill=accent_color, font=font_pnl_sub)
    draw_arrow_triangle(draw, cx=pnl_x + 16, cy=239, size=11, is_up=pnl.is_profit, color=accent_color)

    mid_text = f" {roi_str}  |  {native_str} "
    draw.text((pnl_x + 26, 228), mid_text, fill=accent_color, font=font_pnl_sub)
    mid_bbox = font_pnl_sub.getbbox(mid_text)
    mid_w = (mid_bbox[2] - mid_bbox[0]) if mid_bbox else 80

    dia_x = pnl_x + 26 + mid_w + 3
    draw_eth_diamond(draw, dia_x, 239, size=12, color=accent_color)
    draw.text((dia_x + 9, 228), ")", fill=accent_color, font=font_pnl_sub)

    # --- 3. 4-COLUMN PERFORMANCE STATS (WIDE ROW ACROSS FULL WIDTH) ---
    font_stat_lbl = get_space_grotesk(12, weight="medium")
    font_stat_val = get_space_grotesk(26, weight="semibold")

    cols = [
        {"lbl": "MINTED",  "count": str(pnl.minted_count), "val": f"{pnl.minted_native:.3f}", "x": 52},
        {"lbl": "BOUGHT",  "count": str(pnl.bought_count), "val": f"{pnl.bought_native:.3f}", "x": 285},
        {"lbl": "SOLD",    "count": str(pnl.sold_count),   "val": f"{pnl.sold_native:.3f}",   "x": 515},
        {"lbl": "HOLDING", "count": str(pnl.held_count),   "val": f"{pnl.held_value_native:.3f}", "x": 750},
    ]

    stat_y = 310
    # Dividers between columns
    for sep_x in [255, 485, 715]:
        draw.line([(sep_x, stat_y + 2), (sep_x, stat_y + 58)], fill=sep_color, width=1)

    for c in cols:
        lbl_full = f"{c['lbl']} {c['count']}"
        draw_tracked_text(draw, (c["x"], stat_y), lbl_full, font_stat_lbl, gray_label, letter_spacing=1.5)
        draw.text((c["x"], stat_y + 28), c["val"], fill=white, font=font_stat_val)
        val_bbox = font_stat_val.getbbox(c["val"])
        val_w = (val_bbox[2] - val_bbox[0]) if val_bbox else 40
        draw_eth_diamond(draw, c["x"] + val_w + 10, stat_y + 44, size=14, color=white)

    # --- 4. FOOTER ---
    font_footer = get_space_grotesk(13, weight="medium")
    footer_text = "https://discord.gg/OBSIDIAN"
    foot_bbox = font_footer.getbbox(footer_text)
    foot_w = (foot_bbox[2] - foot_bbox[0]) if foot_bbox else 180
    draw.text((972 - foot_w, 532), footer_text, fill=(130, 140, 155), font=font_footer)

    buffer = io.BytesIO()
    base_card.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer


