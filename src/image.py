"""
Modern pixel art progress bar image generator using Pillow.

Produces a clean pixel-grid progress bar with theming support.
Colors and decorations are provided by the active theme; core layout
and drawing logic lives here as shared code.
"""

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.themes import get_theme
from src.themes.base import Theme

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
FONT_PATH = ASSETS_DIR / "PressStart2P.ttf"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "progress_image.png"

# --- Dimensions ---
IMG_WIDTH = 1200
IMG_HEIGHT = 400
BAR_LEFT = 60
BAR_RIGHT = IMG_WIDTH - 60
BAR_TOP = 160
BAR_HEIGHT = 100
BAR_BOTTOM = BAR_TOP + BAR_HEIGHT
SEGMENT_COUNT = 20  # Number of discrete pixel blocks
SEGMENT_GAP = 4  # Gap between segments


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load the pixel font at the given size, fallback to default."""
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except (OSError, IOError):
        logger.warning("Pixel font not found at %s, using default font", FONT_PATH)
        return ImageFont.load_default()


def _draw_segment(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    filled: bool,
    theme: Theme,
    partial: float = 1.0,
) -> None:
    """
    Draw a single pixel-block segment of the progress bar.

    Args:
        draw: ImageDraw instance.
        x, y: Top-left corner of the segment.
        w, h: Width and height of the segment.
        filled: Whether this segment is in the filled portion.
        theme: Active theme for colors.
        partial: 0.0-1.0 for partially filled segments.
    """
    if not filled and partial <= 0:
        # Empty segment
        draw.rectangle([x, y, x + w, y + h], fill=theme.bar_bg_color)
        # Add subtle grid lines within empty segments
        mid_y = y + h // 2
        draw.line([(x, mid_y), (x + w, mid_y)], fill=theme.grid_line_color, width=1)
        mid_x = x + w // 2
        draw.line([(mid_x, y), (mid_x, y + h)], fill=theme.grid_line_color, width=1)
        return

    if filled and partial >= 1.0:
        # Fully filled segment
        draw.rectangle([x, y, x + w, y + h], fill=theme.bar_fill_color)
        # Add highlight on top portion for depth
        highlight_h = max(h // 4, 2)
        draw.rectangle(
            [x + 1, y + 1, x + w - 1, y + highlight_h],
            fill=theme.bar_fill_highlight,
        )
        # Add subtle inner border for pixel grid look
        draw.rectangle([x, y, x + w, y + h], outline=theme.grid_line_color, width=1)
    elif 0 < partial < 1.0:
        # Partially filled segment
        filled_w = max(int(w * partial), 1)
        # Filled part
        draw.rectangle([x, y, x + filled_w, y + h], fill=theme.bar_fill_color)
        if filled_w > 3:
            highlight_h = max(h // 4, 2)
            draw.rectangle(
                [x + 1, y + 1, x + filled_w - 1, y + highlight_h],
                fill=theme.bar_fill_highlight,
            )
        # Empty part
        if x + filled_w < x + w:
            draw.rectangle([x + filled_w, y, x + w, y + h], fill=theme.bar_bg_color)
        # Border
        draw.rectangle([x, y, x + w, y + h], outline=theme.grid_line_color, width=1)


def _turkish_upper(text: str) -> str:
    """Uppercase with Turkish locale rules (i -> İ, ı -> I)."""
    _tr_map = str.maketrans(
        {
            "i": "İ",
            "ı": "I",
            "ö": "Ö",
            "ü": "Ü",
            "ş": "Ş",
            "ç": "Ç",
            "ğ": "Ğ",
        }
    )
    return text.translate(_tr_map).upper()


def create_progress_image(
    percentage: float,
    semester_name: str = "",
    is_milestone: bool = False,
    semester_type: str = "guz",
    output_path: Path | str | None = None,
) -> str:
    """
    Create a modern pixel art progress bar image.

    Args:
        percentage: Progress percentage (0-100).
        semester_name: Semester display name for the header text.
        is_milestone: Whether this is a milestone post (adds special effects).
        semester_type: "guz" or "bahar" — selects the visual theme automatically.
        output_path: Where to save the image. Defaults to progress_image.png.

    Returns:
        The file path of the saved image as a string.
    """
    output = Path(output_path) if output_path else DEFAULT_OUTPUT
    percentage = max(0.0, min(100.0, percentage))

    theme = get_theme(semester_type)

    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), theme.bg_color)
    draw = ImageDraw.Draw(img)

    # --- Draw border frame ---
    border_inset = 15
    draw.rectangle(
        [
            border_inset,
            border_inset,
            IMG_WIDTH - border_inset,
            IMG_HEIGHT - border_inset,
        ],
        outline=theme.border_color,
        width=2,
    )

    # Corner decorations (pixel art style)
    corner_color = theme.milestone_glow if is_milestone else theme.resolved_accent_color
    corner_size = 8
    for cx, cy in [
        (border_inset, border_inset),
        (IMG_WIDTH - border_inset - corner_size, border_inset),
        (border_inset, IMG_HEIGHT - border_inset - corner_size),
        (
            IMG_WIDTH - border_inset - corner_size,
            IMG_HEIGHT - border_inset - corner_size,
        ),
    ]:
        draw.rectangle(
            [cx, cy, cx + corner_size, cy + corner_size],
            fill=corner_color,
        )

    # --- Theme-specific decorations ---
    if theme.draw_decorations is not None:
        theme.draw_decorations(draw, img, is_milestone)

    # --- Header text ---
    font_header = _load_font(18)
    if semester_name:
        header_text = _turkish_upper(semester_name)
    else:
        header_text = "SEMESTER PROGRESS"

    header_bbox = draw.textbbox((0, 0), header_text, font=font_header)
    header_w = header_bbox[2] - header_bbox[0]
    header_x = (IMG_WIDTH - header_w) // 2
    header_y = 50

    # Text shadow
    draw.text(
        (header_x + 2, header_y + 2),
        header_text,
        fill=theme.text_shadow_color,
        font=font_header,
    )
    draw.text(
        (header_x, header_y), header_text, fill=theme.text_color, font=font_header
    )

    # --- Decorative line under header ---
    line_y = header_y + 35
    line_margin = 100
    draw.line(
        [(line_margin, line_y), (IMG_WIDTH - line_margin, line_y)],
        fill=theme.border_color,
        width=1,
    )
    # Small diamond at center of line
    diamond_color = (
        theme.milestone_glow if is_milestone else theme.resolved_accent_color
    )
    diamond_cx = IMG_WIDTH // 2
    ds = 4
    draw.polygon(
        [
            (diamond_cx, line_y - ds),
            (diamond_cx + ds, line_y),
            (diamond_cx, line_y + ds),
            (diamond_cx - ds, line_y),
        ],
        fill=diamond_color,
    )

    # --- Progress bar border ---
    bar_border = 3
    draw.rectangle(
        [
            BAR_LEFT - bar_border,
            BAR_TOP - bar_border,
            BAR_RIGHT + bar_border,
            BAR_BOTTOM + bar_border,
        ],
        outline=theme.border_color,
        width=2,
    )

    # --- Draw segments ---
    total_bar_width = BAR_RIGHT - BAR_LEFT

    # 1. Calculate the standard width for segments
    # The math here is correct (N-1 gaps), but // leaves a remainder
    segment_total_width = (
        total_bar_width - (SEGMENT_COUNT - 1) * SEGMENT_GAP
    ) // SEGMENT_COUNT

    filled_segments = percentage / 100.0 * SEGMENT_COUNT

    for i in range(SEGMENT_COUNT):
        # Calculate X position
        seg_x = BAR_LEFT + i * (segment_total_width + SEGMENT_GAP)
        seg_y = BAR_TOP

        # 2. FIX: Determine width for THIS segment
        # If it is the last segment, stretch it to the exact right boundary
        # to absorb any integer division remainder.
        if i == SEGMENT_COUNT - 1:
            current_seg_w = BAR_RIGHT - seg_x
        else:
            current_seg_w = segment_total_width

        # 3. Use current_seg_w in the drawing calls below
        if i < int(filled_segments):
            # Fully filled
            _draw_segment(
                draw, seg_x, seg_y, current_seg_w, BAR_HEIGHT, True, theme, 1.0
            )
        elif i == int(filled_segments) and filled_segments % 1 > 0:
            # Partially filled
            _draw_segment(
                draw,
                seg_x,
                seg_y,
                current_seg_w,
                BAR_HEIGHT,
                True,
                theme,
                filled_segments % 1,
            )
        else:
            # Empty
            _draw_segment(
                draw, seg_x, seg_y, current_seg_w, BAR_HEIGHT, False, theme, 0.0
            )

    # --- Percentage text ---
    font_pct = _load_font(32)
    pct_display = int(percentage) if percentage == int(percentage) else percentage
    pct_text = f"{pct_display}%"

    pct_bbox = draw.textbbox((0, 0), pct_text, font=font_pct)
    pct_w = pct_bbox[2] - pct_bbox[0]
    pct_h = pct_bbox[3] - pct_bbox[1]
    pct_x = (IMG_WIDTH - pct_w) // 2
    pct_y = BAR_BOTTOM + 30

    # Shadow
    draw.text(
        (pct_x + 2, pct_y + 2), pct_text, fill=theme.text_shadow_color, font=font_pct
    )
    # Main text
    text_color = theme.milestone_glow if is_milestone else theme.text_color
    draw.text((pct_x, pct_y), pct_text, fill=text_color, font=font_pct)

    # --- Milestone badge ---
    if is_milestone and percentage > 0:
        font_badge = _load_font(12)
        badge_text = "MILESTONE!"
        badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        badge_w = badge_bbox[2] - badge_bbox[0]
        badge_x = (IMG_WIDTH - badge_w) // 2
        badge_y = pct_y + pct_h + 15

        if theme.draw_milestone_badge is not None:
            # Theme provides custom milestone badge drawing
            theme.draw_milestone_badge(draw, badge_x, badge_y, badge_w, _load_font)
        else:
            # Default glow effect: draw multiple times with slight offsets
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                draw.text(
                    (badge_x + dx, badge_y + dy),
                    badge_text,
                    fill=(255, 200, 0),
                    font=font_badge,
                )
            draw.text(
                (badge_x, badge_y),
                badge_text,
                fill=theme.milestone_glow,
                font=font_badge,
            )

    # --- Scanline effect (subtle retro touch) ---
    if theme.scanline_enabled:
        for y in range(0, IMG_HEIGHT, theme.scanline_spacing):
            draw.line([(0, y), (IMG_WIDTH, y)], fill=theme.scanline_color, width=1)

    # Save
    img.save(str(output), "PNG")
    logger.info("Progress image saved to %s (%s theme)", output, theme.name)
    return str(output)
