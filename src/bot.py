"""
Bot logic: tweet text generation, posting flow, and milestone detection.
"""

import logging
from datetime import datetime

from src.calendar import (
    Semester,
    format_percentage,
    get_current_semester,
    load_milestones,
    TZ,
)
from src.image import create_progress_image
from src.twitter import TwitterClient

logger = logging.getLogger(__name__)

# Milestone percentages with special tweet text
MILESTONE_MESSAGES = {
    100: "Finallerde başarılar!",
    69: "nice",
}


def get_tweet_text(
    percentage: float,
    semester: Semester,
    is_milestone: bool = False,
) -> str:
    """
    Generate the tweet text for a given percentage and semester.

    Args:
        percentage: Current progress percentage.
        semester: Active semester object.
        is_milestone: Whether this is a milestone post.

    Returns:
        The formatted tweet text.
    """
    pct_str = format_percentage(percentage)
    base = f"\u26aa {semester.display_name} ilerlemesi: %{pct_str}"

    if percentage >= 100:
        return f"{base} \U0001f3c1\n\nFinallerde başarılar!"

    if is_milestone:
        custom_msg = MILESTONE_MESSAGES.get(int(percentage))
        if custom_msg:
            return f"{base}\n\n{custom_msg}"

    return base


def check_milestone(percentage: float, milestones: list[int]) -> int | None:
    """
    Check if the current percentage has crossed a milestone.

    Returns the milestone value if crossed (within 0.5% tolerance for
    daily posts that might slightly overshoot), or None.
    """
    for m in milestones:
        if abs(percentage - m) < 0.5:
            return m
    return None


def run_post(
    mode: str = "daily",
    dry_run: bool = False,
    now: datetime | None = None,
) -> None:
    """
    Main posting flow.

    Args:
        mode: "daily" for regular daily posts, "milestone" for milestone-triggered posts.
        dry_run: If True, generate image and log but don't actually post.
        now: Override current time (for testing).
    """
    if now is None:
        now = datetime.now(tz=TZ)

    semester = get_current_semester(now=now)
    if semester is None:
        logger.info("No active semester. Skipping post.")
        return

    percentage = semester.progress_at(now)
    milestones = load_milestones()
    milestone_hit = check_milestone(percentage, milestones)
    is_milestone = mode == "milestone" or milestone_hit is not None

    logger.info(
        "Semester: %s | Progress: %s%% | Mode: %s | Milestone: %s",
        semester.display_name,
        format_percentage(percentage),
        mode,
        milestone_hit,
    )

    # Generate image
    img_path = create_progress_image(
        percentage=percentage,
        semester_name=semester.display_name,
        is_milestone=is_milestone,
        semester_type=semester.semester_type,
    )

    # Generate tweet text
    text = get_tweet_text(percentage, semester, is_milestone=is_milestone)

    if dry_run:
        logger.info("DRY RUN - would post:")
        logger.info("  Text: %s", text)
        logger.info("  Image: %s", img_path)
        return

    # Post to Twitter
    client = TwitterClient()
    client.connect()
    client.post_tweet_with_image(text, img_path)
    logger.info("Post complete.")


def print_status(now: datetime | None = None) -> None:
    """Print current semester status without posting."""
    if now is None:
        now = datetime.now(tz=TZ)

    semester = get_current_semester(now=now)
    if semester is None:
        from src.calendar import get_next_semester

        next_sem = get_next_semester(now=now)
        if next_sem:
            days = next_sem.days_until_start(now)
            print(f"No active semester. Next: {next_sem.display_name} in {days} days.")
        else:
            print("No active or upcoming semesters configured.")
        return

    percentage = semester.progress_at(now)
    text = get_tweet_text(percentage, semester)
    milestones = load_milestones()
    milestone_hit = check_milestone(percentage, milestones)

    print(f"Semester: {semester.display_name}")
    print(f"Period: {semester.start} -> {semester.end} ({semester.total_days} days)")
    print(f"Progress: {format_percentage(percentage)}%")
    print(f"Tweet: {text}")
    if milestone_hit is not None:
        print(f"Milestone: {milestone_hit}%")
