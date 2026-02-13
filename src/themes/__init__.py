"""
Theme package: provides visual themes for progress bar images.

Usage:
    from src.themes import get_theme
    theme = get_theme("guz")    # Cyber theme
    theme = get_theme("bahar")  # Spring theme
"""

from src.themes.base import Theme
from src.themes.cyber import CYBER_THEME
from src.themes.spring import SPRING_THEME

_THEMES: dict[str, Theme] = {
    "guz": CYBER_THEME,
    "bahar": SPRING_THEME,
}


def get_theme(semester_type: str = "guz") -> Theme:
    """
    Get the theme for a given semester type.

    Args:
        semester_type: "guz" (fall) or "bahar" (spring).

    Returns:
        The corresponding Theme instance. Defaults to cyber if unknown.
    """
    return _THEMES.get(semester_type, CYBER_THEME)


__all__ = ["Theme", "get_theme", "CYBER_THEME", "SPRING_THEME"]
