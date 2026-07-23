# Quick-Start Checklist: Multi-Filter Calendars

Copy this checklist into a TODO app or print it out. Check off each step as you complete it.

---

## Phase 1: Update Your Repository (15 minutes)

- [ ] **Download the new files** from your Claude chat:
  - [ ] `scraper.py` (new version, replaces old)
  - [ ] `README_UPDATED.md` (merge or replace old README)
  - [ ] `FILTERS_GUIDE.md` (new, add to repo)
  - [ ] `FILTER_TEMPLATES.md` (new, add to repo)
  - [ ] `MIGRATION_SUMMARY.md` (new, add to repo)

- [ ] **Update your repository**:
  - [ ] Replace `scraper.py` with the new version
  - [ ] Update `README.md` with new content (or use `README_UPDATED.md` as-is)
  - [ ] Add `FILTERS_GUIDE.md` to the root
  - [ ] Add `FILTER_TEMPLATES.md` to the root
  - [ ] (optional) Add `MIGRATION_SUMMARY.md` to the root

- [ ] **Commit and push**:
  ```bash
  git add scraper.py README.md FILTERS_GUIDE.md FILTER_TEMPLATES.md
  git commit -m "Add multi-filter calendar support"
  git push
  ```

---

## Phase 2: Test the Workflow (5 minutes)

- [ ] Go to your GitHub repository → **Actions** tab
- [ ] Click **Update Fringe calendar**
- [ ] Click **Run workflow** (green button on the right)
- [ ] Wait for it to finish (should take < 1 minute)
- [ ] ✅ Check: All jobs passed (green checkmarks)

---

## Phase 3: Verify Output (5 minutes)

- [ ] Go to **Code** tab → **docs** folder
- [ ] Verify these files exist:
  - [ ] `fringe-all.ics`
  - [ ] `fringe-no-cancelled.ics`
  - [ ] `fringe-plays-only.ics`
  - [ ] `fringe-outdoor-only.ics`

- [ ] Open one file (e.g., `fringe-no-cancelled.ics`) and spot-check:
  - [ ] Look for `BEGIN:VEVENT` entries
  - [ ] No "CANCELLED" entries should appear in this file
  - [ ] Dates should match July 15–26, 2026

- [ ] Open `debug_instances.csv` (should exist in root):
  - [ ] Spot-check a few rows against https://hftco.ca/performances/
  - [ ] Dates, venues, times should match

---

## Phase 4: Update Your Calendar Subscriptions (5 minutes)

Choose one of these options:

### Option A: Keep existing subscription (simplest)
- [ ] Keep subscribing to `fringe.ics` (still works, same as `fringe-all.ics`)
- [ ] Nothing else to do!

### Option B: Switch to filtered subscription (recommended)
- [ ] Unsubscribe from old `fringe.ics` URL in your calendar app
- [ ] Subscribe to new URL: `https://nemansyed.github.io/<repo-name>/fringe-no-cancelled.ics`
- [ ] Verify it appears in your calendar with correct events

### Option C: Subscribe to multiple calendars (advanced)
- [ ] Subscribe to `fringe-no-cancelled.ics` (your main calendar)
- [ ] Also subscribe to `fringe-outdoor-only.ics` (to see free outdoor events)
- [ ] Both calendars now appear side-by-side in your calendar app

---

## Phase 5: Share With Friends (2 minutes)

- [ ] Send your friends the new calendar URLs based on their interests:
  - **"Everything"** → `https://NemanSyed.github.io/hamilton-fringe-calendar/fringe-all.ics`
  - **"No cancelled"** → `https://NemanSyed.github.io/hamilton-fringe-calendar/fringe-no-cancelled.ics`
  - **"Plays only"** → `https://NemanSyed.github.io/hamilton-fringe-calendar/fringe-plays-only.ics`
  - **"Outdoor only"** → `https://NemanSyed.github.io/hamilton-fringe-calendar/fringe-outdoor-only.ics`
- [ ] Let them know they can also subscribe to multiple calendars at once

---

## Phase 6 (Optional): Add Your First Custom Filter (10 minutes)

Want to add a filter, e.g., "comedy-only"? Here's the quick version:

- [ ] Open `scraper.py` in a text editor
- [ ] Find the line `FILTER_DEFINITIONS = {` (around line 233)
- [ ] Copy one of the existing filters (e.g., `"plays-only"`)
- [ ] Paste it, change the name and description, modify the condition
- [ ] Save the file
- [ ] Test locally (optional):
  ```bash
  python scraper.py --debug
  ```
  - [ ] Check that `docs/fringe-<new-filter-name>.ics` was created
  - [ ] Spot-check the content

- [ ] Commit and push:
  ```bash
  git add scraper.py
  git commit -m "Add <filter-name> filter"
  git push
  ```

- [ ] Wait for workflow to run (automatic, or manually trigger)
- [ ] Verify the new `.ics` file appears in `docs/`
- [ ] Share the new URL with interested friends

**👉 See `FILTERS_GUIDE.md` for 10+ detailed filter examples and explanations.**

---

## Troubleshooting

### "The workflow failed"
- [ ] Go to **Actions** → **Update Fringe calendar** → latest run
- [ ] Click the job name to expand the log
- [ ] Look for lines starting with `ERROR` or `WARNING`
- [ ] Most common: syntax error in a custom filter (see FILTERS_GUIDE.md)

### "I don't see the new `.ics` files in `docs/`"
- [ ] Did you wait for the workflow to finish? (Check Actions tab)
- [ ] Did you commit and push your changes? (Check recent commits)
- [ ] Manually trigger the workflow: **Actions** → **Update Fringe calendar** → **Run workflow**

### "My custom filter didn't work"
- [ ] Check for Python syntax errors (red text in log output)
- [ ] Run locally first: `python scraper.py --debug`
- [ ] See "Debugging a Filter" section in `FILTERS_GUIDE.md`

### "Calendar app doesn't show new calendars"
- [ ] Unsubscribe from the old URL
- [ ] Wait 5 minutes
- [ ] Manually refresh your calendar app (pull down to refresh)
- [ ] Subscribe to the new URL
- [ ] Wait another 5 minutes for calendar app to sync

---

## You're Done! 🎉

Your multi-filter calendar is now live. 

- **Current setup**: 4 pre-built filters (all, no-cancelled, plays-only, outdoor-only)
- **Next time**: Add custom filters following `FILTERS_GUIDE.md`
- **Remember**: The workflow runs automatically daily at 12:00 UTC

Enjoy sharing festival schedules with your friends! 🎭
