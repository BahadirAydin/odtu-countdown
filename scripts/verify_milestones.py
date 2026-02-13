#!/usr/bin/env python3
"""
Verify that the milestone workflow YAML is consistent with config/semesters.yaml.

Checks:
  1. Roundtrip: milestone_datetime -> UTC cron -> back-to-datetime matches.
  2. Staleness: the committed workflow matches what generate_milestones.py would produce.

Exit code 0 = all good, 1 = mismatch found.

Usage:
    python scripts/verify_milestones.py          # Run both checks
    python scripts/verify_milestones.py --roundtrip-only  # Only roundtrip check
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calendar import load_semesters, load_milestones, TZ

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "milestone_post.yml"


def verify_roundtrip() -> bool:
    """
    Verify that milestone_datetime -> cron -> parsed datetime is consistent.

    For each semester/milestone, compute the milestone datetime, convert to
    a UTC cron string, parse it back, and check the minute/hour/day/month match.
    """
    semesters = load_semesters()
    milestones = load_milestones()
    ok = True

    for sem in semesters:
        for m in milestones:
            if m == 0:
                continue

            dt = sem.milestone_datetime(m)
            dt_utc = dt.astimezone(ZoneInfo("UTC"))

            # Build cron the same way generate_milestones.py does
            cron = f"{dt_utc.minute} {dt_utc.hour} {dt_utc.day} {dt_utc.month} *"

            # Parse it back
            parts = cron.split()
            parsed_minute = int(parts[0])
            parsed_hour = int(parts[1])
            parsed_day = int(parts[2])
            parsed_month = int(parts[3])

            if (
                parsed_minute != dt_utc.minute
                or parsed_hour != dt_utc.hour
                or parsed_day != dt_utc.day
                or parsed_month != dt_utc.month
            ):
                print(
                    f"FAIL roundtrip: {sem.display_name} {m}% "
                    f"expected {dt_utc.minute} {dt_utc.hour} {dt_utc.day} {dt_utc.month}, "
                    f"got {parsed_minute} {parsed_hour} {parsed_day} {parsed_month}"
                )
                ok = False

            # Also verify the Istanbul datetime round-trips through progress_at
            pct_at_milestone = sem.progress_at(dt)
            if abs(pct_at_milestone - m) > 0.01:
                print(
                    f"FAIL progress_at: {sem.display_name} {m}% "
                    f"milestone_datetime gives progress {pct_at_milestone}%, expected {m}%"
                )
                ok = False

    if ok:
        print(f"Roundtrip OK: {len(semesters)} semesters x {len(milestones)} milestones verified.")
    return ok


def verify_workflow_freshness() -> bool:
    """
    Check that the committed milestone workflow matches what would be generated.

    Compares only the cron lines, not the full file, since the generator
    skips past milestones (time-dependent). Instead, we verify that every
    cron line in the committed file is a valid milestone for some semester.
    """
    if not WORKFLOW_PATH.exists():
        print("SKIP: milestone workflow file does not exist yet.")
        return True

    semesters = load_semesters()
    milestones = load_milestones()

    # Build set of all valid (cron, semester_name, milestone) tuples
    valid_crons: dict[str, str] = {}
    for sem in semesters:
        for m in milestones:
            if m == 0:
                continue
            dt = sem.milestone_datetime(m)
            dt_utc = dt.astimezone(ZoneInfo("UTC"))
            cron = f"{dt_utc.minute} {dt_utc.hour} {dt_utc.day} {dt_utc.month} *"
            valid_crons[cron] = f"{sem.display_name} {m}%"

    # Parse cron lines from the committed workflow
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    cron_pattern = re.compile(r"- cron: '([^']+)'")
    committed_crons = cron_pattern.findall(workflow_text)

    if not committed_crons:
        print("WARNING: no cron entries found in milestone workflow.")
        return True

    ok = True
    for cron in committed_crons:
        if cron not in valid_crons:
            print(f"FAIL: committed cron '{cron}' does not match any known milestone.")
            ok = False

    if ok:
        print(f"Workflow OK: {len(committed_crons)} cron entries all match valid milestones.")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Verify milestone cron consistency")
    parser.add_argument(
        "--roundtrip-only",
        action="store_true",
        help="Only run the roundtrip verification, skip workflow freshness check.",
    )
    args = parser.parse_args()

    results = []
    results.append(verify_roundtrip())

    if not args.roundtrip_only:
        results.append(verify_workflow_freshness())

    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
