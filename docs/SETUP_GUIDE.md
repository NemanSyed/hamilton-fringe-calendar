# Hamilton Fringe 2026 Calendar — Setup Guide

This walks through everything from "I have five files and a GitHub login" to
"I have a subscribed calendar that updates itself." No prior GitHub
experience needed beyond being able to log in.

Total time: about 15 minutes, most of it waiting for things to finish.

---

## Part 1 — Create the repository

1. Go to **github.com** and make sure you're logged in.
2. Click the **+** icon in the top-right corner of the page, then click
   **New repository**.
3. Fill in the form:
   - **Repository name**: type something like `hamilton-fringe-calendar`
     (no spaces — use hyphens).
   - **Description**: optional, skip it.
   - Make sure **Public** is selected (not Private). This matters — public
     repos get unlimited free GitHub Actions minutes and free GitHub Pages
     hosting, which is what makes this whole thing free.
   - Leave "Add a README file" **unchecked** — you're uploading your own
     files.
4. Click the green **Create repository** button at the bottom.

You'll land on an empty repository page. Keep this tab open.

---

## Part 2 — Upload the files

You should have five files/folders from me:
- `README.md`
- `scraper.py`
- `test_offline.py`
- `requirements.txt`
- a `.github` folder, which contains `workflows/update-calendar.yml` inside it

**The folder structure matters.** `update-calendar.yml` must end up at the
path `.github/workflows/update-calendar.yml` inside the repository — not
loose in the root. GitHub's web uploader preserves folder structure if you
drag a folder in, so the easiest path is:

1. On your empty repository page, click **uploading an existing file**
   (a blue link in the middle of the page — or use the "Add file" dropdown
   → **Upload files** if you don't see that link).
2. Drag all five items (the four files plus the `.github` folder) into the
   upload box at once. If your browser lets you drag a folder, do that — it
   keeps `.github/workflows/update-calendar.yml` in the right place
   automatically.
3. **Double-check the folder structure took**: after dropping the files,
   GitHub shows a file list before you commit. Confirm you see something
   like `.github/workflows/update-calendar.yml` listed — not just
   `update-calendar.yml` sitting by itself. If it looks wrong, remove it
   from the upload and try again, or see the "If drag-and-drop folder upload
   doesn't work" note below.
4. Scroll down to **Commit changes**. Leave the default message, make sure
   "Commit directly to the `main` branch" is selected, and click the green
   **Commit changes** button.

You should now see all five items listed in your repository, including the
`.github` folder.

### If drag-and-drop folder upload doesn't work

Some browsers only let you drag individual files, not folders, into GitHub's
upload box. If that happens:

1. Upload just the four top-level files first (`README.md`, `scraper.py`,
   `test_offline.py`, `requirements.txt`) and commit.
2. Back on the repository's main page, click **Add file** → **Create new
   file**.
3. In the "Name your file" box, type the full path including folders:
   `.github/workflows/update-calendar.yml` — GitHub automatically creates
   the folders when you type slashes in that box.
4. Open your local copy of `update-calendar.yml` in a text editor, copy all
   its contents, and paste them into the big text box on the GitHub page.
5. Scroll down and click **Commit changes**.

---

## Part 3 — Create the output folder

The workflow writes the finished calendar file to a `docs/` folder, which
needs to exist before the first run.

1. Click **Add file** → **Create new file**.
2. In the "Name your file" box, type: `docs/.gitkeep`
   (this creates an empty placeholder file just so the folder exists —
   the content box can stay blank).
3. Click **Commit changes**.

---

## Part 4 — Enable GitHub Pages

This is what turns the generated calendar file into a URL you can subscribe
to.

1. On your repository page, click **Settings** (top menu bar, near the
   right side — you may need to click a **⚙** or scroll the tab bar if
   your window is narrow).
2. In the left sidebar, click **Pages**.
3. Under "Build and deployment," find the **Source** dropdown and make sure
   it says **Deploy from a branch**.
4. Just below that, there are two dropdowns: **Branch**. Set the first one
   to `main` and the second (folder) one to `/docs`.
5. Click **Save**.
6. GitHub will show a message like "Your site is live at
   `https://YOUR-USERNAME.github.io/hamilton-fringe-calendar/`" — this may
   take a minute or two to appear after saving. **Write this URL down** —
   you'll need it in Part 6.

---

## Part 5 — Run it for the first time

1. Click the **Actions** tab (top menu bar, same row as Settings).
2. If you see a message about workflows needing to be enabled, click the
   green button to enable them.
3. In the left sidebar, click **Update Fringe calendar**.
4. On the right side, click the **Run workflow** dropdown button, then
   click the green **Run workflow** button that appears.
5. A new run will appear in the list below, with a yellow dot (running).
   Click on it to watch progress. It should take under a minute.
6. When it finishes, you'll see a green checkmark. If instead you see a red
   ✕, click into the run and read the log — see "If it fails" below.

### Checking the results before you trust it

1. Go back to your repository's main **Code** tab.
2. You should now see two new files in the root: `debug_instances.csv` and
   `debug_flags.csv`, plus a `fringe.ics` file inside the `docs/` folder.
3. Click on `debug_instances.csv`, then click the **Raw** button to see the
   plain data, or just view it in GitHub's built-in table view. Spot-check
   a few rows against **https://hftco.ca/performances/** open in another
   tab — do the dates, titles, venues, and times match?
4. Click on `debug_flags.csv` and spot-check it against a show you know has
   a Relaxed Performance, Mask-Mandatory Performance, or Affinity
   Performance — does the flag show up on the right specific date?
5. If everything looks right, you're good to move to Part 6. If something
   looks wrong, see "If something looks wrong" below before subscribing.

### If it fails

Click into the failed run, then click the job name to expand the log.
Scroll to find lines starting with `ERROR` or a Python traceback (a block of
red-ish text ending in a line like `SomeError: message`). That tells you
what broke. Two likely causes:
- **`test_offline.py` failed**: the workflow is designed to stop before
  touching the live site if this happens, which means something about the
  code itself needs a fix, not the site.
- **A network/connection error fetching hftco.ca**: could be temporary —
  try **Run workflow** again.

---

## Part 6 — Subscribe in your calendar app

Take the Pages URL from Part 4 (something like
`https://YOUR-USERNAME.github.io/hamilton-fringe-calendar/`) and add
`fringe.ics` to the end of it:

```
https://YOUR-USERNAME.github.io/hamilton-fringe-calendar/fringe.ics
```

How you subscribe depends on your calendar app:

- **Apple Calendar (Mac)**: File menu → New Calendar Subscription → paste
  the URL (you can use `webcal://` instead of `https://` at the start, both
  work) → Subscribe.
- **Apple Calendar (iPhone/iPad)**: Settings app → Calendar → Accounts →
  Add Account → Other → Add Subscribed Calendar → paste the URL.
- **Google Calendar**: on the Google Calendar website, click the **+** next
  to "Other calendars" in the left sidebar → **From URL** → paste the URL
  → Add calendar. (Google's app doesn't support adding a URL directly on
  mobile — subscribe on the website once and it syncs to your phone
  automatically.)
- **Outlook**: Add calendar → Subscribe from web → paste the URL.

The calendar will appear as "Hamilton Fringe 2026 (unofficial)" with every
performance as a separate entry, including venue address, content warnings,
special-performance flags, description, and a link back to the ticket page.

---

## Part 7 — Sharing it with friends

The URL from Part 6 is just a normal web link — send it to anyone the same
way, and they subscribe using the same steps as Part 6 on their own device.
Nothing personal is attached to it; it's just the public festival schedule.

---

## What happens automatically from here

The workflow is scheduled to re-run once a day on its own (see the `cron`
line in `update-calendar.yml` if you want to change the time — it's in UTC).
Each run re-scrapes the live site, regenerates `fringe.ics`, and commits it
only if something actually changed (a new cancellation, a rename, a time
change, etc.). Your calendar app re-checks the subscribed URL periodically
on its own schedule (usually every few hours) and picks up updates — you
don't need to do anything.

You can also trigger it manually anytime via **Actions** → **Update Fringe
calendar** → **Run workflow**, the same as Part 5, if you want to force an
immediate refresh.

---

## If something looks wrong

- Re-read the specific row in `debug_instances.csv` or `debug_flags.csv`
  that looks off, and compare it against the same show/date on
  https://hftco.ca directly.
- Check the Action's log (Actions tab → the run in question) for `WARNING`
  lines — the scraper logs a specific warning every time it couldn't parse
  something cleanly, rather than failing silently.
- If a specific venue is missing its address, check the `VENUE_ADDRESSES`
  dictionary near the top of `scraper.py` — it may need a new entry if
  HFTco adds a venue that wasn't in this year's printed program.
