# Multi-Filter Fringe Calendar — Delivered

Hi Neman,

I've created a complete multi-filter calendar system for your Hamilton Fringe 2026 scraper, plus comprehensive documentation for adding custom filters yourself. Here's what you got.

---

## What's Been Delivered

### 1. Enhanced Scraper (scraper.py)
**The main code** — generates multiple filtered `.ics` files instead of one:
- `fringe-all.ics` (everything, including cancelled)
- `fringe-no-cancelled.ics` (everything except cancelled)
- `fringe-plays-only.ics` (indoor theatre, no street events)
- `fringe-outdoor-only.ics` (outdoor free events)

**Key improvements**:
- All filters defined in one clear dictionary (`FILTER_DEFINITIONS`)
- Each filter is a simple one-liner you can copy/modify
- Pre-built with four common filters ready to go
- Backward compatible — `fringe.ics` still exists for old subscriptions

### 2. Documentation (5 files)

| File | Purpose | When to Read |
|------|---------|-------------|
| **QUICK_START.md** | Step-by-step checklist (first time setup) | Before you do anything |
| **MIGRATION_SUMMARY.md** | What changed, why, backward compatibility | To understand the shift |
| **README_UPDATED.md** | Replacement for README.md | When updating your repo |
| **FILTERS_GUIDE.md** | Tutorial on creating custom filters (10+ examples) | When adding your own filters |
| **FILTER_TEMPLATES.md** | 24 ready-to-use copy-paste filters | Quick reference |
| **INDEX.md** | Navigation guide to all files | To find what you need |

### 3. How to Use It

**For initial setup** (one time, ~30 min):
1. Follow the checklist in `QUICK_START.md`
2. Replace `scraper.py`, update `README.md`, add documentation files
3. Commit, push, run the workflow
4. Verify 4 new `.ics` files appear in `docs/`
5. Update your subscriptions (or keep the old one — it still works)

**For adding custom filters** (2–10 min each):
1. Think of what you want (e.g., "comedy-only", "evening-shows", "staircase-only")
2. Look it up in `FILTER_TEMPLATES.md` or write one using `FILTERS_GUIDE.md`
3. Add 5 lines to `scraper.py`'s `FILTER_DEFINITIONS` dictionary
4. Test locally, commit, push
5. New calendar appears in `docs/` automatically

---

## The Problem It Solves

### Before
- One calendar with 457 performances
- Cancelled shows appear struck-through; you have to ignore them manually
- Hard to share with friends who only want (e.g.) outdoor events — they get everything
- No easy way to filter by venue, time, price, genre, etc.

### After
- Multiple calendars, each with a specific filter
- Cancelled shows either present (all.ics) or absent (no-cancelled.ics) — client's choice
- Send different friends different URLs based on their interests
- **Easy to add new filters** — no coding knowledge needed, just copy-paste and customize

---

## Key Features

✅ **4 pre-built filters** included (all, no-cancelled, plays-only, outdoor-only)  
✅ **Easy to extend** — add your own filters by editing one section of one file  
✅ **Copy-paste templates** — 24 ready-to-use filters in FILTER_TEMPLATES.md  
✅ **Detailed guidance** — FILTERS_GUIDE.md walks through available data and 10+ examples  
✅ **Backward compatible** — existing `fringe.ics` subscription still works  
✅ **Automatic daily updates** — all calendars regenerated in one workflow run  
✅ **Zero new dependencies** — same `requests` and `beautifulsoup4` as before  

---

## Available Filter Criteria

Use any of these to build filters:

```python
inst.cancelled          # bool: True if marked CANCELLED
inst.venue              # str: "The Staircase | Studio Theatre"
inst.clean_title        # str: show name
inst.time_text          # str: "7:30pm"
inst.date_text          # str: "Wednesday, July 15"
inst.local_key          # tuple: (month, day, hour, minute) for advanced time filtering

info.genre              # str: "Comedy", "Theatre", "Music", etc.
info.price              # str: "Free", "$20", "$15–$25", etc.
info.company            # str: company name
info.warnings           # str: content warnings
info.flags_by_key       # dict: special flags (RP/MM/AP) by date/time
```

---

## Five-Minute Example

**Want a "comedy-only" calendar?**

1. Open `scraper.py`
2. Find `FILTER_DEFINITIONS = {` (around line 233)
3. Add this before the closing `}`:

```python
    "comedy": {
        "description": "Comedy shows only",
        "filter_func": lambda inst, info: "comedy" in info.genre.lower(),
    },
```

4. Save
5. Commit and push (or test locally with `python scraper.py --debug` first)
6. Done. `fringe-comedy.ics` will be generated automatically on the next workflow run.

---

## Files to Use in Your Repo

**Replace/Update**:
- Replace `scraper.py` (the main script)
- Update `README.md` (use content from `README_UPDATED.md`)

**Add**:
- `FILTERS_GUIDE.md` (detailed how-to)
- `FILTER_TEMPLATES.md` (24 copy-paste filters)

**Keep as-is** (no changes):
- `test_offline.py`
- `requirements.txt`
- `.github/workflows/update-calendar.yml`

---

## Why This Approach?

I chose **filters in a dictionary** (not a config file, not command-line args) because:

1. **Self-documenting** — each filter shows its logic right there
2. **Copy-paste friendly** — take a template, modify the lambda, done
3. **No external config** — everything in one Python file, no separate YAML/JSON to sync
4. **Testable** — you can run `python scraper.py --debug` to test before committing
5. **Scalable** — from 4 pre-built filters to unlimited custom ones

The filter function takes `(inst, info)` because that matches how the scraper works: each performance instance gets matched against show metadata, and the filter decides include/exclude.

---

## Next Steps

1. Read `QUICK_START.md` (it's a checklist with time estimates)
2. Execute the checklist (30 min total)
3. Verify 4 new `.ics` files in GitHub Pages
4. Update your calendar subscriptions
5. Share new URLs with friends who might want filtered views
6. When ready to add custom filters, use `FILTERS_GUIDE.md` or `FILTER_TEMPLATES.md`

---

## If You Hit Issues

**Workflow failed?**
- Check GitHub Actions log for `ERROR` or `WARNING` lines
- Most likely: syntax error in a custom filter

**Custom filter not working?**
- Test locally: `python scraper.py --debug`
- Check `debug_instances.csv` to understand your data
- See "Debugging a Filter" in `FILTERS_GUIDE.md`

**Subscription not updating?**
- Unsubscribe from old URL, wait 5 min, re-subscribe to new URL
- Calendar apps cache for a few hours — be patient

---

## One Last Thing: UTC vs. Local Time

You mentioned Google Calendar shows UTC as the timezone but events appear in the right place. That's exactly right — the scraper converts Eastern (EDT, UTC-4) → UTC for the .ics file, and Google Calendar converts back to your local timezone for display. **No changes needed.** The times are correct; Google's UI label is just a bit misleading.

---

## You've Got All You Need

You now have:
- A production-ready multi-filter scraper
- Four pre-built filters
- Documentation on adding custom filters (copy-paste templates + detailed guide)
- A checklist for first-time setup
- A migration guide explaining what changed

No coding knowledge required to add new filters. The `FILTER_TEMPLATES.md` file is specifically designed so you can grab a template, change the name/description/condition, and you're done.

Happy filtering! 🎭

— Claude
