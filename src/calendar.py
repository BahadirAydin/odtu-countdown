"""
Semester calendar utilities.

Handles loading semester dates from config, determining the active semester,
and calculating progress percentage with proper timezone handling.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

logger = logging.getLogger(__name__)

TZ = ZoneInfo("Europe/Istanbul")
CONFIG_PATH = Path(__file__).parent.parent / "config" / "semesters.yaml"


@dataclass
class Semester:
    """Represents a single academic semester."""

    name: str
    start: date
    end: date
    semester_type: str  # "guz" or "bahar"

    @property
    def display_name(self) -> str:
        """Turkish display name with proper characters."""
        return self.name.replace("guz", "güz").replace("donemi", "dönemi")

    @property
    def total_days(self) -> int:
        return (self.end - self.start).days

    def progress_at(self, now: datetime | None = None) -> float:
        """
        Calculate the percentage of the semester elapsed.

        Returns a value clamped between 0.0 and 100.0.
        Uses second-level precision for accurate progress.
        """
        if now is None:
            now = datetime.now(tz=TZ)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=TZ)

        start_dt = datetime.combine(self.start, datetime.min.time(), tzinfo=TZ)
        end_dt = datetime.combine(self.end, datetime.min.time(), tzinfo=TZ)

        if now <= start_dt:
            return 0.0
        if now >= end_dt:
            return 100.0

        total_seconds = (end_dt - start_dt).total_seconds()
        elapsed_seconds = (now - start_dt).total_seconds()
        percentage = round((elapsed_seconds / total_seconds) * 100, 2)

        return min(percentage, 100.0)

    def is_active(self, now: datetime | None = None) -> bool:
        """Check if the semester is currently active (classes in session)."""
        if now is None:
            now = datetime.now(tz=TZ)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=TZ)

        today = now.date()
        return self.start <= today <= self.end

    def is_upcoming(self, now: datetime | None = None) -> bool:
        """Check if the semester hasn't started yet."""
        if now is None:
            now = datetime.now(tz=TZ)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=TZ)

        return now.date() < self.start

    def days_until_start(self, now: datetime | None = None) -> int:
        """Number of days until the semester starts. Negative if already started."""
        if now is None:
            now = datetime.now(tz=TZ)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=TZ)

        return (self.start - now.date()).days

    def milestone_datetime(self, milestone_pct: float) -> datetime:
        """
        Calculate the exact datetime when a given milestone percentage is reached.
        """
        start_dt = datetime.combine(self.start, datetime.min.time(), tzinfo=TZ)
        end_dt = datetime.combine(self.end, datetime.min.time(), tzinfo=TZ)
        total_seconds = (end_dt - start_dt).total_seconds()
        elapsed_needed = total_seconds * (milestone_pct / 100.0)
        return start_dt + timedelta(seconds=elapsed_needed)


def load_config(config_path: Path | None = None) -> dict:
    """Load the semesters.yaml config file."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_semesters(config_path: Path | None = None) -> list[Semester]:
    """Load all semesters from config."""
    config = load_config(config_path)
    semesters = []

    for entry in config.get("semesters", []):
        start = entry["start"]
        end = entry["end"]
        # Handle both string and date objects from yaml
        if isinstance(start, str):
            start = date.fromisoformat(start)
        if isinstance(end, str):
            end = date.fromisoformat(end)

        semesters.append(
            Semester(
                name=entry["name"],
                start=start,
                end=end,
                semester_type=entry["type"],
            )
        )

    # Sort by start date
    semesters.sort(key=lambda s: s.start)
    return semesters


def load_milestones(config_path: Path | None = None) -> list[int]:
    """Load milestone percentages from config."""
    config = load_config(config_path)
    milestones = config.get("milestones", [10, 25, 50, 75, 100])
    return sorted(milestones)


def get_current_semester(
    now: datetime | None = None, config_path: Path | None = None
) -> Semester | None:
    """
    Get the currently active semester, or the next upcoming semester
    if within 1 day of its start.

    Returns None if no semester is active or upcoming within 1 day.
    """
    if now is None:
        now = datetime.now(tz=TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=TZ)

    semesters = load_semesters(config_path)

    # First check for an active semester
    for sem in semesters:
        if sem.is_active(now):
            return sem

    # Then check for an upcoming semester within 1 day
    for sem in semesters:
        if sem.is_upcoming(now) and sem.days_until_start(now) <= 1:
            return sem

    return None


def get_next_semester(
    now: datetime | None = None, config_path: Path | None = None
) -> Semester | None:
    """Get the next upcoming semester (regardless of how far away)."""
    if now is None:
        now = datetime.now(tz=TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=TZ)

    semesters = load_semesters(config_path)
    for sem in semesters:
        if sem.is_upcoming(now):
            return sem

    return None


def format_percentage(percentage: float) -> str:
    """Format percentage for display: drop decimals if it's a whole number."""
    if percentage == int(percentage):
        return str(int(percentage))
    return str(percentage)
