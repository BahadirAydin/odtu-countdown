"""
Tests for bot logic: tweet text generation, milestone detection, and posting flow.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.bot import check_milestone, get_tweet_text, run_post, MILESTONE_MESSAGES
from src.calendar import Semester, TZ


# ---- Tweet text generation tests ----


class TestGetTweetText:
    def test_regular_daily(self, fall_semester):
        text = get_tweet_text(42.0, fall_semester)
        assert "%42" in text
        assert fall_semester.display_name in text
        assert "\n" not in text  # No extra lines for regular daily

    def test_hundred_percent_with_flag(self, fall_semester):
        text = get_tweet_text(100.0, fall_semester, is_milestone=True)
        assert "\U0001f3c1" in text  # 🏁 flag
        assert "%100" in text

    def test_hundred_percent_uses_milestone_message(self, fall_semester):
        """After bug fix, 100% should use MILESTONE_MESSAGES[100]."""
        text = get_tweet_text(100.0, fall_semester, is_milestone=True)
        assert MILESTONE_MESSAGES[100] in text

    def test_hundred_percent_without_milestone_flag(self, fall_semester):
        """100% without is_milestone should still get the flag but no custom message."""
        text = get_tweet_text(100.0, fall_semester, is_milestone=False)
        assert "\U0001f3c1" in text
        # Should NOT have the milestone message since is_milestone=False
        assert MILESTONE_MESSAGES[100] not in text

    def test_69_milestone_nice(self, fall_semester):
        text = get_tweet_text(69.0, fall_semester, is_milestone=True)
        assert "nice" in text
        assert "%69" in text

    def test_milestone_without_custom_message(self, fall_semester):
        """Milestone at percentage without custom message should return base text."""
        text = get_tweet_text(50.0, fall_semester, is_milestone=True)
        assert "%50" in text
        # No extra lines — just the base text
        assert "\n" not in text

    def test_non_milestone(self, fall_semester):
        text = get_tweet_text(33.0, fall_semester, is_milestone=False)
        assert "%33" in text
        assert "\n" not in text

    def test_decimal_percentage(self, fall_semester):
        text = get_tweet_text(42.57, fall_semester)
        assert "%42.57" in text

    def test_zero_percentage(self, fall_semester):
        text = get_tweet_text(0.0, fall_semester)
        assert "%0" in text

    def test_contains_semester_display_name(self, spring_semester):
        text = get_tweet_text(25.0, spring_semester)
        assert spring_semester.display_name in text


# ---- Milestone detection tests ----


class TestCheckMilestone:
    MILESTONES = [10, 25, 33, 42, 50, 69, 75, 90, 100]

    def test_exact_hit(self):
        assert check_milestone(50.0, self.MILESTONES) == 50

    def test_within_tolerance(self):
        """0.4% above milestone should still match (tolerance < 0.5)."""
        assert check_milestone(50.4, self.MILESTONES) == 50

    def test_outside_tolerance(self):
        """0.5% or more away should not match."""
        assert check_milestone(50.5, self.MILESTONES) is None

    def test_no_match(self):
        assert check_milestone(55.0, self.MILESTONES) is None

    def test_hundred_milestone(self):
        assert check_milestone(100.0, self.MILESTONES) == 100

    def test_edge_case_zero(self):
        """0% is not in default milestones — should return None."""
        assert check_milestone(0.0, self.MILESTONES) is None

    def test_negative_tolerance(self):
        """0.3% below milestone should still match."""
        assert check_milestone(49.7, self.MILESTONES) == 50

    def test_empty_milestones(self):
        assert check_milestone(50.0, []) is None


# ---- Posting flow tests ----


class TestRunPost:
    @patch("src.bot.TwitterClient")
    @patch("src.bot.create_progress_image", return_value="/tmp/test.png")
    @patch("src.bot.get_current_semester")
    @patch("src.bot.load_milestones", return_value=[10, 25, 50, 100])
    def test_daily_mode(self, mock_milestones, mock_semester, mock_image, mock_twitter):
        sem = Semester(
            name="test semester",
            start=date(2025, 9, 29),
            end=date(2026, 1, 2),
            semester_type="guz",
        )
        mock_semester.return_value = sem
        now = datetime(2025, 11, 15, 19, 0, tzinfo=TZ)

        run_post(mode="daily", dry_run=False, now=now)

        mock_image.assert_called_once()
        mock_twitter.return_value.connect.assert_called_once()
        mock_twitter.return_value.post_tweet_with_image.assert_called_once()

    @patch("src.bot.TwitterClient")
    @patch("src.bot.create_progress_image", return_value="/tmp/test.png")
    @patch("src.bot.get_current_semester")
    @patch("src.bot.load_milestones", return_value=[10, 25, 50, 100])
    def test_milestone_mode(
        self, mock_milestones, mock_semester, mock_image, mock_twitter
    ):
        sem = Semester(
            name="test semester",
            start=date(2025, 9, 29),
            end=date(2026, 1, 2),
            semester_type="guz",
        )
        mock_semester.return_value = sem
        now = datetime(2025, 11, 15, 19, 0, tzinfo=TZ)

        run_post(mode="milestone", dry_run=False, now=now)

        # Image should be called with is_milestone=True
        _, kwargs = mock_image.call_args
        assert kwargs.get("is_milestone") is True

    @patch("src.bot.TwitterClient")
    @patch("src.bot.create_progress_image", return_value="/tmp/test.png")
    @patch("src.bot.get_current_semester")
    @patch("src.bot.load_milestones", return_value=[10, 25, 50, 100])
    def test_dry_run_does_not_post(
        self, mock_milestones, mock_semester, mock_image, mock_twitter
    ):
        sem = Semester(
            name="test semester",
            start=date(2025, 9, 29),
            end=date(2026, 1, 2),
            semester_type="guz",
        )
        mock_semester.return_value = sem
        now = datetime(2025, 11, 15, 19, 0, tzinfo=TZ)

        run_post(mode="daily", dry_run=True, now=now)

        mock_image.assert_called_once()
        mock_twitter.return_value.connect.assert_not_called()
        mock_twitter.return_value.post_tweet_with_image.assert_not_called()

    @patch("src.bot.TwitterClient")
    @patch("src.bot.create_progress_image")
    @patch("src.bot.get_current_semester", return_value=None)
    def test_no_active_semester(self, mock_semester, mock_image, mock_twitter):
        now = datetime(2026, 1, 20, 12, 0, tzinfo=TZ)

        run_post(mode="daily", dry_run=False, now=now)

        mock_image.assert_not_called()
        mock_twitter.return_value.connect.assert_not_called()

    @patch("src.bot.TwitterClient")
    @patch("src.bot.create_progress_image", return_value="/tmp/test.png")
    @patch("src.bot.get_current_semester")
    @patch("src.bot.load_milestones", return_value=[10, 25, 50, 100])
    def test_semester_type_passed_to_image(
        self, mock_milestones, mock_semester, mock_image, mock_twitter
    ):
        sem = Semester(
            name="test semester",
            start=date(2025, 9, 29),
            end=date(2026, 1, 2),
            semester_type="bahar",
        )
        mock_semester.return_value = sem
        now = datetime(2025, 11, 15, 19, 0, tzinfo=TZ)

        run_post(mode="daily", dry_run=True, now=now)

        _, kwargs = mock_image.call_args
        assert kwargs.get("semester_type") == "bahar"
