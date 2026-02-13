"""
Tests for semester calendar logic: date loading, percentage calculation,
edge cases, and semester selection.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from src.calendar import (
    Semester,
    format_percentage,
    get_current_semester,
    get_next_semester,
    load_milestones,
    load_semesters,
    TZ,
)

# ---- Test fixtures ----


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


# ---- Semester dataclass tests ----


class TestSemester:
    def test_display_name_guz(self, fall_semester):
        assert fall_semester.display_name == "2025-2026 güz dönemi"

    def test_display_name_bahar(self, spring_semester):
        assert spring_semester.display_name == "2025-2026 bahar dönemi"

    def test_total_days(self, fall_semester):
        expected = (date(2026, 1, 2) - date(2025, 9, 29)).days
        assert fall_semester.total_days == expected

    def test_is_active_during_semester(self, fall_semester):
        mid = datetime(2025, 11, 15, 12, 0, tzinfo=TZ)
        assert fall_semester.is_active(mid) is True

    def test_is_active_before_semester(self, fall_semester):
        before = datetime(2025, 9, 1, 12, 0, tzinfo=TZ)
        assert fall_semester.is_active(before) is False

    def test_is_active_after_semester(self, fall_semester):
        after = datetime(2026, 1, 10, 12, 0, tzinfo=TZ)
        assert fall_semester.is_active(after) is False

    def test_is_active_on_start_day(self, fall_semester):
        start = datetime(2025, 9, 29, 0, 0, tzinfo=TZ)
        assert fall_semester.is_active(start) is True

    def test_is_active_on_end_day(self, fall_semester):
        end = datetime(2026, 1, 2, 23, 59, tzinfo=TZ)
        assert fall_semester.is_active(end) is True

    def test_is_upcoming(self, fall_semester):
        before = datetime(2025, 9, 1, 12, 0, tzinfo=TZ)
        assert fall_semester.is_upcoming(before) is True

    def test_is_not_upcoming_during(self, fall_semester):
        during = datetime(2025, 11, 15, 12, 0, tzinfo=TZ)
        assert fall_semester.is_upcoming(during) is False

    def test_days_until_start(self, fall_semester):
        dt = datetime(2025, 9, 27, 12, 0, tzinfo=TZ)
        assert fall_semester.days_until_start(dt) == 2


# ---- Percentage calculation tests ----


class TestProgressAt:
    def test_zero_before_start(self, fall_semester):
        before = datetime(2025, 9, 1, 12, 0, tzinfo=TZ)
        assert fall_semester.progress_at(before) == 0.0

    def test_zero_at_start(self, fall_semester):
        start = datetime(2025, 9, 29, 0, 0, tzinfo=TZ)
        assert fall_semester.progress_at(start) == 0.0

    def test_hundred_at_end(self, fall_semester):
        end = datetime(2026, 1, 2, 0, 0, tzinfo=TZ)
        assert fall_semester.progress_at(end) == 100.0

    def test_hundred_after_end(self, fall_semester):
        after = datetime(2026, 1, 10, 12, 0, tzinfo=TZ)
        assert fall_semester.progress_at(after) == 100.0

    def test_never_exceeds_hundred(self, fall_semester):
        far_future = datetime(2026, 6, 1, 12, 0, tzinfo=TZ)
        assert fall_semester.progress_at(far_future) == 100.0

    def test_never_below_zero(self, fall_semester):
        far_past = datetime(2020, 1, 1, 12, 0, tzinfo=TZ)
        assert fall_semester.progress_at(far_past) == 0.0

    def test_approximately_fifty_at_midpoint(self, fall_semester):
        start_dt = datetime.combine(
            fall_semester.start, datetime.min.time(), tzinfo=TZ
        )
        end_dt = datetime.combine(
            fall_semester.end, datetime.min.time(), tzinfo=TZ
        )
        mid = start_dt + (end_dt - start_dt) / 2
        pct = fall_semester.progress_at(mid)
        assert 49.9 <= pct <= 50.1

    def test_monotonically_increasing(self, fall_semester):
        """Percentage should always increase as time passes."""
        from datetime import timedelta

        start_dt = datetime.combine(
            fall_semester.start, datetime.min.time(), tzinfo=TZ
        )
        prev = 0.0
        for day in range(fall_semester.total_days + 1):
            now = start_dt + timedelta(days=day)
            pct = fall_semester.progress_at(now)
            assert pct >= prev, f"Day {day}: {pct} < {prev}"
            prev = pct

    def test_naive_datetime_gets_tz(self, fall_semester):
        """Naive datetime should be treated as Istanbul time."""
        naive = datetime(2025, 11, 15, 12, 0)
        aware = datetime(2025, 11, 15, 12, 0, tzinfo=TZ)
        assert fall_semester.progress_at(naive) == fall_semester.progress_at(aware)

    def test_percentage_precision(self, fall_semester):
        """Percentage should have at most 2 decimal places."""
        mid = datetime(2025, 11, 1, 14, 30, tzinfo=TZ)
        pct = fall_semester.progress_at(mid)
        # Should be rounded to 2 decimal places
        assert pct == round(pct, 2)


# ---- Milestone datetime tests ----


class TestMilestoneDatetime:
    def test_milestone_zero(self, fall_semester):
        dt = fall_semester.milestone_datetime(0)
        assert dt.date() == fall_semester.start

    def test_milestone_hundred(self, fall_semester):
        dt = fall_semester.milestone_datetime(100)
        assert dt.date() == fall_semester.end

    def test_milestone_fifty_is_midpoint(self, fall_semester):
        dt = fall_semester.milestone_datetime(50)
        start_dt = datetime.combine(
            fall_semester.start, datetime.min.time(), tzinfo=TZ
        )
        end_dt = datetime.combine(
            fall_semester.end, datetime.min.time(), tzinfo=TZ
        )
        expected_mid = start_dt + (end_dt - start_dt) / 2
        # Allow 1 second tolerance due to rounding
        diff = abs((dt - expected_mid).total_seconds())
        assert diff < 1

    def test_milestone_ordering(self, fall_semester):
        """Milestone datetimes should be in chronological order."""
        milestones = [10, 25, 33, 42, 50, 69, 75, 90, 100]
        prev = fall_semester.milestone_datetime(0)
        for m in milestones:
            dt = fall_semester.milestone_datetime(m)
            assert dt > prev, f"Milestone {m}% is not after previous"
            prev = dt


# ---- Format percentage tests ----


class TestFormatPercentage:
    def test_whole_number(self):
        assert format_percentage(50.0) == "50"

    def test_decimal(self):
        assert format_percentage(42.57) == "42.57"

    def test_zero(self):
        assert format_percentage(0.0) == "0"

    def test_hundred(self):
        assert format_percentage(100.0) == "100"

    def test_single_decimal(self):
        assert format_percentage(33.3) == "33.3"


# ---- Config loading tests ----


class TestConfigLoading:
    def test_load_semesters_from_real_config(self):
        """Test loading from the actual project config."""
        semesters = load_semesters()
        assert len(semesters) > 0
        for sem in semesters:
            assert sem.start < sem.end
            assert sem.semester_type in ("guz", "bahar")

    def test_semesters_sorted_by_start(self):
        semesters = load_semesters()
        for i in range(1, len(semesters)):
            assert semesters[i].start > semesters[i - 1].start

    def test_load_milestones(self):
        milestones = load_milestones()
        assert len(milestones) > 0
        assert all(isinstance(m, int) for m in milestones)
        assert milestones == sorted(milestones)
        assert 100 in milestones


# ---- Semester selection tests ----


class TestGetCurrentSemester:
    def test_during_fall(self):
        now = datetime(2025, 11, 15, 12, 0, tzinfo=TZ)
        sem = get_current_semester(now=now)
        assert sem is not None
        assert sem.semester_type == "guz"

    def test_during_spring(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=TZ)
        sem = get_current_semester(now=now)
        assert sem is not None
        assert sem.semester_type == "bahar"

    def test_between_semesters(self):
        now = datetime(2026, 1, 20, 12, 0, tzinfo=TZ)
        sem = get_current_semester(now=now)
        assert sem is None

    def test_one_day_before_start(self):
        """Should return semester if within 1 day of start."""
        now = datetime(2025, 9, 28, 12, 0, tzinfo=TZ)
        sem = get_current_semester(now=now)
        assert sem is not None
        assert sem.semester_type == "guz"

    def test_two_days_before_start(self):
        """Should return None if more than 1 day before start."""
        now = datetime(2025, 9, 27, 0, 0, tzinfo=TZ)
        sem = get_current_semester(now=now)
        assert sem is None


class TestGetNextSemester:
    def test_between_semesters(self):
        now = datetime(2026, 1, 20, 12, 0, tzinfo=TZ)
        sem = get_next_semester(now=now)
        assert sem is not None
        assert sem.semester_type == "bahar"

    def test_during_semester(self):
        now = datetime(2025, 11, 15, 12, 0, tzinfo=TZ)
        sem = get_next_semester(now=now)
        # Should return the next one after the current
        assert sem is not None
        assert sem.start > now.date()
