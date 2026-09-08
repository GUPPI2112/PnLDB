import datetime
import io
import logging
from pathlib import Path
from typing import Optional, Tuple
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
from src.config import config
from src.core.models import CollectionMeta, PnLResult
from src.renderer.template_generator import create_base_template

logger = logging.getLogger(__name__)

# Fonts directory
FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Loads bundled TrueType font with fallbacks."""
    font_file = "Font-Bold.ttf" if bold else "Font-Regular.ttf"
    local_path = FONTS_DIR / font_file

    if local_path.exists():
        try:
            return ImageFont.truetype(str(local_path), size)
        except Exception:
            pass

    # System fallbacks
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
                    img = Image.open(io.BytesIO(content)).convert("RGBA")
                    return img
    except Exception as e:
        logger.warning("Could not download image from %s: %s", url, e)
    return None


def make_circular_avatar(img: Image.Image, size: int = 72, border_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Crops an image into a circle with an outline border."""
    img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)

    draw_border = ImageDraw.Draw(output)
    draw_border.ellipse((0, 0, size - 1, size - 1), outline=border_color, width=2)
    return output


def draw_placeholder_avatar(size: int = 72, letter: str = "N", bg_color: Tuple[int, int, int] = (40, 50, 70)) -> Image.Image:
    """Draws a stylish circular avatar placeholder."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size - 1, size - 1), fill=bg_color, outline=(100, 120, 150), width=2)
    font = get_font(int(size * 0.5), bold=True)
    bbox = font.getbbox(letter)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((size - w) / 2, (size - h) / 2 - 3), letter, fill=(255, 255, 255), font=font)
    return img


async def render_pnl_card(
    pnl: PnLResult,
    collection: CollectionMeta,
) -> io.BytesIO:
    """
    Renders the complete PnL Card image.
    Uses profit_card.png (Green) if profit >= 0, or loss_card.png (Red) if loss < 0.
    """
    # 1. Select template
    template_path = config.PROFIT_TEMPLATE_PATH if pnl.is_profit else config.LOSS_TEMPLATE_PATH

    width, height = 1200, 675
    if template_path.exists():
        try:
            base_card = Image.open(template_path).convert("RGBA")
            if base_card.size != (width, height):
                base_card = base_card.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.warning("Error loading template from %s: %s", template_path, e)
            base_card = create_base_template(is_profit=pnl.is_profit, width=width, height=height).convert("RGBA")
    else:
        base_card = create_base_template(is_profit=pnl.is_profit, width=width, height=height).convert("RGBA")

    draw = ImageDraw.Draw(base_card)

    # Color palette
    if pnl.is_profit:
        accent_color = (0, 230, 118)       # #00E676 Vibrant Green
        pill_bg = (0, 230, 118, 40)
        pill_border = (0, 230, 118, 180)
    else:
        accent_color = (255, 59, 48)       # #FF3B30 Vibrant Red
        pill_bg = (255, 59, 48, 40)
        pill_border = (255, 59, 48, 180)

    white = (255, 255, 255)
    gray_light = (200, 208, 220)
    gray_muted = (130, 140, 160)

    # --- 1. HEADER SECTION ---
    # Collection Logo
    avatar_size = 72
    avatar_img = None
    if collection.image_url:
        avatar_raw = await download_image(collection.image_url)
        if avatar_raw:
            avatar_img = make_circular_avatar(avatar_raw, size=avatar_size, border_color=accent_color)

    if not avatar_img:
        first_letter = (collection.name[:1] if collection.name else "N").upper()
        avatar_img = draw_placeholder_avatar(size=avatar_size, letter=first_letter)

    base_card.paste(avatar_img, (55, 45), mask=avatar_img)

    # Collection Name
    font_name = get_font(30, bold=True)
    display_name = collection.name if len(collection.name) <= 28 else collection.name[:26] + "..."
    draw.text((145, 48), display_name, fill=white, font=font_name)

    # Badges subheader: Chain Pill + Wallet Pill
    font_badge = get_font(15, bold=True)
    
    # Chain Badge
    chain_cfg = config.get_chain_config(pnl.chain)
    chain_label = chain_cfg.display_name if chain_cfg else pnl.chain.capitalize()
    chain_bbox = font_badge.getbbox(chain_label)
    chain_w = chain_bbox[2] - chain_bbox[0] + 20
    
    draw.rounded_rectangle([145, 90, 145 + chain_w, 115], radius=6, fill=(35, 45, 65), outline=(70, 85, 115), width=1)
    draw.text((155, 94), chain_label, fill=gray_light, font=font_badge)

    # Wallet Badge
    wallet_label = f"Wallet: {pnl.shortened_wallet}"
    wallet_bbox = font_badge.getbbox(wallet_label)
    wallet_w = wallet_bbox[2] - wallet_bbox[0] + 20
    wallet_x = 145 + chain_w + 10

    draw.rounded_rectangle([wallet_x, 90, wallet_x + wallet_w, 115], radius=6, fill=(25, 32, 45), outline=(50, 60, 80), width=1)
    draw.text((wallet_x + 10, 94), wallet_label, fill=gray_muted, font=font_badge)


    # --- 2. HERO PNL SECTION (y=140..310) ---
    font_hero_label = get_font(16, bold=True)
    font_hero_val = get_font(52, bold=True)
    font_roi_pill = get_font(24, bold=True)

    # "TOTAL PNL" Label
    draw.text((80, 165), "TOTAL ESTIMATED PNL", fill=gray_muted, font=font_hero_label)

    # PnL Amount (e.g. +1.4500 ETH)
    draw.text((80, 205), pnl.formatted_pnl, fill=accent_color, font=font_hero_val)

    # ROI Pill on right side of hero
    roi_text = f"{pnl.formatted_roi} ROI"
    roi_bbox = font_roi_pill.getbbox(roi_text)
    roi_tw = roi_bbox[2] - roi_bbox[0]
    roi_th = roi_bbox[3] - roi_bbox[1]
    
    roi_pill_w = roi_tw + 44
    roi_pill_h = roi_th + 26
    roi_pill_x = width - 80 - roi_pill_w
    roi_pill_y = 195

    # Draw ROI pill overlay
    roi_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    roi_draw = ImageDraw.Draw(roi_overlay)
    roi_draw.rounded_rectangle(
        [roi_pill_x, roi_pill_y, roi_pill_x + roi_pill_w, roi_pill_y + roi_pill_h],
        radius=14,
        fill=pill_bg,
        outline=pill_border,
        width=2,
    )
    base_card = Image.alpha_composite(base_card, roi_overlay)
    draw = ImageDraw.Draw(base_card)

    draw.text(
        (roi_pill_x + 22, roi_pill_y + 11),
        roi_text,
        fill=accent_color,
        font=font_roi_pill,
    )


    # --- 3. 4-CARD STATS GRID (y=340..510) ---
    box_w = 260
    box_h = 170
    spacing = (width - 100 - (box_w * 4)) / 3
    y_pos = 340

    stats_data = [
        {
            "label": "TOTAL INVESTED",
            "value": pnl.formatted_invested,
            "sub": "Mints & Marketplace Buys",
        },
        {
            "label": "TOTAL RECEIVED",
            "value": pnl.formatted_received,
            "sub": "Marketplace Sales Revenue",
        },
        {
            "label": "TRADE ACTIVITY",
            "value": f"{pnl.bought_count} Bought • {pnl.sold_count} Sold",
            "sub": "Activity Transactions",
        },
        {
            "label": "CURRENT HOLDINGS",
            "value": f"{pnl.held_count} Currently Held",
            "sub": "In Wallet Balance",
        },
    ]

    font_stat_label = get_font(13, bold=True)
    font_stat_val = get_font(21, bold=True)
    font_stat_sub = get_font(13, bold=False)

    for i, stat in enumerate(stats_data):
        x_pos = int(50 + i * (box_w + spacing))

        # Stat Label
        draw.text((x_pos + 20, y_pos + 24), stat["label"], fill=gray_muted, font=font_stat_label)

        # Stat Value
        draw.text((x_pos + 20, y_pos + 62), stat["value"], fill=white, font=font_stat_val)

        # Stat Subtitle
        draw.text((x_pos + 20, y_pos + 118), stat["sub"], fill=gray_muted, font=font_stat_sub)


    # --- 4. FOOTER ---
    font_footer = get_font(14, bold=False)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    draw.text((55, 595), "NFT PnL Bot • Realized Analytics", fill=gray_muted, font=font_footer)
    
    date_bbox = font_footer.getbbox(now_str)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text((width - 55 - date_w, 595), now_str, fill=gray_muted, font=font_footer)

    # Save to BytesIO buffer
    buffer = io.BytesIO()
    base_card.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer
