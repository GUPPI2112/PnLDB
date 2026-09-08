import io
import logging
from pathlib import Path
from typing import Optional, Tuple
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
from src.config import config
from src.core.models import CollectionMeta, PnLResult

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Loads bundled TrueType font with fallbacks."""
    font_file = "Font-Bold.ttf" if bold else "Font-Regular.ttf"
    local_path = FONTS_DIR / font_file

    if local_path.exists():
        try:
            return ImageFont.truetype(str(local_path), size)
        except Exception:
            pass

    fallbacks = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fb in fallbacks:
        if Path(fb).exists():
            try:
                return ImageFont.truetype(fb, size)
            except Exception:
                continue

    return ImageFont.load_default()


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
        logger.warning("Could not download image from %s: %s", url, e)
    return None


def make_squircle_avatar(
    raw_img: Optional[Image.Image] = None,
    size: int = 48,
    radius: int = 12,
    fallback_letter: str = "W",
) -> Image.Image:
    """Creates a rounded-corner squircle avatar matching pnlref format."""
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if raw_img:
        resized = ImageOps.fit(raw_img, (size, size), method=Image.Resampling.LANCZOS)
        output.paste(resized, (0, 0), mask=mask)
    else:
        # Fallback stylized avatar
        draw = ImageDraw.Draw(output)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(30, 36, 46))
        font = get_font(int(size * 0.45), bold=True)
        draw.text((size // 2 - 6, size // 2 - 12), fallback_letter, fill=(200, 210, 225), font=font)

    # Outline border
    draw_border = ImageDraw.Draw(output)
    draw_border.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, outline=(60, 70, 85), width=1)
    return output


def draw_eth_diamond(
    draw: ImageDraw.Draw,
    cx: float,
    cy: float,
    size: float = 14,
    color: Tuple[int, int, int] = (255, 255, 255),
):
    """Draws a crisp Ethereum diamond glyph matching the template reference."""
    half_h = size * 0.60
    half_w = size * 0.38
    pts = [
        (cx, cy - half_h),
        (cx + half_w, cy),
        (cx, cy + half_h),
        (cx - half_w, cy),
    ]
    draw.polygon(pts, fill=color)


async def render_pnl_card(
    pnl: PnLResult,
    collection: CollectionMeta,
) -> io.BytesIO:
    """
    Renders the exact PnL Card format based on pnltemp and pnlref.
    """
    width, height = 1024, 576

    # Choose template: priority pnltemp.png -> profit_card/loss_card -> fallback
    template_candidates = [
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
        # Fallback dark canvas
        base_card = Image.new("RGBA", (width, height), (10, 12, 16, 255))

    draw = ImageDraw.Draw(base_card)

    # Theme colors
    # Profit: #2FE695 (47, 230, 149), Loss: #FF453A (255, 69, 58)
    accent_color = (47, 230, 149) if pnl.is_profit else (255, 69, 58)
    white = (255, 255, 255)
    gray_label = (142, 149, 162)
    sep_color = (35, 42, 52)

    # --- 1. USER PROFILE (TOP LEFT) ---
    avatar_raw = None
    if collection.image_url:
        avatar_raw = await download_image(collection.image_url)

    first_letter = (collection.name[:1] if collection.name else "W").upper()
    avatar = make_squircle_avatar(avatar_raw, size=48, radius=12, fallback_letter=first_letter)
    base_card.paste(avatar, (42, 42), mask=avatar)

    font_user = get_font(22, bold=True)
    draw.text((104, 54), pnl.display_user, fill=white, font=font_user)

    # --- 2. COLLECTION SECTION ---
    font_col_label = get_font(15, bold=False)
    draw.text((42, 138), "Collection", fill=gray_label, font=font_col_label)

    # Collection Name with auto font size
    col_name = collection.name or "Unknown Collection"
    font_size = 44 if len(col_name) <= 16 else (36 if len(col_name) <= 24 else 28)
    font_col_name = get_font(font_size, bold=True)
    draw.text((42, 168), col_name, fill=white, font=font_col_name)

    # --- 3. 4-COLUMN STATS ROW ---
    font_stat_lbl = get_font(14, bold=False)
    font_stat_val = get_font(24, bold=True)

    stats = [
        {"lbl": f"Minted {pnl.minted_count}", "val": f"{pnl.minted_native:.3f}", "x": 42},
        {"lbl": f"Bought {pnl.bought_count}", "val": f"{pnl.bought_native:.3f}", "x": 165},
        {"lbl": f"Sold {pnl.sold_count}",     "val": f"{pnl.sold_native:.3f}",   "x": 285},
        {"lbl": f"Holding {pnl.held_count}",  "val": f"{pnl.held_value_native:.3f}", "x": 405},
    ]

    # Subtle vertical separators between columns
    for sep_x in [145, 265, 385]:
        draw.line([(sep_x, 272), (sep_x, 328)], fill=sep_color, width=1)

    for st in stats:
        draw.text((st["x"], 270), st["lbl"], fill=gray_label, font=font_stat_lbl)
        draw.text((st["x"], 298), st["val"], fill=white, font=font_stat_val)

        # Place diamond glyph next to value
        bbox = font_stat_val.getbbox(st["val"])
        val_w = bbox[2] - bbox[0]
        draw_eth_diamond(draw, st["x"] + val_w + 10, 313, size=14, color=white)

    # --- 4. PNL HERO SECTION ---
    font_pnl_lbl = get_font(16, bold=True)
    draw.text((42, 365), "PNL", fill=accent_color, font=font_pnl_lbl)

    font_pnl_val = get_font(54, bold=True)
    draw.text((42, 396), pnl.formatted_usd_pnl, fill=accent_color, font=font_pnl_val)

    # Subline: ( ▲ 1383%  |  +0.221 ♦ )
    font_pnl_sub = get_font(18, bold=True)
    arrow = "▲" if pnl.is_profit else "▼"
    roi_str = f"{abs(pnl.roi_percentage):.0f}%"
    native_str = pnl.formatted_native_pnl

    sub_prefix = f"( {arrow} {roi_str}  |  {native_str} "
    draw.text((42, 474), sub_prefix, fill=accent_color, font=font_pnl_sub)

    sub_bbox = font_pnl_sub.getbbox(sub_prefix)
    sub_w = sub_bbox[2] - sub_bbox[0]
    
    # Diamond in subline
    draw_eth_diamond(draw, 42 + sub_w + 5, 485, size=13, color=accent_color)
    draw.text((42 + sub_w + 14, 474), ")", fill=accent_color, font=font_pnl_sub)

    # --- 5. FOOTER ---
    font_footer = get_font(14, bold=False)
    draw.text((820, 525), "discord.gg/egodao", fill=(85, 92, 102), font=font_footer)

    # Output PNG buffer
    buffer = io.BytesIO()
    base_card.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer
