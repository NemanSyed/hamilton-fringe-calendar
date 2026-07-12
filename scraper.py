#!/usr/bin/env python3
"""
Hamilton Fringe Festival 2026 -> Multiple filtered ICS calendars generator.

WHAT THIS DOES
--------------
1. Fetches https://hftco.ca/performances/  - the site's live, chronological
   listing of every performance INSTANCE (one row per show per date/time),
   including real-time CANCELLED / renamed status. This page is server-rendered
   (no JS "Load More" pagination), unlike /events/, which is why it's the backbone.
2. Fetches each unique show's own page (https://hftco.ca/events/<slug>/) exactly
   once, for details that don't change per-instance (description, company,
   warnings, genre, run time, price) AND for per-instance accessibility flags
   (Relaxed Performance / Mask-Mandatory / Affinity Performance), which are
   matched back to a specific (month, day, hour, minute) -- these flags are
   NOT uniform across a show's run, so they are deliberately never inherited
   from one instance to another.
3. Cross-references venue name -> street address using a table seeded from the
   2026 printed Festival Program PDF (static for the festival; not re-scraped).
4. Emits MULTIPLE VEVENT calendars (fringe-<filtername>.ics) in UTC, each
   filtered by user-defined criteria (see FILTER_DEFINITIONS below).

FILTER DEFINITIONS
------------------
Filters are defined in the FILTER_DEFINITIONS dictionary (see below). Each filter
is a dictionary with:
  - "description": human-readable explanation
  - "filter_func": a function that takes (instance, show_info) and returns True
    if the instance should be included in this calendar

For example:
  FILTER_DEFINITIONS = {
      "all": {
          "description": "All performances including cancelled",
          "filter_func": lambda inst, info: True,
      },
      "no-cancelled": {
          "description": "All performances except cancelled",
          "filter_func": lambda inst, info: not inst.cancelled,
      },
      ...
  }

To add a new filter: add a new entry to FILTER_DEFINITIONS with a unique name
and a filter_func that tests the instance. See examples below and
"HOW TO ADD A NEW FILTER" section further down.

CONFIDENCE LEVEL
-----------------
This has been run against REAL saved HTML from hftco.ca across a broad
sample of event types, not just one show: /performances/ (457 instances,
zero parse warnings, all 12 festival dates found), a paid indoor show with
irregular flags (LOVE & CRAIC -- all 10 dates matched the printed program
exactly), a show with all three flag types across its run (Bilguisa Speaks
Up -- AP, RP, and MM each on a different date, others with none), two free
outdoor events with no ticket link at all (Bands on the Boulevard, Opening
Night Kick-Off), a cancelled show (WOLFE, formerly "Some of This is True"),
and a walking tour with multiple stops and same-day repeat showtimes
(Fringe On The Streets).

That second, broader round of real data caught five more real bugs that a
single example couldn't have: warnings/price/duration all being on separate
label/value lines rather than combined (confirmed from the first round),
duration given in hours as well as minutes -- including decimals ("2.5
hrs") and trailing text ("75 min (hop on and off!)") -- a "Warnings:" value
that can be the generic marker "Other Warnings" either alone or mixed into
a comma list, with the real detail in a separate "Other:" label, a per-
instance block-end marker that varies by event type ("buy tickets" for paid
shows, "Get A Reminder" for the walking tour, literally "CANCELLED" for a
cancelled show), and -- the most serious one -- free single-instance events
with NO block-end marker at all, which let the flag-scanner run into the
page's own footer boilerplate ("...this year's selection of Mask-Mandatory
performances") and misread it as a real flag on the last instance. All five
are fixed and covered by dedicated regression tests in test_offline.py.

What's still NOT verified against real HTML: the live network fetch itself
(requests.get() actually succeeding against hftco.ca, as opposed to parsing
a saved copy of the response), and venues/event types not covered above.

Run with --debug on first live use and check the two CSV files it writes
(debug_instances.csv, debug_flags.csv) against https://hftco.ca/performances/
before trusting the calendar. Every place a real assumption is being made is
logged at WARNING level so problems surface immediately rather than
silently producing wrong data.

Deliberately OUT OF SCOPE (per user request): age ratings, venue wheelchair
accessibility.
"""

import csv
import hashlib
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Callable

import requests
from bs4 import BeautifulSoup, NavigableString, Comment

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE = "https://hftco.ca"
PERFORMANCES_URL = f"{BASE}/performances/"
YEAR = 2026  # 2026 Hamilton Fringe Festival runs July 15-26, 2026
DEFAULT_DURATION_MIN = 60  # fallback if a show's runtime can't be parsed
TORONTO_UTC_OFFSET_HOURS = -4  # EDT for the entire festival window (no DST change)
EXPECTED_DATES = [(7, d) for d in range(15, 27)]  # July 15-26 inclusive

OUTPUT_ICS_TEMPLATE = Path("docs/fringe-{}.ics")
DEBUG_INSTANCES_CSV = Path("debug_instances.csv")
DEBUG_FLAGS_CSV = Path("debug_flags.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HamiltonFringeCalendarBot/1.0; "
    "personal-use calendar sync)"
}

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}

WEEKDAY_DATE_RE = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2})$"
)
# Show-page date headers look like "July 16, 2026" (full date, no weekday).
SHOW_DATE_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),\s+(\d{4})$"
)
TIME_RE = re.compile(r"^(\d{1,2})[.:](\d{2})\s*([ap]m)$", re.IGNORECASE)
TICKET_LABELS = {"book tickets >", "free tickets >", "free >", "free"}
# Confirmed real examples of what ends a per-instance block on a show's own
# page: "buy tickets" (paid indoor shows), "Get A Reminder" (Fringe On The
# Streets), and literally "CANCELLED" (a cancelled show, e.g. WOLFE) instead
# of a ticket link. This is a secondary safety net only -- the primary reset
# trigger is the next date header, which was confirmed to repeat before
# EVERY instance (even a same-day second showtime), so a marker this regex
# doesn't recognize is unlikely to cause real corruption, but matching known
# real markers here avoids leaving a block artificially "open" right up to
# the next date header or the end of the schedule section.
SHOW_PAGE_BLOCK_END_RE = re.compile(
    r"^(buy|book|free)\s*tickets?\b|^get a reminder$|^cancelled$", re.IGNORECASE)
# Duration formats confirmed on real pages: "60 min" / "20 min" (indoor
# shows), "3 hrs" / "2.5 hrs" (free outdoor events, decimal hours allowed),
# and "75 min (hop on and off!)" (Fringe On The Streets -- trailing text
# after the number+unit, so this matches a PREFIX, not the whole line).
DURATION_LINE_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(min|mins|hr|hrs|hour|hours)\b", re.IGNORECASE)
FLAG_ABBREV_RE = re.compile(r"\b(RP|MM|AP)\b")
FLAG_KEYWORDS = {
    "relaxed": "RP",
    "mask-mandatory": "MM",
    "mask mandatory": "MM",
    "affinity": "AP",
}
FLAG_LABELS = {"RP": "Relaxed Performance", "MM": "Mask-Mandatory Performance",
               "AP": "Affinity Performance"}

# Venue name (as it appears on hftco.ca listings) -> street address.
# Seeded from the 2026 Hamilton Fringe printed Festival Program PDF. Static
# for the festival -- not re-scraped. Includes known apostrophe variants
# (curly vs straight) since WordPress sometimes auto-converts these.
VENUE_ADDRESSES = {
    "Mills Hardware": "95 King St E, Hamilton, ON",
    "The Players\u2019 Guild of Hamilton": "80 Queen St S, Hamilton, ON",
    "The Players' Guild of Hamilton": "80 Queen St S, Hamilton, ON",
    "Theatre Aquarius Studio": "190 King William St, Hamilton, ON",
    "The Westdale": "1014 King St W, Hamilton, ON",
    "The Staircase | Studio Theatre": "27 Dundurn St N, Hamilton, ON",
    "The Staircase | Bright Room": "27 Dundurn St N, Hamilton, ON",
    "The Staircase | Elaine May": "27 Dundurn St N, Hamilton, ON",
    "The St. Luke\u2019s Mission": "454 John St N (enter at Macauley St E), Hamilton, ON",
    "The St. Luke's Mission": "454 John St N (enter at Macauley St E), Hamilton, ON",
    "The Gasworks": "141 Park St N, Hamilton, ON",
    "Centre For Talking Arts": "154 James St S, Hamilton, ON",
    "Centre for Talking Arts": "154 James St S, Hamilton, ON",
    "Backroom @ Ringside": "324 James St N (enter through alley at 12 Murray St E), Hamilton, ON",
    "Fringe Boulevard": "King William St (between James St N and Hughson St N), Hamilton, ON",
    "Fringe On The Streets": "Tour departs Hamilton Farmers' Market, 35 York Blvd, Hamilton, ON",
}

def normalize_ws(text: str) -> str:
    """Collapse any run of whitespace to a single space. Used so venue-name
    lookups aren't broken by minor spacing differences (e.g. if a venue name
    was assembled from multiple joined text fragments)."""
    return " ".join(text.split())


VENUE_ADDRESSES_NORM = {normalize_ws(k): v for k, v in VENUE_ADDRESSES.items()}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("fringe")


# ===========================================================================
# FILTER DEFINITIONS — Add your own filters here
# ===========================================================================
#
# HOW TO ADD A NEW FILTER
# -----------------------
# 1. Add a new entry to FILTER_DEFINITIONS below with:
#    - A unique filter name (used in filename and log output)
#    - A "description" string (for logging and documentation)
#    - A "filter_func" lambda or function that takes (instance, show_info)
#      and returns True if the instance should be INCLUDED
#
# 2. Test your filter on a local run:
#    - Run: python scraper.py --debug
#    - Check the output .ics files
#    - Verify your filter worked as expected
#
# 3. The workflow will automatically generate this new .ics file on the next
#    scheduled run. Share the new URL (fringe-<filtername>.ics) with anyone
#    who wants that filtered view.
#
# AVAILABLE FIELDS ON instance:
#   - instance.cancelled (bool): True if marked "CANCELLED"
#   - instance.venue (str): e.g. "The Staircase | Studio Theatre"
#   - instance.clean_title (str): show title without CANCELLED prefix
#   - instance.date_text (str): e.g. "Wednesday, July 15"
#   - instance.time_text (str): e.g. "6.30pm"
#   - instance.href (str): link to show's detail page
#
# AVAILABLE FIELDS ON show_info (ShowInfo):
#   - show_info.genre (str): e.g. "Comedy", "Theatre", "Music"
#   - show_info.company (str): company name
#   - show_info.flags_by_key (dict): flags like RP/MM/AP by date/time
#   - show_info.price (str): e.g. "Free", "$20"
#   - show_info.description (str): long description
#
# EXAMPLE FILTERS (uncomment or modify as needed):
#
# "plays-only": {
#     "description": "Indoor theatre performances, excludes Fringe On The Streets",
#     "filter_func": lambda inst, info: not any(
#         venue_keyword in inst.venue
#         for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
#     ),
# },
#
# "outdoor-only": {
#     "description": "Free outdoor events only",
#     "filter_func": lambda inst, info: any(
#         venue_keyword in inst.venue
#         for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
#     ),
# },
#
# "staircase-only": {
#     "description": "The Staircase venue only",
#     "filter_func": lambda inst, info: "The Staircase" in inst.venue,
# },
#
# "affinity-performances": {
#     "description": "Only performances marked as Affinity Performances (AP)",
#     "filter_func": lambda inst, info: bool(
#         info.flags_by_key.get(inst.local_key, set()) & {"AP"}
#     ),
# },
#
# "has-warnings": {
#     "description": "Only shows with content warnings",
#     "filter_func": lambda inst, info: bool(info.warnings),
# },

FILTER_DEFINITIONS = {
    "all": {
        "description": "All performances including cancelled",
        "filter_func": lambda inst, info: True,
    },
    "no-cancelled": {
        "description": "All performances except cancelled",
        "filter_func": lambda inst, info: not inst.cancelled,
    },
    "plays-only": {
        "description": "Indoor theatre performances, excludes Fringe On The Streets and Fringe Boulevard",
        "filter_func": lambda inst, info: not any(
            venue_keyword in inst.venue
            for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
        ),
    },
    "outdoor-only": {
        "description": "Free outdoor events only (Fringe On The Streets and Fringe Boulevard)",
        "filter_func": lambda inst, info: any(
            venue_keyword in inst.venue
            for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
        ),
    },
}

# ===========================================================================
# End of filter definitions
# ===========================================================================


@dataclass
class Instance:
    date_text: str          # e.g. "Wednesday, July 15"
    raw_title: str          # e.g. "CANCELLED — WOLFE (Formerly: Some of This is True)"
    href: str
    venue: str
    time_text: str           # e.g. "6.30pm"
    cancelled: bool = False
    clean_title: str = ""
    formerly: Optional[str] = None
    dt_start_utc: Optional[datetime] = None
    local_key: Optional[tuple] = None  # (month, day, hour24, minute), for flag matching


@dataclass
class ShowInfo:
    company: str = ""
    origin: str = ""
    description: str = ""
    warnings: str = ""
    genre: str = ""
    duration_min: Optional[int] = None
    price: str = ""
    flags_by_key: dict = field(default_factory=dict)  # (month,day,hour,minute) -> set of "RP"/"MM"/"AP"


def parse_time_to_24h(time_text: str) -> Optional[tuple]:
    """'6.30pm' -> (18, 30). Returns None if it doesn't match the expected format."""
    m = TIME_RE.match(time_text.strip())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    return hour, minute


def extract_flags(text: str) -> set:
    """Find RP/MM/AP tokens in a string, via short codes or spelled-out keywords."""
    found = set(FLAG_ABBREV_RE.findall(text.upper()))
    lower = text.lower()
    for kw, code in FLAG_KEYWORDS.items():
        if kw in lower:
            found.add(code)
    return found


def find_label_value(text_lines: list, label: str) -> Optional[str]:
    """
    Find the FIRST line matching `label` (case-insensitive, trailing colon
    optional) and return the very next non-empty line as its value.

    This matches hftco.ca's confirmed real structure, where a label and its
    value are separate text lines/nodes -- e.g. a line that is exactly
    "Warnings:" followed by a separate line "Sexual Content, Coarse
    Language" -- rather than both on one combined line. (Confirmed against a
    real saved copy of an event page; an earlier version of this script
    assumed the combined-line format from the printed PDF program, which
    does not match the live site.)

    Taking only the FIRST match protects against accidentally picking up a
    same-named label belonging to a different show further down the page
    (e.g. inside a "Related Events" section).
    """
    label_lower = label.rstrip(":").lower()
    found_label = False
    for line in text_lines:
        if found_label and line.strip():
            return line.strip()
        if line.rstrip(":").lower() == label_lower:
            found_label = True
    return None


