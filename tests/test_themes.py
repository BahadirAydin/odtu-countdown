"""
Tests for the theme system: theme selection, color validation, and draw hooks.
"""

from PIL import Image, ImageDraw

from src.themes import get_theme, CYBER_THEME, SPRING_THEME
from src.themes.base import Theme


class TestGetTheme:
    def test_guz_returns_cyber(self):
        assert get_theme("guz") is CYBER_THEME

    def test_bahar_returns_spring(self):
        assert get_theme("bahar") is SPRING_THEME

    def test_unknown_falls_back_to_cyber(self):
        assert get_theme("yaz") is CYBER_THEME

    def test_default_is_cyber(self):
        assert get_theme() is CYBER_THEME


class TestThemeProperties:
    def test_cyber_name(self):
        assert CYBER_THEME.name == "cyber"

    def test_spring_name(self):
        assert SPRING_THEME.name == "spring"

    def test_resolved_accent_color_when_set(self):
        """Spring theme has explicit accent_color — should return it."""
        assert SPRING_THEME.accent_color is not None
        assert SPRING_THEME.resolved_accent_color == SPRING_THEME.accent_color

    def test_resolved_accent_color_fallback(self):
        """Cyber theme has no accent_color — should fall back to bar_fill_color."""
        assert CYBER_THEME.accent_color is None
        assert CYBER_THEME.resolved_accent_color == CYBER_THEME.bar_fill_color


class TestThemeColorValidation:
    """Validate that all theme color tuples are well-formed RGB."""

    COLOR_FIELDS = [
        "bg_color",
        "bar_bg_color",
        "bar_fill_color",
        "bar_fill_highlight",
        "border_color",
        "text_color",
        "text_shadow_color",
        "grid_line_color",
        "milestone_glow",
    ]

    def _assert_valid_rgb(self, color, field_name, theme_name):
        assert isinstance(color, tuple), f"{theme_name}.{field_name} is not a tuple"
        assert (
            len(color) == 3
        ), f"{theme_name}.{field_name} has {len(color)} elements, expected 3"
        for i, val in enumerate(color):
            assert (
                0 <= val <= 255
            ), f"{theme_name}.{field_name}[{i}] = {val} out of 0-255"

    def test_cyber_colors_valid(self):
        for field in self.COLOR_FIELDS:
            self._assert_valid_rgb(getattr(CYBER_THEME, field), field, "cyber")

    def test_spring_colors_valid(self):
        for field in self.COLOR_FIELDS:
            self._assert_valid_rgb(getattr(SPRING_THEME, field), field, "spring")

    def test_spring_accent_color_valid(self):
        self._assert_valid_rgb(SPRING_THEME.accent_color, "accent_color", "spring")


class TestSpringDrawHooks:
    """Spring theme draw hooks should execute without error on a real image."""

    def test_draw_decorations_runs(self):
        img = Image.new("RGB", (1200, 400), SPRING_THEME.bg_color)
        draw = ImageDraw.Draw(img)
        assert SPRING_THEME.draw_decorations is not None
        # Should not raise
        SPRING_THEME.draw_decorations(draw, img, False)

    def test_draw_decorations_milestone_runs(self):
        img = Image.new("RGB", (1200, 400), SPRING_THEME.bg_color)
        draw = ImageDraw.Draw(img)
        SPRING_THEME.draw_decorations(draw, img, True)

    def test_draw_milestone_badge_runs(self):
        img = Image.new("RGB", (1200, 400), SPRING_THEME.bg_color)
        draw = ImageDraw.Draw(img)
        assert SPRING_THEME.draw_milestone_badge is not None

        from PIL import ImageFont

        def load_font(size):
            return ImageFont.load_default()

        # Should not raise
        SPRING_THEME.draw_milestone_badge(draw, 500, 300, 100, load_font)

    def test_cyber_has_no_draw_hooks(self):
        assert CYBER_THEME.draw_decorations is None
        assert CYBER_THEME.draw_milestone_badge is None
