#!/usr/bin/env python3
"""
Scrape ODTU academic calendar to extract semester start/end dates.

Parses the OIDB academic calendar page and updates config/semesters.yaml.

Usage:
    python scripts/scrape_calendar.py                    # Scrape current+next year
    python scripts/scrape_calendar.py --year 2025-2026   # Scrape specific year
    python scripts/scrape_calendar.py --dry-run          # Preview without writing

The scraper looks for these key phrases in the calendar:
    - "Derslerin Baslamasi" -> semester start date
    - "derslerin son gunu"  -> semester end date (last day of classes)
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "semesters.yaml"

BASE_URL = "https://oidb.metu.edu.tr/tr/odtu-ankara-ve-erdemli-kampuslari-{year}-akademik-takvim"

# Turkish month names -> month numbers
TURKISH_MONTHS = {
    "ocak": 1,
    "subat": 2,
    "mart": 3,
    "nisan": 4,
    "mayis": 5,
    "haziran": 6,
    "temmuz": 7,
    "agustos": 8,
    "eylul": 9,
    "ekim": 10,
    "kasim": 11,
    "aralik": 12,
    # With Turkish characters
    "şubat": 2,
    "mayıs": 5,
    "ağustos": 8,
    "eylül": 9,
    "kasım": 11,
    "aralık": 12,
}

# Pattern: "DD MONTH YYYY" or "DD MONTH"
DATE_PATTERN = re.compile(
    r"(\d{1,2})\s+("
    + "|".join(TURKISH_MONTHS.keys())
    + r")\s*(\d{4})?",
    re.IGNORECASE,
)


def _normalize_turkish(text: str) -> str:
    """Normalize Turkish characters for matching."""
    replacements = {
        "İ": "i",
        "ı": "i",
        "Ö": "o",
        "ö": "o",
        "Ü": "u",
        "ü": "u",
        "Ş": "s",
        "ş": "s",
        "Ç": "c",
        "ç": "c",
        "Ğ": "g",
        "ğ": "g",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.lower()


def _parse_date_from_text(text: str, default_year: int) -> date | None:
    """Try to extract a date from Turkish text.

    Uses the regex with IGNORECASE flag to match Turkish month names,
    then normalizes the matched month name for lookup. This avoids issues
    with Python's str.lower() producing combining characters for Turkish
    dotted capital İ (e.g. 'İ'.lower() -> 'i̇' instead of 'i').
    """
    # Search without lowering -- re.IGNORECASE handles case matching
    match = DATE_PATTERN.search(text.strip())
    if not match:
        return None

    day = int(match.group(1))
    # Normalize the matched month name for dict lookup
    month_name = _normalize_turkish(match.group(2))
    year = int(match.group(3)) if match.group(3) else default_year

    month = TURKISH_MONTHS.get(month_name)
    if month is None:
        return None

    try:
        return date(year, month, day)
    except ValueError:
        return None


def fetch_calendar(year_str: str) -> str:
    """Fetch the academic calendar HTML for a given year (e.g., '2025-2026')."""
    url = BASE_URL.format(year=year_str)
    print(f"Fetching: {url}")

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_calendar(html: str, year_str: str) -> list[dict]:
    """
    Parse the academic calendar HTML and extract semester dates.

    The ODTU academic calendar page has a consistent structure:
    - A section header line: "GÜZ DÖNEMİ" or "BAHAR DÖNEMİ VE YAZ OKULU"
    - Entries as pairs of lines: date line, then description line
    - The date line is directly above (i-1) the description line

    We look for:
    - "Derslerin Başlaması" (with the parenthetical about programs) -> start
    - "derslerin son günü" (for lisans/lisansüstü) -> end

    Returns a list of semester dicts with keys: name, start, end, type.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find the main content area
    content = soup.find("div", class_="field--name-body") or soup.find("article") or soup
    text_content = content.get_text()

    # Split into lines and process
    lines = text_content.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    semesters = []
    start_year = int(year_str.split("-")[0])
    end_year = int(year_str.split("-")[1])

    # State machine: look for semester sections and key dates
    current_section = None  # "guz" or "bahar"
    fall_start = None
    fall_end = None
    spring_start = None
    spring_end = None

    for i, line in enumerate(lines):
        normalized = _normalize_turkish(line)

        # Detect semester section headers.
        # These are standalone lines like "GÜZ DÖNEMİ" or "BAHAR DÖNEMİ VE YAZ OKULU".
        # We require short lines to avoid matching casual mentions in descriptions
        # (e.g. "Erasmus ... Bahar Dönemi içindir" on line 12).
        if len(line) < 40:
            if normalized.strip() == "guz donemi":
                current_section = "guz"
                continue
            if "bahar donemi" in normalized and "yaz okulu" in normalized:
                current_section = "bahar"
                continue

        # Look for "Derslerin Başlaması" (classes start).
        # The actual line reads: "Derslerin Başlaması (Önlisans, lisans ve lisansüstü programlar)"
        # We match "derslerin baslamasi" and require it mentions "lisans" to avoid matching
        # TİB (Temel İngilizce Birimi) class start lines.
        if "derslerin baslamasi" in normalized and "lisans" in normalized:
            # Date is on the line directly before
            if i > 0:
                default_year = start_year if current_section == "guz" else end_year
                d = _parse_date_from_text(lines[i - 1], default_year)
                if d:
                    if current_section == "guz" and fall_start is None:
                        fall_start = d
                        print(f"  Found fall start: {d}")
                    elif current_section == "bahar" and spring_start is None:
                        spring_start = d
                        print(f"  Found spring start: {d}")

        # Look for "derslerin son günü" (last day of classes).
        # The actual line reads: "Lisans ve lisansüstü programları ... için derslerin son günü"
        # Skip TİB and Meslek Yüksekokulu entries.
        if "derslerin son gun" in normalized:
            # Skip TİB (Temel İngilizce Birimi) entries
            if "temel ingilizce" in normalized:
                continue
            # Skip Meslek Yüksekokulu (vocational school)
            if "meslek yuksekokulu" in normalized:
                continue
            # Skip Yaz Okulu (summer school)
            if "yaz okulu" in normalized:
                continue

            # Require "lisans" to match only the main program entry
            if "lisans" not in normalized:
                continue

            # Date is on the line directly before
            if i > 0:
                default_year = end_year if current_section == "guz" else end_year
                d = _parse_date_from_text(lines[i - 1], default_year)
                if d:
                    if current_section == "guz" and fall_end is None:
                        fall_end = d
                        print(f"  Found fall end: {d}")
                    elif current_section == "bahar" and spring_end is None:
                        spring_end = d
                        print(f"  Found spring end: {d}")

    # Build semester entries
    if fall_start and fall_end:
        semesters.append(
            {
                "name": f"{year_str} guz donemi",
                "start": fall_start.isoformat(),
                "end": fall_end.isoformat(),
                "type": "guz",
            }
        )

    if spring_start and spring_end:
        semesters.append(
            {
                "name": f"{year_str} bahar donemi",
                "start": spring_start.isoformat(),
                "end": spring_end.isoformat(),
                "type": "bahar",
            }
        )

    return semesters