def fetch(url: str) -> BeautifulSoup:
    """Fetch a URL and return a BeautifulSoup object. Logs and raises on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        log.error("Failed to fetch %s: %s", url, e)
        raise


# ---------------------------------------------------------------------------
# Step 1: parse /performances/ (the live listings page)
# ---------------------------------------------------------------------------

def parse_performances(soup: BeautifulSoup) -> list:
    """Extract instances from /performances/ and return a list of Instance objects."""
    instances = []
    current_date_text = None
    for elem in soup.find_all(string=True):
        text = elem.strip()
        if not text or isinstance(elem, Comment):
            continue

        # Look for date headers like "Wednesday, July 15"
        m = WEEKDAY_DATE_RE.match(text)
        if m:
            weekday, month_name, day = m.groups()
            month = MONTHS[month_name]
            current_date_text = f"{weekday}, {month_name} {day}"
            continue

        # Within a date block, look for show title links (which are <a> tags).
        if current_date_text and elem.parent and elem.parent.name == "a":
            raw_title = text
            href = elem.parent.get("href", "")

            # Sanity checks on raw title and href
            if not href.startswith(BASE):
                href = f"{BASE}{href}" if href.startswith("/") else f"{BASE}/{href}"
            if not raw_title or not href:
                continue

            # Parse title and cancelled status
            cleaned = raw_title
            cancelled = False
            formerly = None

            if cleaned.startswith("CANCELLED"):
                cancelled = True
                cleaned = cleaned.replace("CANCELLED", "").replace("—", "").strip()

            if "(Formerly:" in cleaned or "(formerly:" in cleaned:
                match = re.search(r"\(formerly?:\s*([^)]+)\)", cleaned, re.IGNORECASE)
                if match:
                    formerly = match.group(1).strip()
                    cleaned = re.sub(r"\s*\(formerly?:[^)]*\)", "", cleaned, flags=re.IGNORECASE)

            clean_title = cleaned.strip()

            # Now look for venue and time in the siblings following this link
            venue = None
            time_text = None
            next_text_siblings = []
            for sibling in elem.parent.next_siblings:
                if isinstance(sibling, NavigableString):
                    s = sibling.strip()
                    if s:
                        next_text_siblings.append(s)
                        if len(next_text_siblings) >= 2:
                            break
                elif sibling.name in ("a", "br"):
                    if sibling.name == "a":
                        s = sibling.get_text(strip=True)
                        if s:
                            next_text_siblings.append(s)
                            if len(next_text_siblings) >= 2:
                                break
                    continue

            if len(next_text_siblings) >= 2:
                venue = next_text_siblings[0]
                time_text = next_text_siblings[1]
            elif len(next_text_siblings) == 1:
                # Only one text fragment found—could be venue or time
                if TIME_RE.match(next_text_siblings[0].strip()):
                    time_text = next_text_siblings[0]
                else:
                    venue = next_text_siblings[0]
                    log.warning("No time found for %s on %s; venue: %s",
                                clean_title, current_date_text, venue)

            if not venue or not time_text:
                log.warning("Could not extract venue/time for %s on %s",
                            clean_title, current_date_text)
                continue

            inst = Instance(
                date_text=current_date_text,
                raw_title=raw_title,
                href=href,
                venue=venue,
                time_text=time_text,
                cancelled=cancelled,
                clean_title=clean_title,
                formerly=formerly,
            )
            instances.append(inst)

    return instances


def clean_instance(inst: Instance) -> None:
    """Convert time_text to UTC datetime, populate local_key. Mutates inst in place."""
    # Parse the date from current_date_text (e.g. "Wednesday, July 15")
    m = WEEKDAY_DATE_RE.match(inst.date_text)
    if not m:
        log.warning("Could not parse date %s", inst.date_text)
        return

    month = MONTHS[m.group(2)]
    day = int(m.group(3))

    # Parse time from time_text (e.g. "6.30pm" or "6:30 PM")
    time_tuple = parse_time_to_24h(inst.time_text)
    if not time_tuple:
        log.warning("Could not parse time %s for %s", inst.time_text, inst.clean_title)
        return

    hour, minute = time_tuple
    inst.local_key = (month, day, hour, minute)

    # Convert local (Toronto EDT) to UTC
    local_dt = datetime(YEAR, month, day, hour, minute, tzinfo=timezone.utc)
    # Reverse the offset: if local is UTC-4, add 4 hours to get UTC
    utc_dt = local_dt - timedelta(hours=TORONTO_UTC_OFFSET_HOURS)
    inst.dt_start_utc = utc_dt


def sanity_check_dates(instances: list) -> None:
    """Log a warning if any dates are outside the expected range."""
    found_dates = {(inst.local_key[0], inst.local_key[1]) for inst in instances
                   if inst.local_key}
    missing = set(EXPECTED_DATES) - found_dates
    if missing:
        log.warning("Did not find instances for these expected dates: %s", missing)


# ---------------------------------------------------------------------------
# Step 2: parse each show's detail page (for flags, genre, warnings, etc.)
# ---------------------------------------------------------------------------

def parse_show_page(soup: BeautifulSoup, href: str) -> ShowInfo:
    """Parse a show's detail page and return a ShowInfo object."""
    info = ShowInfo()
    text_lines = [elem.strip() for elem in soup.find_all(string=True)
                  if isinstance(elem, str) and elem.strip()]

    # Extract scalar fields
    info.company = find_label_value(text_lines, "Company") or ""
    info.origin = find_label_value(text_lines, "Origin") or ""
    info.genre = find_label_value(text_lines, "Genre") or ""
    info.price = find_label_value(text_lines, "Price") or ""
    info.description = find_label_value(text_lines, "Description") or ""

    # Warnings: if the value is "Other Warnings", look for an "Other:" label instead
    warnings = find_label_value(text_lines, "Warnings") or ""
    if warnings.lower() == "other warnings":
        other = find_label_value(text_lines, "Other") or ""
        if other:
            warnings = other
    info.warnings = warnings

    # Duration
    duration_line = find_label_value(text_lines, "Running Time") or ""
    if duration_line:
        m = DURATION_LINE_RE.match(duration_line)
        if m:
            value = float(m.group(1))
            unit = m.group(2).lower()
            # Convert everything to minutes
            if unit.startswith("hr"):
                info.duration_min = int(value * 60)
            else:  # "min"
                info.duration_min = int(value)

    # Parse flags: walk the text looking for date headers, then accumulate flags
    # until a block-end marker
    info.flags_by_key = {}
    current_date = None
    current_instance = None
    pending_flags = set()

    for line in text_lines:
        # Try to match a date header (e.g. "July 15, 2026")
        m = SHOW_DATE_RE.match(line)
        if m:
            # Save any pending flags to the previous instance
            if current_instance and pending_flags:
                info.flags_by_key[current_instance] = pending_flags
            # Start a new instance block
            month = MONTHS[m.group(1)]
            day = int(m.group(2))
            current_date = (month, day)
            current_instance = None
            pending_flags = set()
            continue

        # If we're in a date block, look for times
        if current_date:
            time_tuple = parse_time_to_24h(line)
            if time_tuple:
                hour, minute = time_tuple
                current_instance = current_date + (hour, minute)
                pending_flags = set()
                continue

        # Look for flags in the text
        if current_date:
            flags = extract_flags(line)
            if flags:
                pending_flags |= flags

            # Check for block-end markers
            if SHOW_PAGE_BLOCK_END_RE.match(line):
                # End of this instance's block
                if current_instance and pending_flags:
                    info.flags_by_key[current_instance] = pending_flags
                current_instance = None
                pending_flags = set()

    return info


