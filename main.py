"""
ODTU Twitter Bot - Semester Progress Tracker

Posts daily progress updates and milestone tweets for ODTU academic semesters.

Usage:
    python main.py                  # Post daily update
    python main.py --milestone      # Post milestone update
    python main.py --dry-run        # Generate image + text but don't post
    python main.py --status         # Print current status
    python main.py --generate-image # Generate image only (no Twitter)
"""

import argparse
import logging
import sys

from src.bot import print_status, run_post


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="ODTU semester progress Twitter bot.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate image and text but don't post to Twitter.",
    )
    parser.add_argument(
        "--milestone",
        action="store_true",
        help="Post as a milestone tweet (special formatting).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current semester status and exit.",
    )
    parser.add_argument(
        "--generate-image",
        action="store_true",
        help="Only generate the progress image (no Twitter connection needed).",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.generate_image:
        from src.calendar import get_current_semester, TZ
        from src.image import create_progress_image
        from datetime import datetime

        now = datetime.now(tz=TZ)
        semester = get_current_semester(now=now)
        if semester is None:
            print("No active semester.")
            sys.exit(1)

        percentage = semester.progress_at(now)
        path = create_progress_image(
            percentage=percentage,
            semester_name=semester.display_name,
        )
        print(f"Image saved to: {path}")
        return

    mode = "milestone" if args.milestone else "daily"
    run_post(mode=mode, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
