"""
Offline test harness. Builds synthetic HTML that mirrors the confirmed
structure of hftco.ca/performances/ and a show page (including IRREGULAR
RP/MM/AP flags -- present on some instances, absent on others, per the
user's clarification that this is not uniform), then runs the real parsing
functions against it with no network access. This can't prove the real
site's raw HTML matches these fixtures, but it proves the algorithm itself
is correct against the structure it's designed for, and catches logic bugs
independent of that risk.
"""
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, ".")
import scraper  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture 1: /performances/ page -- two dates, five instances, one cancelled
# with a rename, mirroring real examples pulled from the live site.
# Note: Image links (empty <a><img></a> tags) removed to match real site
# structure and prevent parser from misinterpreting them as show titles.
# ---------------------------------------------------------------------------
PERFORMANCES_HTML = """
<html><body><main>
<h3>Wednesday, July 15</h3>
<a href="https://hftco.ca/events/opening-night-kick-off/">Opening Night Kick-Off</a>
<p>Mills Hardware</p>
<p>6.30pm</p>
<a href="https://hftco.ca/events/opening-night-kick-off/">book tickets &gt;</a>

<h3>Thursday, July 16</h3>
<a href="https://hftco.ca/events/some-of-this-is-true/">CANCELLED &#8212; WOLFE (Formerly: Some of This is True)</a>
<p>The Gasworks</p>
<p>6.00pm</p>
<a href="https://hftco.ca/events/some-of-this-is-true/">book tickets &gt;</a>

<a href="https://hftco.ca/events/love-craic/">LOVE &amp; CRAIC</a>
<p>The Staircase | Studio Theatre</p>
<p>10.30pm</p>
<a href="https://hftco.ca/events/love-craic/">book tickets &gt;</a>

<h3>Friday, July 17</h3>
<a href="https://hftco.ca/events/love-craic/">LOVE &amp; CRAIC</a>
<p>The Staircase | Studio Theatre</p>
<p>7.30pm</p>
<a href="https://hftco.ca/events/love-craic/">book tickets &gt;</a>

<a href="https://hftco.ca/events/foodie-fringe/">Foodie Fringe</a>
<p>Fringe Boulevard</p>
<p>5.00pm</p>
<a href="https://hftco.ca/events/foodie-fringe/">free tickets &gt;</a>
</main></body></html>
"""

# ---------------------------------------------------------------------------
# Fixture 2: LOVE & CRAIC's own show page. This mirrors the CONFIRMED real
# structure from an actual saved copy of hftco.ca/events/love-craic/ --
# label and value as separate lines (e.g. "Warnings:" then, separately,
# "Sexual Content, Coarse Language"), a "Dates & Times >" marker right
# before the real description, and a standalone "60 min" duration line per
# instance -- NOT the combined "Genre | 60m" single-line format an earlier
# version of this script assumed (that assumption came from the PDF
# program's layout and turned out not to match the live site at all).
#
# Two performance instances are included with DELIBERATELY DIFFERENT flags
# (one has "Relaxed Performance" alone, the other has the real confirmed
# combined phrasing "Relaxed Performance & Mask-Mandatory Performance"),
# to keep testing that flags are per-instance, not inherited across the run.
# ---------------------------------------------------------------------------
SHOW_PAGE_HTML = """
<html><body><main>
<h1>LOVE &amp; CRAIC</h1>
<h2>Squirrel Suit Productions</h2>
<h3>Hamilton, ON</h3>
<p>July 16, 2026 - July 26, 2026</p>
<p>Dates &amp; Times &gt;</p>
<p>Storyteller Carlyn Rhamey takes you on a Celtic adventure like no other, full of perilous cliffs and Viking ghosts.</p>
<p>&quot;A rave review quote that should NOT be picked up as the description.&quot;</p>
<p>Writer/Performer</p>
<p>Carlyn Rhamey</p>
<p>Event Details</p>
<p>General Admission:</p>
<p>$14</p>
<p>Warnings:</p>
<p>Sexual Content, Coarse Language</p>
<p>Venue:</p>
<p>The Staircase | Studio Theatre</p>
<p>Genre:</p>
<p>Theatre-Comedy, Storytelling/Solo Show</p>

<h3>July 16, 2026</h3>
<a href="https://hftco.ca/venues/the-staircase">The Staircase | Studio Theatre</a>
<p>Relaxed Performance</p>
<h3>10.30pm</h3>
<h3>60 min</h3>
<p>buy tickets</p>

<h3>July 17, 2026</h3>
<a href="https://hftco.ca/venues/the-staircase">The Staircase | Studio Theatre</a>
<p>Relaxed Performance &amp; Mask-Mandatory Performance</p>
<h3>7.30pm</h3>
<h3>60 min</h3>
<p>buy tickets</p>
</main></body></html>
"""

