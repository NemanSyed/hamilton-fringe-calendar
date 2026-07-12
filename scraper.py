#!/usr/bin/env python3
"""
Hamilton Fringe Festival 2026 -> ICS calendar generator.

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
4. Emits one VEVENT per performance instance to docs/fringe.ics, in UTC.

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
from typing import Optional

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

OUTPUT_ICS = Path("docs/fringe.ics")
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Instance:
    date_text: str          # e.g. "Wednesday, July 15"
    raw_title: str          # e.g. "CANCELLED \u2014 WOLFE (Formerly: Some of This is True)"
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
    target = label.rstrip(":").strip().lower()
    for i, line in enumerate(text_lines):
        if line.rstrip(":").strip().lower() == target and i + 1 < len(text_lines):
            return text_lines[i + 1].strip()
    return None


# ---------------------------------------------------------------------------
# Step 1: parse the live /performances/ page for every instance
# ---------------------------------------------------------------------------

def fetch(url: str) -> BeautifulSoup:
    log.info("Fetching %s", url)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_performances(soup: BeautifulSoup) -> list:
    """
    Single linear pass over the DOM in document (parse) order.

    State machine: seek_title -> collecting_venue_then_time -> (emit) -> seek_title.

    Two things this deliberately guards against, found during code review:

    1. bs4.Comment is a SUBCLASS of NavigableString, so a naive
       `isinstance(el, NavigableString)` check also matches HTML comments.
       And a <script>/<style> tag's inline content is itself a
       NavigableString child, indistinguishable from real visible text by
       type alone. Both are explicitly excluded below.
    2. A venue name is not guaranteed to be a single text node -- if it's
       split across nested inline tags (e.g. "The Staircase" and "Studio
       Theatre" as separate <span> children around a "|"), the old version
       of this function would grab only the first fragment as the venue and
       then fail to match a time on the second fragment, silently dropping
       the whole performance instance. This version instead collects text
       fragments as "venue" until one of them matches a time pattern,
       joining fragments with a single space -- which produces the correct
       venue string whether it was one node or several, and never drops an
       instance just because of how the venue text happens to be split.

    This also deliberately does NOT use find_all_next() from an anchor tag:
    bs4's "next" traversal is PARSE order, so a tag's own child text is
    itself the first "next" element after the tag -- an earlier version used
    find_all_next() and it silently read each title back as its own venue.
    """
    main = soup.find("main") or soup.body
    if main is None:
        raise RuntimeError("Could not find page body on /performances/")

    instances = []
    current_date = None
    state = "seek_title"
    pending_title = pending_href = None
    venue_fragments = []
    skip_parent = None  # Tag whose own direct-child text should be ignored
    MAX_VENUE_FRAGMENTS = 5  # bail out rather than run away if something's off

    for el in main.descendants:
        if isinstance(el, Comment):
            continue

        if isinstance(el, NavigableString):
            parent_name = getattr(el.parent, "name", None)
            if parent_name in ("script", "style", "noscript"):
                continue
            if skip_parent is not None and el.parent is skip_parent:
                continue
            text = str(el).strip()
            if not text:
                continue

            if state == "collecting_venue_then_time":
                if TIME_RE.match(text):
                    venue = " ".join(venue_fragments) if venue_fragments else None
                    if venue is None:
                        log.warning("Time %r found with no venue text collected for %r -- skipping",
                                    text, pending_title)
                    elif not current_date:
                        log.warning("No date context yet for %r -- skipping", pending_title)
                    else:
                        if len(venue_fragments) > 1:
                            log.info("Venue text for %r was split across %d fragments: %r",
                                     pending_title, len(venue_fragments), venue)
                        instances.append(Instance(
                            date_text=current_date, raw_title=pending_title,
                            href=pending_href, venue=venue, time_text=text,
                        ))
                    state = "seek_title"
                    skip_parent = None
                    venue_fragments = []
                else:
                    venue_fragments.append(text)
                    if len(venue_fragments) > MAX_VENUE_FRAGMENTS:
                        log.warning(
                            "Gave up looking for a time after title %r -- collected %d text "
                            "fragments (%r) with no time match; skipping this block",
                            pending_title, len(venue_fragments), venue_fragments,
                        )
                        state = "seek_title"
                        skip_parent = None
                        venue_fragments = []
            # state == "seek_title": stray text between blocks, ignore it
            continue

        name = getattr(el, "name", None)
        if name in ("h2", "h3"):
            txt = el.get_text(strip=True)
            if WEEKDAY_DATE_RE.match(txt):
                current_date = txt
            continue

        if name != "a":
            continue
        href = el.get("href", "")
        if not href.startswith(f"{BASE}/events/"):
            continue
        text = el.get_text(strip=True)
        if not text:
            continue  # image-only link (e.g. thumbnail wrapped in <a>)

        if text.lower() in TICKET_LABELS:
            # "book tickets >" etc. also link to /events/... -- treat as an
            # explicit end-of-block marker, and reset if a block was left
            # incomplete (e.g. venue/time text didn't resolve).
            if state != "seek_title":
                log.warning("Block for %r ended without finding a time -- skipping",
                            pending_title)
            state = "seek_title"
            skip_parent = None
            venue_fragments = []
            continue

        if state != "seek_title":
            # A second title-like anchor appeared before we finished the
            # previous block. Shouldn't happen given the confirmed page
            # structure, but don't silently corrupt state if it does.
            log.warning("Unexpected title anchor %r while still parsing %r -- resetting",
                        text, pending_title)
        pending_title, pending_href = text, href
        skip_parent = el
        venue_fragments = []
        state = "collecting_venue_then_time"

    log.info("Parsed %d performance instances", len(instances))
    return instances


def clean_instance(inst: Instance) -> None:
    title = inst.raw_title
    cancelled = False
    if title.upper().startswith("CANCELLED"):
        cancelled = True
        title = re.sub(r"^CANCELLED\s*[\u2014\-]\s*", "", title, flags=re.IGNORECASE)

    m = re.match(r"^(.*?)\s*\(Formerly:\s*(.*?)\)\s*$", title)
    formerly = None
    if m:
        title = m.group(1).strip()
        formerly = m.group(2).strip()

    inst.cancelled = cancelled
    inst.clean_title = title
    inst.formerly = formerly

    dm = WEEKDAY_DATE_RE.match(inst.date_text)
    hm = parse_time_to_24h(inst.time_text)
    if not (dm and hm):
        return
    month = MONTHS[dm.group(2)]
    day = int(dm.group(3))
    hour, minute = hm
    inst.local_key = (month, day, hour, minute)

    local_naive = datetime(YEAR, month, day, hour, minute)
    inst.dt_start_utc = local_naive - timedelta(hours=TORONTO_UTC_OFFSET_HOURS)


def sanity_check_dates(instances: list) -> None:
    found = {inst.local_key[:2] for inst in instances if inst.local_key}
    missing = [d for d in EXPECTED_DATES if d not in found]
    if missing:
        log.warning(
            "No performances parsed for expected festival date(s): %s -- "
            "this may mean /performances/ is paginated/truncated after all, "
            "or the site's date range changed. Double check before trusting output.",
            ", ".join(f"July {d[1]}" for d in missing),
        )
    else:
        log.info("Sanity check OK: found performances on all %d expected festival dates",
                  len(EXPECTED_DATES))


# ---------------------------------------------------------------------------
# Step 2: parse each unique show's own page
# ---------------------------------------------------------------------------

def parse_show_page(soup: BeautifulSoup, href: str) -> ShowInfo:
    main = soup.find("main") or soup.body
    info = ShowInfo()
    text_lines = [s.strip() for s in main.stripped_strings if s.strip()]

    # --- Company / origin: first two headings in the content area. Best-effort;
    # logged if suspicious so it's easy to spot during the --debug review pass.
    h2 = main.find("h2")
    h3 = main.find("h3")
    if h2:
        info.company = h2.get_text(strip=True)
    else:
        log.warning("%s: no <h2> found for company name", href)
    if h3:
        info.origin = h3.get_text(strip=True)

    # --- Warnings / Genre / Price. Confirmed against real saved copies of
    # multiple event pages: the label and its value are SEPARATE consecutive
    # text lines/nodes -- e.g. "Warnings:" then, as its own line, "Sexual
    # Content, Coarse Language" -- not combined on one line as an earlier
    # version of this script assumed (that assumption came from the printed
    # PDF program's layout, which does not match the live site's HTML).
    # find_label_value() takes the FIRST matching label only, so it can't
    # accidentally pick up a same-named label belonging to a different show
    # lower on the page (e.g. inside a "Related Events" section).
    #
    # Warnings has an extra wrinkle, confirmed from two different real
    # patterns: sometimes the value is the literal generic category marker
    # "Other Warnings" on its own (e.g. Opening Night Kick-Off), and
    # sometimes it's a comma list that INCLUDES "Other Warnings" alongside
    # real categories (e.g. WOLFE: "Sexual Content, Coarse Language,
    # Violence, Other Warnings"). Either way, a separate "Other:" label
    # holds the actual free-text detail that belongs in place of that
    # generic marker, so it's substituted in via substring replacement --
    # this correctly handles both the "marker alone" and "marker mixed into
    # a list" cases with the same logic.
    warnings_val = find_label_value(text_lines, "Warnings:")
    other_detail = find_label_value(text_lines, "Other:")
    if warnings_val and warnings_val.lower() != "none":
        if other_detail and "other warnings" in warnings_val.lower():
            warnings_val = re.sub(r"other warnings", other_detail, warnings_val,
                                   flags=re.IGNORECASE)
        info.warnings = warnings_val

    genre_val = find_label_value(text_lines, "Genre:")
    if genre_val:
        info.genre = genre_val
    else:
        log.warning("%s: no 'Genre:' label found", href)

    price_val = find_label_value(text_lines, "General Admission:")
    if price_val:
        info.price = f"General Admission: {price_val}"

    # --- Duration: appears as a line starting with a number and a unit,
    # repeated in each per-instance block. Confirmed real formats: "60 min"
    # / "20 min" (indoor shows), "3 hrs" / "2.5 hrs" (free outdoor events),
    # and "75 min (hop on and off!)" (Fringe On The Streets -- trailing text
    # after the unit, so DURATION_LINE_RE matches a prefix, not the whole
    # line). NOT combined with genre via "|" -- that was a PDF-only layout,
    # not present in the live HTML.
    dur_line = next((l for l in text_lines if DURATION_LINE_RE.match(l)), None)
    if dur_line:
        m = DURATION_LINE_RE.match(dur_line)
        value, unit = float(m.group(1)), m.group(2).lower()
        info.duration_min = round(value * 60) if unit.startswith("h") else round(value)
    else:
        log.warning("%s: could not find a run-time line (e.g. '60 min' or '3 hrs'); "
                    "using default %d min", href, DEFAULT_DURATION_MIN)

    # --- Description: confirmed real structure has a literal "Dates & Times >"
    # marker line immediately before the show's own description paragraph,
    # and before any review-quote lines or credits. Using that marker instead
    # of a "longest line on the page" heuristic -- the old heuristic actually
    # picked up unrelated footer boilerplate (a health & safety notice) on
    # the real page because that boilerplate text was LONGER than the real
    # description. Falls back to the old heuristic (with a loud warning) only
    # if the marker isn't present, so a future layout change degrades instead
    # of silently returning nothing.
    try:
        marker_idx = text_lines.index("Dates & Times >")
        info.description = text_lines[marker_idx + 1]
    except ValueError:
        log.warning("%s: 'Dates & Times >' marker not found -- falling back to "
                    "longest-line heuristic for description (less reliable)", href)
        candidates = [
            l for l in text_lines
            if len(l) > 80 and not l.startswith(("WARNINGS", "Warnings", "General Admission"))
        ]
        info.description = max(candidates, key=len) if candidates else ""
    except IndexError:
        log.warning("%s: 'Dates & Times >' marker was the last line on the page "
                    "(no description followed it)", href)

    # --- Per-instance flags: walk the repeating
    #   <date "July 16, 2026"> <venue> <time "9.00pm"> <duration> [flags?] <ticket label>
    # block. Flags are NOT assumed uniform across a show's run -- each
    # instance's flag set starts empty and only gets what's found in its own
    # block, exactly as confirmed against the live/printed schedule data.
    #
    # IMPORTANT: flag placement relative to the time is NOT assumed to be
    # "after" only. Confirmed real examples show it both ways -- the printed
    # program's master schedule grid shows "3:00 PM MM" (flag after), while
    # the same program's individual show listings show "TU 21 * 7:30PM"
    # (asterisk/flag before). So any flag-looking text seen after a date
    # header but before its time is held as `pending_flags` and merged in
    # the moment a time is matched, in addition to continuing to catch flags
    # that appear after the time, up to the next block-end marker.
    #
    # HARD STOP at "Related Events": confirmed present as an exact-match
    # line, right at the schedule section's boundary, on every real page
    # checked (paid shows, free events, a cancelled show, and a walking
    # tour). This was found to be necessary, not just cautious: some free,
    # single-instance events (e.g. Opening Night Kick-Off, Bands on the
    # Boulevard) have NO block-end marker at all after their only instance
    # -- no "buy tickets", no "Get A Reminder", nothing -- so without this
    # stop, current_instance stayed "open" all the way into the page's
    # footer boilerplate, which contains the sentence "...this year's
    # selection of Mask-Mandatory performances," and that got matched as a
    # real MM flag on the last instance. Confirmed via real data, not
    # hypothetical -- this exact false positive happened before this fix.
    current_date = None       # (month, day) or None
    current_instance = None   # (month, day, hour, minute) or None, once time is seen
    pending_flags = set()     # flags seen after a date header but before its time
    for line in text_lines:
        if line == "Related Events":
            break

        dm = SHOW_DATE_RE.match(line)
        if dm:
            month = MONTHS[dm.group(1)]
            day = int(dm.group(2))
            current_date = (month, day)
            current_instance = None
            pending_flags = set()
            continue

        hm = parse_time_to_24h(line)
        if hm and current_date:
            current_instance = (current_date[0], current_date[1], hm[0], hm[1])
            info.flags_by_key.setdefault(current_instance, set())
            if pending_flags:
                info.flags_by_key[current_instance] |= pending_flags
                pending_flags = set()
            continue

        flags = extract_flags(line)
        if flags:
            if current_instance:
                info.flags_by_key[current_instance] |= flags
            elif current_date:
                pending_flags |= flags

        if SHOW_PAGE_BLOCK_END_RE.match(line):
            # End of this instance's block -- stay on the same date in case
            # there's a second showtime the same day, but stop attaching
            # flags to it until we see the next time.
            current_instance = None
            pending_flags = set()

    return info


# ---------------------------------------------------------------------------
# Step 3: build + write the ICS file
# ---------------------------------------------------------------------------

def escape_ics(text: str) -> str:
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
    slug = inst.href.rstrip("/").rsplit("/", 1)[-1]
    key = f"{slug}-{inst.dt_start_utc.isoformat() if inst.dt_start_utc else inst.time_text}"
    return f"{hashlib.sha1(key.encode()).hexdigest()}@hamilton-fringe-calendar"


def write_ics(instances: list, shows: dict) -> str:
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

    perf_soup = fetch(PERFORMANCES_URL)
    instances = parse_performances(perf_soup)
    for inst in instances:
        clean_instance(inst)
    sanity_check_dates(instances)

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

    ics_text = write_ics(instances, shows)
    OUTPUT_ICS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ICS.write_text(ics_text, encoding="utf-8")
    log.info("Wrote %s (%d bytes)", OUTPUT_ICS, len(ics_text))


if __name__ == "__main__":
    main()
