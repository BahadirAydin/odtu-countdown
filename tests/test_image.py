"""
Tests for the pixel art progress bar image generator.
"""

from pathlib import Path

from PIL import Image

from src.image import _turkish_upper, create_progress_image


# ---- Turkish uppercase tests ----


class TestTurkishUpper:
    def test_dotted_i(self):
        assert _turkish_upper("i") == "İ"

    def test_dotless_i(self):
        assert _turkish_upper("ı") == "I"

    def test_full_sentence(self):
        result = _turkish_upper("güz dönemi ilerlemesi")
        assert result == "GÜZ DÖNEMİ İLERLEMESİ"

    def test_already_uppercase(self):
        assert _turkish_upper("ABC") == "ABC"

    def test_special_chars_preserved(self):
        result = _turkish_upper("öüşçğ")
        assert result == "ÖÜŞÇĞ"

    def test_mixed_case(self):
        result = _turkish_upper("2025-2026 bahar dönemi")
        assert result == "2025-2026 BAHAR DÖNEMİ"


# ---- Image generation tests ----


class TestCreateProgressImage:
    def test_returns_valid_path(self, tmp_output_path):
        path = create_progress_image(50.0, "Test Semester", output_path=tmp_output_path)
        assert Path(path).exists()

    def test_output_is_png(self, tmp_output_path):
        path = create_progress_image(50.0, "Test Semester", output_path=tmp_output_path)
        img = Image.open(path)
        assert img.format == "PNG"

    def test_dimensions(self, tmp_output_path):
        path = create_progress_image(50.0, "Test Semester", output_path=tmp_output_path)
        img = Image.open(path)
        assert img.size == (1200, 400)

    def test_guz_theme_dark_background(self, tmp_output_path):
        """Cyber theme (guz) should have a dark background."""
        path = create_progress_image(
            50.0, "Test", semester_type="guz", output_path=tmp_output_path
        )
        img = Image.open(path)
        # Top-left corner area should be dark (bg_color is (18, 18, 30))
        # Scanlines may alter exact values, so check that it's dark (< 50 per channel)
        r, g, b = img.getpixel((0, 0))
        assert r < 50 and g < 50 and b < 50

    def test_bahar_theme_cream_background(self, tmp_output_path):
        """Spring theme (bahar) should have a cream/warm background."""
        path = create_progress_image(
            50.0, "Test", semester_type="bahar", output_path=tmp_output_path
        )
        img = Image.open(path)
        # bg_color is (250, 245, 230), scanlines disabled for spring
        r, g, b = img.getpixel((0, 0))
        assert r > 200 and g > 200 and b > 200

    def test_milestone_mode(self, tmp_output_path):
        """Milestone mode should produce a valid image without error."""
        path = create_progress_image(
            50.0, "Test", is_milestone=True, output_path=tmp_output_path
        )
        img = Image.open(path)
        assert img.size == (1200, 400)

    def test_percentage_clamped_above_100(self, tmp_output_path):
        """Percentage > 100 should be clamped — no error."""
        path = create_progress_image(150.0, "Test", output_path=tmp_output_path)
        assert Path(path).exists()

    def test_percentage_clamped_below_zero(self, tmp_output_path):
        """Negative percentage should be clamped — no error."""
        path = create_progress_image(-10.0, "Test", output_path=tmp_output_path)
        assert Path(path).exists()

    def test_zero_percentage(self, tmp_output_path):
        path = create_progress_image(0.0, "Test", output_path=tmp_output_path)
        assert Path(path).exists()

    def test_hundred_percentage(self, tmp_output_path):
        path = create_progress_image(100.0, "Test", output_path=tmp_output_path)
        assert Path(path).exists()

    def test_custom_output_path(self, tmp_path):
        custom = tmp_path / "custom_name.png"
        path = create_progress_image(42.0, "Test", output_path=custom)
        assert path == str(custom)
        assert custom.exists()