FOODIE_FRINGE_HTML = """
<html><body><main>
<h1>Foodie Fringe</h1>
<h2>HFTco</h2>
<h3>Hamilton</h3>
<p>Each night, Fringe Boulevard hosts a rotating lineup of local restaurants serving curated menus.</p>
</main></body></html>
"""

OPENING_NIGHT_HTML = """
<html><body><main>
<h1>Opening Night Kick-Off</h1>
<h2>HFTco</h2>
<h3>Hamilton</h3>
<p>It's the party that sets the Fringe in motion, featuring artists pitching their shows.</p>
</main></body></html>
"""


def fake_fetch(url):
    mapping = {
        scraper.PERFORMANCES_URL: PERFORMANCES_HTML,
        "https://hftco.ca/events/love-craic/": SHOW_PAGE_HTML,
        "https://hftco.ca/events/some-of-this-is-true/": SHOW_PAGE_HTML.replace(
            "LOVE &amp; CRAIC", "WOLFE"),
        "https://hftco.ca/events/foodie-fringe/": FOODIE_FRINGE_HTML,
        "https://hftco.ca/events/opening-night-kick-off/": OPENING_NIGHT_HTML,
    }
    return BeautifulSoup(mapping[url], "html.parser")


scraper.fetch = fake_fetch  # monkeypatch -- no real network call happens