def update_config(new_semesters: list[dict], config_path: Path = CONFIG_PATH) -> None:
    """Merge scraped semesters into the existing config file."""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    existing = config.get("semesters", [])

    # Index existing by (name)
    existing_by_name = {s["name"]: s for s in existing}

    # Merge: update existing, add new
    for sem in new_semesters:
        existing_by_name[sem["name"]] = sem

    # Sort by start date and rebuild
    merged = sorted(existing_by_name.values(), key=lambda s: s["start"])
    config["semesters"] = merged

    # Preserve milestones if present
    if "milestones" not in config:
        config["milestones"] = [10, 25, 33, 42, 50, 69, 75, 90, 100]

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nConfig updated: {config_path}")
    print(f"Total semesters: {len(merged)}")


def main():
    parser = argparse.ArgumentParser(description="Scrape ODTU academic calendar")
    parser.add_argument(
        "--year",
        type=str,
        help="Academic year to scrape (e.g., 2025-2026). Defaults to current + next.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview extracted dates without writing to config.",
    )
    args = parser.parse_args()

    if args.year:
        years = [args.year]
    else:
        # Determine current academic year
        from datetime import datetime

        now = datetime.now()
        if now.month >= 9:
            current_year = f"{now.year}-{now.year + 1}"
            next_year = f"{now.year + 1}-{now.year + 2}"
        else:
            current_year = f"{now.year - 1}-{now.year}"
            next_year = f"{now.year}-{now.year + 1}"
        years = [current_year, next_year]

    all_semesters = []
    for year_str in years:
        try:
            html = fetch_calendar(year_str)
            semesters = parse_calendar(html, year_str)
            all_semesters.extend(semesters)
            print(f"\nFound {len(semesters)} semester(s) for {year_str}")
        except requests.RequestException as e:
            print(f"Failed to fetch calendar for {year_str}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing calendar for {year_str}: {e}", file=sys.stderr)

    if not all_semesters:
        print("No semesters found. Check the ODTU website or try a specific year.")
        sys.exit(1)

    print("\nExtracted semesters:")
    for sem in all_semesters:
        print(f"  {sem['name']}: {sem['start']} -> {sem['end']} ({sem['type']})")

    if args.dry_run:
        print("\nDry run - config not updated.")
    else:
        update_config(all_semesters)


if __name__ == "__main__":
    main()