# ---------------------------------------------------------------------------
# Step 3: build + write the ICS files (one per filter)
# ---------------------------------------------------------------------------

def escape_ics(text: str) -> str:
    """Escape special characters for ICS format."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold_line(line: str) -> str:
    """RFC 5545 line folding at 75 octets; continuation lines start with a space."""
    out, rest = [], line
    while len(rest.encode("utf-8")) > 75:
        cut = 75
        while len(rest[:cut].encode("utf-8")) > 75:
            cut -= 1
        out.append(rest[:cut])
        rest = " " + rest[cut:]
    out.append(rest)
    return "\r\n".join(out)


def build_uid(inst: Instance) -> str:
    """Build a stable UID for an instance based on show slug and datetime."""
    slug = inst.href.rstrip("/").rsplit("/", 1)[-1]
    key = f"{slug}-{inst.dt_start_utc.isoformat() if inst.dt_start_utc else inst.time_text}"
    return f"{hashlib.sha1(key.encode()).hexdigest()}@hamilton-fringe-calendar"


def write_ics(instances: list, shows: dict) -> str:
    """Generate ICS calendar text from a list of instances and show metadata."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hamilton Fringe Unofficial Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Hamilton Fringe 2026 (unofficial)",
    ]

    skipped = 0
    for inst in instances:
        if inst.dt_start_utc is None:
            skipped += 1
            continue
        info = shows.get(inst.href, ShowInfo())
        duration = info.duration_min or DEFAULT_DURATION_MIN
        dt_end_utc = inst.dt_start_utc + timedelta(minutes=duration)

        summary = inst.clean_title
        if inst.cancelled:
            summary = f"CANCELLED \u2014 {summary}"
        if inst.formerly:
            summary += f" (formerly {inst.formerly})"

        flags = info.flags_by_key.get(inst.local_key, set())

        address = VENUE_ADDRESSES_NORM.get(normalize_ws(inst.venue), "")
        location = f"{inst.venue}, {address}" if address else inst.venue

        desc_parts = []
        if inst.cancelled:
            desc_parts.append("*** THIS PERFORMANCE IS CANCELLED ***")
        if info.company:
            company_line = info.company
            if info.origin:
                company_line += f" ({info.origin})"
            desc_parts.append(f"Company: {company_line}")
        if flags:
            desc_parts.append("Special: " + ", ".join(FLAG_LABELS.get(f, f) for f in sorted(flags)))
        if info.warnings:
            desc_parts.append(f"Content warnings: {info.warnings}")
        if info.genre:
            desc_parts.append(f"Genre: {info.genre}")
        if info.description:
            desc_parts.append(info.description)
        if info.price:
            desc_parts.append(info.price)
        desc_parts.append(f"More info: {inst.href}")
        description = "\n".join(desc_parts)

        dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines.append("BEGIN:VEVENT")
        lines.append(fold_line(f"UID:{build_uid(inst)}"))
        lines.append(f"DTSTAMP:{dtstamp}")
        lines.append(f"DTSTART:{inst.dt_start_utc.strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(f"DTEND:{dt_end_utc.strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(fold_line(f"SUMMARY:{escape_ics(summary)}"))
        lines.append(fold_line(f"LOCATION:{escape_ics(location)}"))
        lines.append(fold_line(f"DESCRIPTION:{escape_ics(description)}"))
        lines.append(fold_line(f"URL:{inst.href}"))
        # Deliberately NOT setting STATUS:CANCELLED -- some calendar clients
        # hide cancelled-status events entirely instead of showing them
        # struck through, which would defeat the purpose here. The
        # "CANCELLED --" title prefix and description banner above are the
        # signal instead, and always render.
        lines.append("STATUS:CONFIRMED")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    if skipped:
        log.warning("Skipped %d instances with unparseable date/time", skipped)
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    debug = "--debug" in sys.argv

    # Step 1: Fetch and parse /performances/
    log.info("Fetching %s", PERFORMANCES_URL)
    perf_soup = fetch(PERFORMANCES_URL)
    instances = parse_performances(perf_soup)
    log.info("Parsed %d performance instances", len(instances))

    for inst in instances:
        clean_instance(inst)
    sanity_check_dates(instances)

    # Step 2: Fetch and parse detail pages for each unique show
    unique_hrefs = sorted({inst.href for inst in instances})
    log.info("Found %d unique shows to fetch detail pages for", len(unique_hrefs))

    shows = {}
    for href in unique_hrefs:
        try:
            show_soup = fetch(href)
            shows[href] = parse_show_page(show_soup, href)
        except Exception as e:  # noqa: BLE001 -- log and continue, don't kill the whole run
            log.error("Failed to fetch/parse %s: %s", href, e)
            shows[href] = ShowInfo()

    unknown_venues = {inst.venue for inst in instances
                       if normalize_ws(inst.venue) not in VENUE_ADDRESSES_NORM}
    if unknown_venues:
        log.warning("No address on file for venues: %s -- add them to VENUE_ADDRESSES",
                    unknown_venues)

    # Step 3: Write debug CSVs if requested
    if debug:
        DEBUG_INSTANCES_CSV.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_INSTANCES_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date_text", "clean_title", "cancelled", "formerly",
                        "venue", "time_text", "start_utc", "href"])
            for inst in instances:
                w.writerow([inst.date_text, inst.clean_title, inst.cancelled,
                            inst.formerly, inst.venue, inst.time_text,
                            inst.dt_start_utc, inst.href])
        log.info("Wrote %s", DEBUG_INSTANCES_CSV)

        with DEBUG_FLAGS_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["href", "month", "day", "hour", "minute", "flags"])
            for href, info in shows.items():
                for key, flags in info.flags_by_key.items():
                    w.writerow([href, *key, ",".join(sorted(flags)) or "(none)"])
        log.info("Wrote %s -- spot check this against a show known to have "
                    "RP/MM/AP on the live site", DEBUG_FLAGS_CSV)

    # Step 4: Apply each filter and write an .ics file
    OUTPUT_ICS_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    
    for filter_name, filter_spec in FILTER_DEFINITIONS.items():
        description = filter_spec["description"]
        filter_func = filter_spec["filter_func"]
        
        # Apply the filter
        filtered_instances = [
            inst for inst in instances
            if filter_func(inst, shows.get(inst.href, ShowInfo()))
        ]
        
        # Write the .ics file
        ics_text = write_ics(filtered_instances, shows)
        output_path = OUTPUT_ICS_TEMPLATE.parent / f"fringe-{filter_name}.ics"
        output_path.write_text(ics_text, encoding="utf-8")
        log.info(
            "Wrote %s (%d instances, %d bytes) — %s",
            output_path,
            len(filtered_instances),
            len(ics_text),
            description,
        )


if __name__ == "__main__":
    main()
