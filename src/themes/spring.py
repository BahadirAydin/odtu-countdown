"""
Spring theme: ODTU campus spring / Bahar Senliği inspired.

Bright warm background, campus greens, golden sunlight accents,
festival banner-style decorations. Used for bahar (spring) semesters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.themes.base import Theme

if TYPE_CHECKING:
    from PIL import Image, ImageDraw


# --- Custom decoration hooks ---

def _draw_spring_decorations(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    is_milestone: bool,
) -> None:
    """
    Draw festival-inspired decorations: bunting flags along the top border
    and small flower/leaf pixel art in corners.
    """
    width = img.width
    border_inset = 15

    # --- Bunting flags (festival banner triangles along top) ---
    flag_colors = [
        (74, 124, 46),   # Campus green
        (218, 165, 32),  # Golden
        (180, 80, 60),   # Warm terracotta
        (74, 124, 46),   # Campus green
        (100, 160, 70),  # Lighter green
    ]
    flag_y_start = border_inset + 2
    flag_height = 14
    flag_width = 16
    flag_gap = 8
    total_flag = flag_width + flag_gap

    # Draw flags across the top
    start_x = border_inset + 20
    end_x = width - border_inset - 20
    i = 0
    x = start_x
    while x + flag_width < end_x:
        color = flag_colors[i % len(flag_colors)]
        # Triangle pointing down
        draw.polygon(
            [
                (x, flag_y_start),
                (x + flag_width, flag_y_start),
                (x + flag_width // 2, flag_y_start + flag_height),
            ],
            fill=color,
        )
        x += total_flag
        i += 1

    # Bunting string connecting flags
    draw.line(
        [(start_x, flag_y_start), (x - flag_gap, flag_y_start)],
        fill=(100, 80, 50),
        width=1,
    )

    # --- Corner leaf/flower pixels ---
    _draw_corner_leaf(draw, border_inset + 2, img.height - border_inset - 18, is_milestone)
    _draw_corner_leaf(draw, width - border_inset - 18, img.height - border_inset - 18, is_milestone, flip=True)


def _draw_corner_leaf(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    is_milestone: bool,
    flip: bool = False,
) -> None:
    """Draw a small pixel art leaf/sprout in a corner."""
    green = (74, 124, 46)
    light_green = (120, 180, 70)
    stem = (100, 80, 50)

    if not flip:
        # Stem
        draw.rectangle([x + 6, y + 8, x + 8, y + 16], fill=stem)
        # Leaves
        draw.rectangle([x + 2, y + 4, x + 6, y + 8], fill=green)
        draw.rectangle([x + 8, y + 2, x + 12, y + 6], fill=green)
        draw.rectangle([x + 4, y + 2, x + 8, y + 6], fill=light_green)
    else:
        # Stem
        draw.rectangle([x + 8, y + 8, x + 10, y + 16], fill=stem)
        # Leaves
        draw.rectangle([x + 10, y + 4, x + 14, y + 8], fill=green)
        draw.rectangle([x + 4, y + 2, x + 8, y + 6], fill=green)
        draw.rectangle([x + 8, y + 2, x + 12, y + 6], fill=light_green)

    # Small flower dot for milestone
    if is_milestone:
        flower = (220, 100, 80)
        draw.rectangle([x + 6, y, x + 10, y + 4], fill=flower)


def _draw_spring_milestone_badge(
    draw: ImageDraw.ImageDraw,
    badge_x: int,
    badge_y: int,
    badge_w: int,
    load_font,
) -> None:
    """
    Draw a festive milestone badge: warm sunburst instead of gold glow.
    """
    font_badge = load_font(12)
    badge_text = "MILESTONE!"

    # Warm sunburst glow (terracotta/golden tones)
    glow_color = (218, 135, 32)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text(
            (badge_x + dx, badge_y + dy),
            badge_text,
            fill=glow_color,
            font=font_badge,
        )
    draw.text(
        (badge_x, badge_y),
        badge_text,
        fill=(230, 170, 40),  # Warm golden
        font=font_badge,
    )


# --- Theme definition ---

SPRING_THEME = Theme(
    name="spring",
    bg_color=(250, 245, 230),             # Warm cream/off-white
    bar_bg_color=(220, 215, 195),         # Light warm gray
    bar_fill_color=(74, 124, 46),         # ODTU campus green
    bar_fill_highlight=(120, 180, 70),    # Lighter spring green
    border_color=(180, 165, 130),         # Warm tan border
    text_color=(55, 45, 35),              # Dark warm brown text
    text_shadow_color=(250, 245, 230),    # Same as bg (subtle emboss effect)
    grid_line_color=(205, 200, 180),      # Subtle warm grid
    milestone_glow=(218, 165, 32),        # Golden sunlight
    accent_color=(218, 165, 32),          # Golden for corners/diamond
    scanline_enabled=False,               # No scanlines - bright clean look
    draw_decorations=_draw_spring_decorations,
    draw_milestone_badge=_draw_spring_milestone_badge,
)