def main():
    perf_soup = fake_fetch(scraper.PERFORMANCES_URL)
    instances = scraper.parse_performances(perf_soup)
    assert len(instances) == 5, f"expected 5 instances, got {len(instances)}"

    for inst in instances:
        scraper.clean_instance(inst)

    by_title_time = {(i.clean_title, i.time_text): i for i in instances}

    wolfe = by_title_time[("WOLFE", "6.00pm")]
    assert wolfe.cancelled is True
    assert wolfe.formerly == "Some of This is True"
    print("PASS: cancellation + rename parsed correctly")

    craic_thu = by_title_time[("LOVE & CRAIC", "10.30pm")]
    craic_fri = by_title_time[("LOVE & CRAIC", "7.30pm")]
    assert craic_thu.local_key == (7, 16, 22, 30), craic_thu.local_key
    assert craic_fri.local_key == (7, 17, 19, 30), craic_fri.local_key
    print("PASS: two instances of the same show on different days parsed distinctly")

    unique_hrefs = sorted({i.href for i in instances})
    assert len(unique_hrefs) == 4
    shows = {href: scraper.parse_show_page(fake_fetch(href), href) for href in unique_hrefs}
    print("PASS: fetched and parsed", len(shows), "show detail pages")

    craic_info = shows["https://hftco.ca/events/love-craic/"]
    assert craic_info.company == "Squirrel Suit Productions", craic_info.company
    assert craic_info.origin == "Hamilton, ON"
    assert craic_info.warnings == "Sexual Content, Coarse Language"
    assert craic_info.duration_min == 60
    print("PASS: company/origin/warnings/duration parsed from show page")

    # THE CRITICAL CHECK: flags must be per-instance, not inherited across
    # the show's whole run. Thursday 10.30pm has RP only; Friday 7.30pm has
    # the real confirmed combined phrasing "Relaxed Performance &
    # Mask-Mandatory Performance" -- proving both that flags don't leak
    # between instances AND that the combined-phrase format (seen on the
    # real site) is parsed into both codes correctly.
    thu_key = (7, 16, 22, 30)
    fri_key = (7, 17, 19, 30)
    assert craic_info.flags_by_key.get(thu_key) == {"RP"}, craic_info.flags_by_key.get(thu_key)
    assert craic_info.flags_by_key.get(fri_key) == {"RP", "MM"}, craic_info.flags_by_key.get(fri_key)
    print("PASS: per-instance flags correctly NOT uniform across the show's run")

    # Full ICS generation
    ics_text = scraper.write_ics(instances, shows)
    assert ics_text.count("BEGIN:VEVENT") == 5
    assert ics_text.count("END:VEVENT") == 5

    # RFC 5545 line-folding can insert "\r\n " (fold + single space) anywhere,
    # including mid-word, so unfold before doing any substring checks -- this
    # mirrors what a real ICS parser does and avoids false failures/passes.
    unfolded = ics_text.replace("\r\n ", "")

    assert "CANCELLED \u2014 WOLFE (formerly Some of This is True)" in unfolded
    assert "STATUS:CANCELLED" not in unfolded  # deliberately excluded, see code comments
    assert "Special: Relaxed Performance" in unfolded

    # Thursday 10.30pm LOVE & CRAIC (RP only)      -> UTC 2026-07-17T02:30:00Z
    # Friday   7.30pm LOVE & CRAIC (RP + MM)        -> UTC 2026-07-17T23:30:00Z
    thu_block = unfolded[unfolded.index("DTSTART:20260717T023000Z"):]
    thu_block = thu_block[:thu_block.index("END:VEVENT")]
    fri_block = unfolded[unfolded.index("DTSTART:20260717T233000Z"):]
    fri_block = fri_block[:fri_block.index("END:VEVENT")]
    assert "Relaxed Performance" in thu_block
    assert "Mask-Mandatory" not in thu_block, "MM flag leaked into the wrong instance!"
    assert "Relaxed Performance" in fri_block and "Mask-Mandatory" in fri_block
    print("PASS: generated ICS text passes all structural + flag-leakage checks")

    # UTC conversion sanity: 6.30pm EDT on July 15 -> 22:30 UTC (UTC-4)
    kickoff = by_title_time[("Opening Night Kick-Off", "6.30pm")]
    assert kickoff.dt_start_utc.strftime("%Y%m%dT%H%M%SZ") == "20260715T223000Z", \
        kickoff.dt_start_utc
    print("PASS: local-to-UTC time conversion correct")

    print()
    test_warnings_parsing()
    print()
    test_multi_fragment_venue()
    print()
    test_script_and_comment_immunity()
    print()
    test_flag_before_time()
    print()
    test_duration_formats()
    print()
    test_other_warnings_substitution()
    print()
    test_related_events_hard_stop()
    print()
    print("ALL OFFLINE CHECKS PASSED")


