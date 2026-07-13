# Migration Guide: Single Calendar → Multi-Filter Calendars

## What Changed

Your Fringe calendar scraper now generates **multiple `.ics` files** instead of one, each with a different filter applied. This lets you and your friends subscribe to exactly the shows you care about.

### Before
- One calendar: `fringe.ics`
- Contains everything (cancelled shows appear struck-through in your calendar app)
- You had to manually hide or ignore events you didn't want

### After
- Multiple calendars: `fringe-all.ics`, `fringe-no-cancelled.ics`, `fringe-plays-only.ics`, etc.
- Each calendar has only the events matching its filter
- You can subscribe to multiple calendars and mix/match filters in your calendar app
- Easy to share different URLs with different friends (e.g., "here's the outdoor events calendar")
- **You can add your own filters** in 2 minutes, no coding knowledge needed

---

## What to Replace in Your Repository

1. Replace `scraper.py` with the new version (includes filtering logic).
2. Replace `README.md` with `README_UPDATED.md` (or merge the new section).
3. Add three new documentation files:
   - `FILTERS_GUIDE.md` — How to create custom filters (detailed)
   - `FILTER_TEMPLATES.md` — 24 ready-to-use filters (copy & paste)
   - `MIGRATION_SUMMARY.md` — This file

**Your existing files (`test_offline.py`, `requirements.txt`, `.github/workflows/update-calendar.yml`) don't need to change.**

---

## Backward Compatibility

**Good news**: Your existing subscriptions will still work!

- If you or anyone was subscribed to `fringe.ics`, that URL still exists in the new version.
- It contains the same data as `fringe-all.ics` (everything, including cancelled).
- No one needs to re-subscribe or change anything.

However, if you want to use the new filtering features:
- Unsubscribe from `fringe.ics` (or keep it if you like seeing everything).
- Subscribe to a filtered calendar like `fringe-no-cancelled.ics` or `fringe-outdoor-only.ics`.

---

## New Calendar URLs

After you push the updated `scraper.py`, the workflow will generate these `.ics` files in `docs/`:

| Filename | URL | What It Contains |
|----------|-----|------------------|
| `fringe-all.ics` | `https://.../fringe-all.ics` | Everything, including cancelled shows |
| `fringe-no-cancelled.ics` | `https://.../fringe-no-cancelled.ics` | All shows except cancelled |
| `fringe-plays-only.ics` | `https://.../fringe-plays-only.ics` | Indoor theatre only (no street events) |
| `fringe-outdoor-only.ics` | `https://.../fringe-outdoor-only.ics` | Outdoor events only |

Each file is independent — you can subscribe to one, many, or all of them.

---

## How to Update Your Repository

### Step 1: Download the new files

You should have received:
- `scraper.py` (new version, ~800 lines)
- `README_UPDATED.md`
- `FILTERS_GUIDE.md`
- `FILTER_TEMPLATES.md`
- `MIGRATION_SUMMARY.md` (this file)

### Step 2: Replace and add files in your repo

1. Replace `scraper.py` with the new version.
2. Update `README.md`:
   - Option A: Replace it entirely with `README_UPDATED.md`.
   - Option B: Merge — copy the "What's New: Multiple Filtered Calendars" section and the "Creating Custom Filters" section into your existing README.
3. Add `FILTERS_GUIDE.md` to the root of your repository.
4. Add `FILTER_TEMPLATES.md` to the root.
5. Keep `test_offline.py`, `requirements.txt`, and `.github/workflows/update-calendar.yml` as-is.

### Step 3: Test locally (optional, but recommended)

```bash
python scraper.py --debug
```

This will:
- Fetch the live site.
- Generate `fringe-all.ics`, `fringe-no-cancelled.ics`, `fringe-plays-only.ics`, `fringe-outdoor-only.ics`.
- Generate debug CSVs.

Verify the output looks correct (check event counts, spot-check a few titles).

### Step 4: Commit and push

```bash
git add scraper.py README.md FILTERS_GUIDE.md FILTER_TEMPLATES.md
git commit -m "Add multi-filter calendar support"
git push
```

### Step 5: Run the workflow

1. Go to **Actions** → **Update Fringe calendar** → **Run workflow**.
2. Wait for it to finish (should take < 1 minute).
3. Verify the new `.ics` files appear in `docs/`:
   - `fringe-all.ics`
   - `fringe-no-cancelled.ics`
   - `fringe-plays-only.ics`
   - `fringe-outdoor-only.ics`

---

## Updating Your Calendar Subscriptions

### If you're the owner

1. Keep your existing `fringe.ics` subscription (it still works), OR
2. Unsubscribe from `fringe.ics` and subscribe to `fringe-no-cancelled.ics` instead (recommended).
3. Optionally, add another calendar for a different filter (e.g., `fringe-outdoor-only.ics`).

