"""
Generates clean baseline green and red template background cards (1200x675).
Users can replace these templates in assets/templates/ with their own custom designs anytime.
"""
from pathlib import Path
from PIL import Image, ImageDraw


def create_base_template(is_profit: bool, width: int = 1200, height: int = 675) -> Image.Image:
    # 1. Base dark canvas
    img = Image.new("RGBA", (width, height), (11, 15, 23, 255))
    draw = ImageDraw.Draw(img)

    # Accent colors
    # Green profit: #00E676 (0, 230, 118), Red loss: #FF3B30 (255, 59, 48)
    if is_profit:
        accent = (0, 230, 118)
        accent_dim = (0, 230, 118, 30)
        card_bg = (18, 28, 24, 230)
        card_border = (0, 230, 118, 90)
    else:
        accent = (255, 59, 48)
        accent_dim = (255, 59, 48, 30)
        card_bg = (28, 18, 20, 230)
        card_border = (255, 59, 48, 90)

    # Gradient/glow background circles
    glow_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_overlay)

    # Top-right glow
    glow_draw.ellipse([800, -100, 1300, 400], fill=(accent[0], accent[1], accent[2], 25))
    # Bottom-left glow
    glow_draw.ellipse([-100, 350, 450, 900], fill=(accent[0], accent[1], accent[2], 18))

    img = Image.alpha_composite(img, glow_overlay)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([0, 0, width, 6], fill=accent)

    # Outer border frame
    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=24, outline=card_border, width=2)

    # Hero PnL Glass Container
    draw.rounded_rectangle([50, 140, width - 50, 310], radius=18, fill=card_bg, outline=card_border, width=2)

    # Stats 4-Grid Containers
    box_w = 260
    box_h = 170
    spacing = (width - 100 - (box_w * 4)) / 3  # spacing between 4 cards
    y_pos = 340

    stat_bg = (16, 21, 30, 230)
    stat_border = (40, 48, 65, 200)

    for i in range(4):
        x_pos = int(50 + i * (box_w + spacing))
        draw.rounded_rectangle(
            [x_pos, y_pos, x_pos + box_w, y_pos + box_h],
            radius=14,
            fill=stat_bg,
            outline=stat_border,
            width=1,
        )

    return img.convert("RGB")


def generate_default_templates():
    templates_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    profit_path = templates_dir / "profit_card.png"
    loss_path = templates_dir / "loss_card.png"

    if not profit_path.exists():
        profit_img = create_base_template(is_profit=True)
        profit_img.save(profit_path, "PNG", quality=95)
        print(f"Generated default profit template: {profit_path}")

    if not loss_path.exists():
        loss_img = create_base_template(is_profit=False)
        loss_img.save(loss_path, "PNG", quality=95)
        print(f"Generated default loss template: {loss_path}")


if __name__ == "__main__":
    generate_default_templates()
