# Multi-Filter Fringe Calendar — Complete Deliverables

This package contains everything you need to upgrade your single Fringe calendar to a multi-filter setup, plus comprehensive documentation for adding your own filters.

---

## Files at a Glance

| File | Type | Purpose | For Whom |
|------|------|---------|----------|
| **scraper.py** | Python code | New scraper that generates multiple filtered calendars. **Replace your old one.** | Everyone |
| **README_UPDATED.md** | Documentation | Updated README explaining the multi-filter feature and new setup. Merge into your existing README or use as-is. | Repository maintainers |
| **QUICK_START.md** | Checklist | Step-by-step checklist to get everything running (15–30 minutes total). **Start here.** | You (for the first time) |
| **MIGRATION_SUMMARY.md** | Guide | What changed, backward compatibility, how to migrate. Explains the "why" and "what's different". | You (conceptual overview) |
| **FILTERS_GUIDE.md** | Tutorial | Comprehensive guide to understanding filters, available data, and creating custom ones. Includes 10+ examples. | You (when adding custom filters) |
| **FILTER_TEMPLATES.md** | Copy-paste | 24 ready-to-use filter templates. No explanation — just copy, paste, and go. | You (quick reference) |
| **INDEX.md** | This file | Navigation guide. You are here. | Everyone |

---

## Recommended Reading Order

### First Time Setup (30 minutes total)

1. **Start:** Read `QUICK_START.md` (the checklist)
   - Gives you a step-by-step plan with checkboxes
   - Takes 5 min to understand; execution takes ~30 min

2. **Understand:** Skim `MIGRATION_SUMMARY.md` (5 min)
   - Explains what changed and why
   - Describes backward compatibility
   - Shows before/after workflow

3. **Do:** Execute the checklist from `QUICK_START.md`
   - Upload files to GitHub
   - Run the workflow
   - Update your calendar subscriptions

### Adding Custom Filters (10–20 minutes per filter)

1. **Quick reference:** Look up your desired filter in `FILTER_TEMPLATES.md`
   - 24 ready-to-use filters with no explanation needed
   - Copy, paste, save, done

2. **Building from scratch:** Read `FILTERS_GUIDE.md`
   - Available data fields (what you can test)
   - 10+ detailed, worked examples
   - Common mistakes and debugging tips
   - Advanced techniques (AND/OR logic, nested conditions)

3. **Reference:** Keep `README_UPDATED.md` nearby
   - Explains the feature to users
   - Shows how to subscribe to different calendars

---

## The New Multi-Filter System

### What It Does

**Before**: One calendar file (`fringe.ics`) with all 457 performances.

**After**: Multiple calendar files, each with a different filter:
- `fringe-all.ics` — Everything (including cancelled shows)
- `fringe-no-cancelled.ics` — All except cancelled
- `fringe-plays-only.ics` — Indoor theatre only
- `fringe-outdoor-only.ics` — Outdoor free events only
- `fringe-YOUR-CUSTOM.ics` — Any filter you create

### Key Features

✅ **Pre-built filters** — 4 common filters included  
✅ **Custom filters** — Add your own in 2 minutes without coding  
✅ **Share different URLs** — Send "plays" URL to theater friends, "outdoor" URL to others  
✅ **Backward compatible** — Old `fringe.ics` still works  
✅ **One scrape, multiple outputs** — All calendars generated in one daily workflow run  
✅ **Automatic updates** — Runs daily, all calendars stay fresh  

---

## Quick Reference: Filter Examples

### Copy-Paste Ready (No Coding)
See **`FILTER_TEMPLATES.md`** for 24 ready-to-use filters, including:
- No cancelled shows
- Free only / Paid only
- Single venue (Staircase, Aquarius, Westdale, etc.)
- Indoor only / Outdoor only
- Evening shows / Afternoon shows / Morning shows
- Weekend only
- Shows with/without content warnings
- Special access flags (Relaxed, Mask-Mandatory, Affinity)
- Combinations (e.g., free + outdoor, evening + Staircase)

### Need to Write Your Own?
See **`FILTERS_GUIDE.md`** for:
- Available fields on each performance instance
- Available metadata from show detail pages
- 10+ detailed, worked examples
- Debugging techniques
- Common mistakes

---

## What to Do With Each File

### To Your Repository

1. **Replace** `scraper.py` with the new `scraper.py` (800 lines, includes filter logic)

2. **Update** `README.md`:
   - Option A: Use `README_UPDATED.md` as-is (complete replacement)
   - Option B: Merge — copy the sections "What's New" and "Creating Custom Filters" into your existing README

3. **Add** these documentation files to the root:
   - `FILTERS_GUIDE.md`
   - `FILTER_TEMPLATES.md`
   - (optional) `MIGRATION_SUMMARY.md`

4. **Keep unchanged**:
   - `test_offline.py` (no changes needed)
   - `requirements.txt` (no new dependencies)
   - `.github/workflows/update-calendar.yml` (still works as-is)

