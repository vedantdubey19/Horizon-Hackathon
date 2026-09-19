"""Generate realistic student handwritten solution images in JPG and WebP formats."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples" / "images"
FRONTEND_SAMPLES_DIR = PROJECT_ROOT / "frontend" / "public" / "samples" / "images"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Load fonts
try:
    HAND_FONT = ImageFont.truetype("/System/Library/Fonts/MarkerFelt.ttc", 30)
    HAND_FONT_LG = ImageFont.truetype("/System/Library/Fonts/MarkerFelt.ttc", 38)
    HEADER_FONT = ImageFont.truetype("/System/Library/Fonts/Geneva.ttf", 18)
except Exception:
    HAND_FONT = ImageFont.load_default()
    HAND_FONT_LG = ImageFont.load_default()
    HEADER_FONT = ImageFont.load_default()

# Color palette
PAPER_BG = (252, 249, 242)      # Warm cream paper
RULE_LINE = (215, 228, 237)      # Light blue ruled notebook lines
MARGIN_LINE = (232, 169, 162)    # Soft red margin line
HEADER_TEXT = (140, 130, 120)    # Soft gray header text
INK_BLUE = (25, 45, 110)         # Blue ballpoint pen ink
INK_BLACK = (35, 35, 40)         # Charcoal ink

WIDTH = 900
HEIGHT = 1150
LINE_HEIGHT = 44
MARGIN_X = 110
TOP_MARGIN = 160


def draw_notebook_paper() -> Image.Image:
    """Create a high-resolution lined exam sheet background."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=PAPER_BG)
    draw = ImageDraw.Draw(img)

    # Header text
    draw.text((MARGIN_X, 45), "NAME: ____________________", fill=HEADER_TEXT, font=HEADER_FONT)
    draw.text((MARGIN_X + 380, 45), "ROLL NO: ____________", fill=HEADER_TEXT, font=HEADER_FONT)
    draw.text((MARGIN_X, 85), "SUBJECT: Physics / Math", fill=HEADER_TEXT, font=HEADER_FONT)
    draw.text((MARGIN_X + 380, 85), "DATE: 2026-09-19", fill=HEADER_TEXT, font=HEADER_FONT)

    # Horizontal ruled lines
    for y in range(TOP_MARGIN, HEIGHT - 60, LINE_HEIGHT):
        draw.line([(30, y), (WIDTH - 30, y)], fill=RULE_LINE, width=1)

    # Vertical red margin line (double rule)
    draw.line([(MARGIN_X, 30), (MARGIN_X, HEIGHT - 30)], fill=MARGIN_LINE, width=2)
    draw.line([(MARGIN_X - 6, 30), (MARGIN_X - 6, HEIGHT - 30)], fill=MARGIN_LINE, width=1)

    return img


def render_sheet(
    q_num: str,
    title: str,
    steps: list[str],
    ink_color=INK_BLUE,
) -> Image.Image:
    """Render handwriting on the notebook sheet."""
    img = draw_notebook_paper()
    draw = ImageDraw.Draw(img)

    # Question number in margin
    q_y = TOP_MARGIN + 6
    draw.text((40, q_y), f"Ans {q_num}", fill=ink_color, font=HAND_FONT)

    # Problem header
    draw.text((MARGIN_X + 24, q_y), f"[{title}]", fill=(100, 100, 100), font=HEADER_FONT)

    # Render steps aligned to ruled lines
    curr_line_y = TOP_MARGIN + LINE_HEIGHT + 4
    for i, step_text in enumerate(steps, start=1):
        # Step number
        step_prefix = f"({i})  "
        draw.text((MARGIN_X + 24, curr_line_y), step_prefix + step_text, fill=ink_color, font=HAND_FONT)
        curr_line_y += LINE_HEIGHT * 2  # Space steps across notebook lines

    return img


DEMO_SHEETS = {
    "ohm_correct": {
        "q_num": "1",
        "title": "Ohm's Law (V = 12V, R = 6Ω)",
        "steps": [
            "Formula:  V = I * R",
            "Substitute:  12 = I * 6",
            "Solve:  I = 12 / 6 = 2",
            "Final Answer:  I = 2 A",
        ],
        "ink": INK_BLUE,
    },
    "ohm_wrong_sub": {
        "q_num": "1",
        "title": "Ohm's Law (Substitution Error)",
        "steps": [
            "Formula:  V = I * R",
            "Substitute:  12 = I * 24",
            "Solve:  I = 12 / 24 = 0.5",
            "Final Answer:  I = 0.5 A",
        ],
        "ink": (30, 50, 120),
    },
    "optics_wrong_sign": {
        "q_num": "7",
        "title": "Pressure & Unit Conversion (F=100N, A=50cm²)",
        "steps": [
            "Formula:  P = F / A",
            "Area:  A = 50 * 10^-4 m² = 0.005 m²",
            "Calculation:  P = 100 / 0.005 = 20000",
            "Final Answer:  20000 Pa",
        ],
        "ink": INK_BLACK,
    },
    "quad_slip": {
        "q_num": "4",
        "title": "Quadratic Equation (x² - 5x + 6 = 0)",
        "steps": [
            "Standard Form:  a = 1,  b = -5,  c = 6",
            "Quadratic Formula:  x = (-b ± √(b² - 4ac)) / (2a)",
            "Substitution:  x = (5 ± √(25 - 24)) / 2",
            "Roots:  x = 3  or  x = 2",
        ],
        "ink": INK_BLUE,
    },
}


def main():
    print(f"Generating realistic demo images in {SAMPLES_DIR}...")
    for key, data in DEMO_SHEETS.items():
        img = render_sheet(
            q_num=data["q_num"],
            title=data["title"],
            steps=data["steps"],
            ink_color=data["ink"],
        )

        # Output formats: .jpg, .webp, and .png
        targets = [
            (SAMPLES_DIR / f"{key}.jpg", "JPEG", {"quality": 92}),
            (SAMPLES_DIR / f"{key}.webp", "WEBP", {"quality": 90}),
            (SAMPLES_DIR / f"{key}.png", "PNG", {}),
            (FRONTEND_SAMPLES_DIR / f"{key}.jpg", "JPEG", {"quality": 92}),
            (FRONTEND_SAMPLES_DIR / f"{key}.webp", "WEBP", {"quality": 90}),
            (FRONTEND_SAMPLES_DIR / f"{key}.png", "PNG", {}),
        ]

        for path, fmt, params in targets:
            img.save(path, fmt, **params)
            print(f"  ✓ Saved: {path.name} ({fmt}, {path.stat().st_size // 1024} KB)")

    print("All demo JPG and WebP images successfully generated!")


if __name__ == "__main__":
    main()
