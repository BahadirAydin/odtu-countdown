"""
Theme base: dataclass defining all visual properties for progress bar images.

Each theme provides a complete color palette and optional custom draw hooks
for decorations and milestone badges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from PIL import Image, ImageDraw

# Type alias for draw hook functions
DrawHook = Callable[["ImageDraw.ImageDraw", "Image.Image", bool], None]
MilestoneBadgeHook = Callable[
    ["ImageDraw.ImageDraw", int, int, int, "Callable[[int], object]"],
    None,
]

# RGB color type
Color = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    """
    Complete visual theme for the progress bar image.

    All color fields are RGB tuples. Optional draw hooks allow themes
    to add custom decorations beyond simple color swaps.
    """

    name: str

    # --- Core palette ---
    bg_color: Color
    bar_bg_color: Color
    bar_fill_color: Color
    bar_fill_highlight: Color
    border_color: Color
    text_color: Color
    text_shadow_color: Color
    grid_line_color: Color
    milestone_glow: Color

    # --- Accent color for corners, diamond, etc. ---
    # Defaults to bar_fill_color if not set (resolved via property)
    accent_color: Color | None = None

    # --- Scanline effect ---
    scanline_enabled: bool = True
    scanline_color: tuple[int, int, int, int] = (0, 0, 0, 15)
    scanline_spacing: int = 4

    # --- Optional custom draw hooks ---
    # Called after the border frame to draw theme-specific decorations
    draw_decorations: DrawHook | None = field(default=None, repr=False)
    # Called instead of the default milestone badge
    draw_milestone_badge: MilestoneBadgeHook | None = field(
        default=None, repr=False
    )

    @property
    def resolved_accent_color(self) -> Color:
        """Accent color, falling back to bar_fill_color."""
        return self.accent_color if self.accent_color is not None else self.bar_fill_color