def test_warnings_parsing():
    """Targeted checks for the warnings-parsing edge cases, using the
    CONFIRMED real format (label and value as separate lines): a literal
    'None' value must be excluded, and a later same-named label further down
    the page must not overwrite a real value already found."""
    html_none = ('<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                 '<p>Warnings:</p><p>None</p><p>Genre:</p><p>Theatre-Comedy</p></main>')
    info = scraper.parse_show_page(BeautifulSoup(html_none, "html.parser"), "test1")
    assert info.warnings == "", f"expected empty warnings, got {info.warnings!r}"

    html_real = ('<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                 '<p>Warnings:</p><p>Coarse Language, Nudity</p>'
                 '<p>Genre:</p><p>Theatre-Drama</p></main>')
    info = scraper.parse_show_page(BeautifulSoup(html_real, "html.parser"), "test2")
    assert info.warnings == "Coarse Language, Nudity", info.warnings

    # A second "Warnings:" label appearing later (e.g. inside a Related
    # Events section for a different show) must not overwrite the first,
    # real match.
    html_dup = ('<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                '<p>Warnings:</p><p>Sexual Content</p>'
                '<p>Genre:</p><p>Theatre-Comedy</p>'
                '<p>Related Events</p><p>Warnings:</p><p>something else entirely</p></main>')
    info = scraper.parse_show_page(BeautifulSoup(html_dup, "html.parser"), "test3")
    assert info.warnings == "Sexual Content", info.warnings

    print("PASS: warnings parsing handles 'None', real values, and no-overwrite correctly")


def test_multi_fragment_venue():
    """A venue name split across nested inline tags (e.g. two <span>s around
    a '|') must still be captured as one venue and NOT drop the instance."""
    html = """
    <html><body><main>
    <h3>Wednesday, July 15</h3>
    <a href="https://hftco.ca/events/love-craic/"><img src="x.jpg"></a>
    <a href="https://hftco.ca/events/love-craic/">LOVE &amp; CRAIC</a>
    <span>The Staircase</span> <span>|</span> <span>Studio Theatre</span>
    <p>7.30pm</p>
    <a href="https://hftco.ca/events/love-craic/">book tickets &gt;</a>
    </main></body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    instances = scraper.parse_performances(soup)
    assert len(instances) == 1, f"expected 1 instance, got {len(instances)} -- venue split dropped it"
    assert instances[0].venue == "The Staircase | Studio Theatre", instances[0].venue
    assert instances[0].time_text == "7.30pm"
    print("PASS: venue text split across multiple fragments is joined correctly, instance not dropped")


def test_script_and_comment_immunity():
    """An inline <script> tag or an HTML comment sitting between the title
    link and the real venue text must not be read as the venue."""
    html = """
    <html><body><main>
    <h3>Wednesday, July 15</h3>
    <a href="https://hftco.ca/events/love-craic/"><img src="x.jpg"></a>
    <a href="https://hftco.ca/events/love-craic/">LOVE &amp; CRAIC</a>
    <script>var trackingId = "should not be captured as venue";</script>
    <!-- this is an HTML comment and should also be ignored -->
    <p>The Staircase | Studio Theatre</p>
    <p>7.30pm</p>
    <a href="https://hftco.ca/events/love-craic/">book tickets &gt;</a>
    </main></body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    instances = scraper.parse_performances(soup)
    assert len(instances) == 1, f"expected 1 instance, got {len(instances)}"
    assert instances[0].venue == "The Staircase | Studio Theatre", (
        f"script or comment content leaked into venue: {instances[0].venue!r}")
    print("PASS: inline <script> and HTML comment content correctly ignored")


def test_flag_before_time():
    """A flag token appearing BEFORE the time within a date's block (as seen
    in the printed program's per-show listings, e.g. 'TU 21 * 7:30PM') must
    still be attached to that specific instance, not dropped."""
    html = """
    <html><body><main>
    <h1>LOVE &amp; CRAIC</h1><h2>Squirrel Suit Productions</h2><h3>Hamilton, ON</h3>
    <p>Theatre-Comedy | 60m</p>
    <h3>July 21, 2026</h3>
    <a href="https://hftco.ca/venues/the-staircase">The Staircase</a>
    <p>RP</p>
    <h3>9.15pm</h3>
    <p>buy tickets</p>
    </main></body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    info = scraper.parse_show_page(soup, "test-flag-before-time")
    key = (7, 21, 21, 15)  # 9.15pm -> 21:15
    assert info.flags_by_key.get(key) == {"RP"}, info.flags_by_key
    print("PASS: flag appearing BEFORE the time is still attached to the correct instance")


def test_duration_formats():
    """Confirmed real formats: '60 min' (indoor), '3 hrs' / '2.5 hrs' (free
    outdoor events, decimal hours), and '75 min (hop on and off!)' (Fringe
    On The Streets -- trailing text after the unit)."""
    cases = [
        ("60 min", 60),
        ("20 min", 20),
        ("3 hrs", 180),
        ("2.5 hrs", 150),
        ("75 min (hop on and off!)", 75),
    ]
    for dur_text, expected_min in cases:
        html = (f'<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                f'<p>Genre:</p><p>G</p>'
                f'<h3>July 16, 2026</h3><p>Venue</p><h3>7.00pm</h3>'
                f'<p>{dur_text}</p><p>buy tickets</p></main>')
        info = scraper.parse_show_page(BeautifulSoup(html, "html.parser"), "dur-test")
        assert info.duration_min == expected_min, (
            f"{dur_text!r} -> expected {expected_min}, got {info.duration_min}")
    print("PASS: duration parsing handles min, hrs, decimal hrs, and trailing text")


def test_other_warnings_substitution():
    """Confirmed real pattern: the 'Warnings:' value can be the generic
    marker 'Other Warnings' alone, OR that marker mixed into a comma list
    alongside real categories (e.g. WOLFE's actual real value: 'Sexual
    Content, Coarse Language, Violence, Other Warnings'). Either way, a
    separate 'Other:' label holds the real detail that should replace it."""
    html_alone = ('<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                  '<p>Warnings:</p><p>Other Warnings</p>'
                  '<p>Other:</p><p>Could include mature content</p>'
                  '<p>Genre:</p><p>G</p></main>')
    info = scraper.parse_show_page(BeautifulSoup(html_alone, "html.parser"), "ow-test1")
    assert info.warnings == "Could include mature content", info.warnings

    html_mixed = ('<main><h1>T</h1><h2>C</h2><h3>O</h3>'
                  '<p>Warnings:</p><p>Sexual Content, Coarse Language, Violence, Other Warnings</p>'
                  '<p>Other:</p><p>Themes of sexual harassment</p>'
                  '<p>Genre:</p><p>G</p></main>')
    info = scraper.parse_show_page(BeautifulSoup(html_mixed, "html.parser"), "ow-test2")
    assert info.warnings == "Sexual Content, Coarse Language, Violence, Themes of sexual harassment", (
        info.warnings)
    print("PASS: 'Other Warnings' marker correctly substituted, both alone and mixed into a list")


def test_related_events_hard_stop():
    """CONFIRMED REAL BUG, found via real uploaded data: a free, single-
    instance event with NO block-end marker at all after its only instance
    (no 'buy tickets', no 'Get A Reminder', nothing) let the flag-scanning
    loop run straight into the page's footer boilerplate, which contains
    the sentence '...this year's selection of Mask-Mandatory performances,'
    and that got matched as a real MM flag on the last instance. This
    happened for real on the actual Bands on the Boulevard and Opening
    Night Kick-Off pages before the 'Related Events' hard stop was added."""
    html = """
    <html><body><main>
    <h1>Some Free Event</h1><h2>HFTco</h2><h3>Hamilton</h3>
    <p>Genre:</p><p>Free Outdoor Events</p>
    <h3>July 25, 2026</h3>
    <p>Fringe Boulevard</p>
    <h3>7.30pm</h3>
    <p>3 hrs</p>
    <p>Related Events</p>
    <p>HEALTH &amp; SAFETY GUIDELINES</p>
    <p>Check program listings for this year's selection of Mask-Mandatory performances.</p>
    </main></body></html>
    """
    info = scraper.parse_show_page(BeautifulSoup(html, "html.parser"), "no-marker-test")
    key = (7, 25, 19, 30)
    assert info.flags_by_key.get(key, set()) == set(), (
        f"footer boilerplate leaked into flags: {info.flags_by_key}")
    print("PASS: 'Related Events' hard stop prevents footer boilerplate from leaking into flags")


if __name__ == "__main__":
    main()