### For Your Own Reference

- **`QUICK_START.md`** — Keep this as a checklist for the first setup
- **`MIGRATION_SUMMARY.md`** — Reference if explaining the change to friends or collaborators
- **`FILTERS_GUIDE.md`** — Bookmark or print for when you want to add filters
- **`FILTER_TEMPLATES.md`** — Bookmark for quick copy-paste filter reference

---

## The Workflow

### Daily Automation (Unchanged)

1. GitHub Actions runs `update-calendar.yml` daily at 12:00 UTC
2. Script fetches `hftco.ca/performances/` and each show's detail page
3. Applies all filters defined in `FILTER_DEFINITIONS`
4. Writes multiple `.ics` files to `docs/`:
   - `fringe-all.ics`
   - `fringe-no-cancelled.ics`
   - `fringe-plays-only.ics`
   - `fringe-outdoor-only.ics`
   - `fringe-<your-custom>.ics` (any filters you added)
5. Commits changes if anything changed
6. Your calendar apps automatically sync the new `.ics` files (within hours)

---

## Common Questions

### Q: Will my existing subscriptions break?
**A:** No. The old `fringe.ics` URL still works (equivalent to `fringe-all.ics`). Existing subscribers see no change. They can optionally switch to a filtered calendar.

### Q: How many filters can I add?
**A:** Unlimited. Each filter adds one line to the dictionary and takes ~100ms to apply. Adding 100 filters would take ~10 seconds total.

### Q: Do I need to write Python code?
**A:** No. Most filters are one-liners you can copy from `FILTER_TEMPLATES.md`. For custom logic, see `FILTERS_GUIDE.md` — it's template-based, not traditional coding.

### Q: Can other people add filters to my calendar?
**A:** Only if they have write access to your GitHub repo. Otherwise, they'd have to ask you. (You could set up a form or just ask in email/Slack.)

### Q: What if I make a filter mistake?
**A:** The workflow tests the filter logic locally first (offline regression tests). If something's wrong, it logs a warning. You'll see it in the GitHub Actions log before anything goes live.

---

## File Sizes

- `scraper.py` — ~32 KB (main script, multi-filter logic)
- `README_UPDATED.md` — ~8 KB
- `FILTERS_GUIDE.md` — ~22 KB (detailed, example-heavy)
- `FILTER_TEMPLATES.md` — ~10 KB (24 templates)
- `MIGRATION_SUMMARY.md` — ~10 KB
- `QUICK_START.md` — ~6 KB
- **Total** — ~88 KB (all documentation)

---

## Support & Debugging

### Something went wrong?

1. **Check the GitHub Actions log:**
   - Go to **Actions** tab → latest run
   - Look for lines starting with `ERROR` or `WARNING`
   - Most issues surface there immediately

2. **Local testing:**
   ```bash
   python scraper.py --debug
   ```
   This generates debug CSVs you can inspect without touching the live site.

3. **Filter debugging:**
   - See "Debugging a Filter" in `FILTERS_GUIDE.md`
   - Most common issue: filter logic is too strict (resulting in 0 events)

4. **Still stuck?**
   - Re-read the relevant section in `FILTERS_GUIDE.md`
   - Check `FILTER_TEMPLATES.md` for a similar example
   - Inspect `debug_instances.csv` to understand your data

---

## What's Next?

1. **Read** `QUICK_START.md` (the checklist)
2. **Execute** the checklist (30 minutes)
3. **Verify** the workflow ran and generated all `.ics` files
4. **Update** your calendar subscriptions
5. **Share** the new URLs with friends
6. **When ready**: Add custom filters using `FILTERS_GUIDE.md` or `FILTER_TEMPLATES.md`

---

## File Manifest

```
Required to update your repo:
  ✓ scraper.py                    (replaces old scraper.py)
  ✓ README_UPDATED.md             (replaces or merges with README.md)
  ✓ FILTERS_GUIDE.md              (add to repo root)
  ✓ FILTER_TEMPLATES.md           (add to repo root)
  ✓ MIGRATION_SUMMARY.md          (optional, add to repo root)

For your reference:
  ✓ QUICK_START.md                (bookmark or print)
  ✓ INDEX.md                      (this file, bookmark)

Do NOT modify:
  — test_offline.py               (no changes needed)
  — requirements.txt              (no changes needed)
  — .github/workflows/update-calendar.yml  (no changes needed)
```

---

## Version Info

- **Scraper version:** 2.0 (multi-filter edition)
- **Python version:** 3.7+ (same as before)
- **Dependencies:** `requests`, `beautifulsoup4` (unchanged)
- **Festival:** Hamilton Fringe 2026 (July 15–26)
- **Compatible with:** Google Calendar, Apple Calendar, Outlook, most calendar apps that support `.ics` subscriptions

---

**You're all set. Start with `QUICK_START.md` and follow the checklist. Good luck!** 🎭