### If you're sharing with others

Send them the new calendar URLs that match their interests:

- **"Show me everything"** → `https://.../fringe-all.ics`
- **"Show me everything except cancelled"** → `https://.../fringe-no-cancelled.ics`
- **"I only like theatre, not street events"** → `https://.../fringe-plays-only.ics`
- **"I only like free outdoor stuff"** → `https://.../fringe-outdoor-only.ics`

They can unsubscribe from the old URL and subscribe to the new one, or keep both (calendars will overlap but that's fine).

---

## Adding Your First Custom Filter

Once you've migrated, you can easily add filters tailored to your interests. Here's the quickest example:

### Want a "comedy-only" calendar?

1. Open `scraper.py` in a text editor.
2. Find the line `FILTER_DEFINITIONS = {` (around line 233).
3. Add this before the closing `}`:

```python
    "comedy": {
        "description": "Comedy shows only",
        "filter_func": lambda inst, info: "comedy" in info.genre.lower(),
    },
```

4. Save the file.
5. Test: `python scraper.py --debug`
6. Verify `docs/fringe-comedy.ics` was created and contains comedy shows.
7. Commit and push: `git add scraper.py && git commit -m "Add comedy filter" && git push`
8. The workflow will generate `fringe-comedy.ics` from now on.
9. Share the URL: `https://.../fringe-comedy.ics`

**See `FILTERS_GUIDE.md` for 10+ detailed examples and step-by-step instructions.**

---

## What NOT to Change

- `test_offline.py` — No changes needed; it still tests the parsing logic.
- `requirements.txt` — No new dependencies.
- `.github/workflows/update-calendar.yml` — The workflow still works as-is.
- Existing scheduled runs — They'll automatically use the new multi-calendar setup.

---

## Troubleshooting

### "I pushed the new code but only see old `.ics` files in `docs/`"

The workflow hasn't run yet. Either:
1. Wait for the scheduled time (usually 12:00 UTC daily), or
2. Manually trigger it: **Actions** → **Update Fringe calendar** → **Run workflow**.

### "My custom filter didn't work"

See "Debugging a Filter" in `FILTERS_GUIDE.md`. Most common issues:
- Syntax error (check Python output for error message).
- Filter is too strict (generating very few or zero events).
- Misspelled field name or venue name.

### "The calendar app doesn't show the new calendars"

Your calendar app may cache the old URL. Try:
1. Unsubscribe from the old calendar.
2. Wait a few minutes.
3. Subscribe to the new URL.
4. Refresh your calendar app.

---

## Comparison: Old vs. New Workflow

### Old Workflow
1. Scraper generates `fringe.ics` with all 457 performances.
2. You subscribe to that one URL.
3. Cancelled shows appear as struck-through; you have to visually filter them.
4. To share with someone who only likes outdoor events, they get the same calendar and have to ignore what they don't want.

### New Workflow
1. Scraper generates `fringe-all.ics`, `fringe-no-cancelled.ics`, `fringe-plays-only.ics`, `fringe-outdoor-only.ics`, plus any custom filters you add.
2. You subscribe to the calendars that match your interests.
3. Cancelled shows are either present (in `fringe-all.ics`) or absent (in `fringe-no-cancelled.ics`), depending on your choice.
4. You can share different URLs with different friends: "outdoor events" URL for one, "plays at The Staircase" URL for another.
5. **Easy to add new filters**: edit one section of one file, save, push.

---

## Files You Now Have

### Core files (unchanged)
- `test_offline.py` — Regression tests
- `requirements.txt` — Dependencies
- `.github/workflows/update-calendar.yml` — CI workflow

### Updated files
- `scraper.py` — Now generates multiple filtered `.ics` files
- `README.md` — Updated to explain the new feature

### New documentation files
- `FILTERS_GUIDE.md` — Comprehensive guide to creating custom filters
- `FILTER_TEMPLATES.md` — 24 ready-to-use filter templates
- `MIGRATION_SUMMARY.md` — This file

---

## Next Steps

1. Replace `scraper.py` in your repository.
2. Update `README.md` (or add `README_UPDATED.md` content to it).
3. Add `FILTERS_GUIDE.md` and `FILTER_TEMPLATES.md` to your repository.
4. Run the workflow manually to test.
5. Verify the new `.ics` files appear in `docs/`.
6. Update your personal subscriptions to use `fringe-no-cancelled.ics` (or another filtered version).
7. Share new URLs with friends.
8. When you want a new filter, see `FILTERS_GUIDE.md` and add it to `FILTER_DEFINITIONS`.

Happy filtering! 🎭
