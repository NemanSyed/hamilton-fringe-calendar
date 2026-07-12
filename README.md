# Hamilton Fringe 2026 — Unofficial Subscribed Calendar

Scrapes the live, official schedule from hftco.ca daily and publishes it as a
webcal:// subscription, so a calendar app always shows the current lineup —
including cancellations and renames — without manual re-import.

**This is not affiliated with or endorsed by Hamilton Festival Theatre
Company.** It just reads their public website. If HFTco changes their site
layout, the scraper may need small fixes (see "If something breaks" below).

## One-time setup (about 10 minutes)

1. **Create the repo.** On GitHub, create a new **public** repository (public
   is what makes GitHub Actions and Pages free with no minute limits — see
   note below). Upload all the files in this folder, preserving the
   `.github/workflows/` and `docs/` folder structure.

2. **Enable GitHub Pages.**
   - Go to the repo's **Settings → Pages**.
   - Under "Build and deployment", set **Source** to "Deploy from a branch".
   - Set **Branch** to `main` and folder to `/docs`, then Save.
   - GitHub will give you a URL like
     `https://<your-username>.github.io/<repo-name>/`.

3. **Run the workflow once manually.**
   - Go to the **Actions** tab → "Update Fringe calendar" → **Run workflow**.
   - This first runs `test_offline.py` — a self-contained logic test with no
     network calls, checking things like cancellation/rename parsing, per-
     instance flag matching, and UTC time conversion against known-correct
     examples pulled from the real site. If this fails, the workflow stops
     before touching the live site or committing anything.
   - It then scrapes hftco.ca for real and commits `docs/fringe.ics`.
   - **Check `debug_instances.csv`** (every parsed performance: date, title,
     cancelled/renamed status, venue, time) against
     https://hftco.ca/performances/, and **`debug_flags.csv`** (every
     RP/MM/AP flag found, tied to a specific show + date + time) against a
     show page you know has special performances. If something looks wrong,
     see "If something breaks" below.

4. **Subscribe in your calendar app.** Your feed URL is:
   ```
   https://<your-username>.github.io/<repo-name>/fringe.ics
   ```
   Use `webcal://` instead of `https://` for apps that recognize it directly
   (Apple Calendar, some others), or use the "subscribe by URL" / "add
   calendar from URL" option in Google Calendar, Outlook, etc. and paste the
   `https://` link.

5. **Share it.** The URL above is public — hand it to anyone. They subscribe
   the same way. Nothing personal is in the feed; it's just the public
   festival schedule.

After this, it runs itself: the Action re-scrapes daily at 12:00 UTC and
pushes an updated `fringe.ics` if anything changed. Your subscribed calendar
app re-checks the URL periodically (interval varies by app, typically
every few hours) and picks up the changes automatically.

## Cost

Free. Public repos get unlimited GitHub Actions minutes on standard runners,
and GitHub Pages is free for public repos. A daily run of this script takes
well under a minute.

## If something breaks

The scraper works by walking hftco.ca's page structure using patterns like
"the text right after a show's title link is the venue, then the time" —
it doesn't depend on guessed CSS class names, which makes it fairly resilient,
but not immune to layout changes. If the debug CSVs look wrong after a site
update:

- Check the Action's log output (Actions tab → latest run) — it logs a
  specific warning for every row, venue, or flag it couldn't parse cleanly,
  rather than failing silently.
- Run `python test_offline.py` locally — it exercises the parsing logic
  against fixed sample data with no network dependency, so it isolates
  whether a bug is in the parsing *logic* vs. a live *site change*.
- Re-run `python scraper.py --debug` locally (or via "Run workflow") after
  any fix, and check both debug CSVs before trusting it live.

## Development notes

`test_offline.py` is an offline regression test: it builds synthetic HTML
matching hftco.ca's confirmed structure and runs the real parsing functions
against it, with no network access. It specifically checks that RP/MM/AP
flags do **not** leak between performance instances of the same show — since
those flags are irregular (present on some dates/times, absent on others),
that was the trickiest part to get right. It also round-trips the generated
calendar through the independent `icalendar` Python library to catch RFC 5545
formatting mistakes my own code might not notice in itself.

The CI workflow runs this test before every live scrape and refuses to
proceed if it fails — so a future edit that breaks the parsing logic won't
silently corrupt the published calendar.

## What's included in each calendar entry

- Show title (with CANCELLED / renamed status reflected live)
- Venue name + street address
- Date/time/duration, one entry per performance instance
- Content warnings
- Relaxed Performance / Mask-Mandatory / Affinity Performance flags, per
  specific instance (confirmed against a real show with irregular flags
  across its run — see "Confidence level" below)
- Genre, short description, price, and a link back to the ticket page

**Deliberately excluded** (per your scope): age ratings, physical/wheelchair
accessibility.

## Confidence level

This scraper has been validated against real, saved HTML from hftco.ca
across a broad sample of event types — not just one show. Confirmed
correct: the live `/performances/` listing (457 instances, zero parse
warnings, all 12 festival dates found), a paid indoor show with irregular
flags across its run (all 10 dates matched the printed program exactly), a
show with all three flag types — Affinity, Relaxed, and Mask-Mandatory —
each on a different specific date, two free outdoor events with no ticket
link at all, a cancelled show, and a multi-stop walking tour with same-day
repeat showtimes.

That second round of real data caught five more real bugs a single example
couldn't have: duration given in hours as well as minutes (including
decimals and trailing text like "75 min (hop on and off!)"), a warnings
value that's sometimes a generic "Other Warnings" marker needing
substitution from a separate detail field, a block-end marker that varies
by event type, and — the most serious one — free single-instance events
with no block-end marker at all, which let flag-detection run into the
page's own footer text and misread a sentence about "Mask-Mandatory
performances" as a real flag. All five are fixed and locked in with
dedicated regression tests.

Still unverified: the live network fetch itself, as opposed to parsing a
saved copy of the response — that's what the first real workflow run is for.
