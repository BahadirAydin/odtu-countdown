"""
Shared test fixtures for the ODTU Twitter Bot test suite.
"""

from datetime import date

import pytest

from src.calendar import Semester


@pytest.fixture
def fall_semester():
    return Semester(
        name="2025-2026 guz donemi",
        start=date(2025, 9, 29),
        end=date(2026, 1, 2),
        semester_type="guz",
    )


@pytest.fixture
def spring_semester():
    return Semester(
        name="2025-2026 bahar donemi",
        start=date(2026, 2, 16),
        end=date(2026, 6, 5),
        semester_type="bahar",
    )


@pytest.fixture
def tmp_output_path(tmp_path):
    """Temporary output path for image tests."""
    return tmp_path / "test_progress.png"
