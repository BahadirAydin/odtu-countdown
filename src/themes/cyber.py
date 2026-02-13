"""
Cyber theme: dark navy/cyan pixel art style.

This is the original theme used for güz (fall) semesters.
All values are extracted directly from the original image.py constants.
"""

from src.themes.base import Theme

CYBER_THEME = Theme(
    name="cyber",
    bg_color=(18, 18, 30),
    bar_bg_color=(35, 35, 55),
    bar_fill_color=(0, 220, 220),
    bar_fill_highlight=(100, 255, 255),
    border_color=(60, 60, 90),
    text_color=(230, 230, 250),
    text_shadow_color=(0, 0, 0),
    grid_line_color=(25, 25, 42),
    milestone_glow=(255, 220, 50),
)
