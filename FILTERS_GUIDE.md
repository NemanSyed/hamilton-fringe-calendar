# Adding Custom Filters to Your Fringe Calendar

This guide shows you how to create new filtered calendars (e.g., only comedy shows, only evening performances, only venues on King Street) without touching any code outside the `FILTER_DEFINITIONS` section.

---

## Quick Start: Add Your First Filter

1. Open `scraper.py` in a text editor.
2. Find the section labeled `FILTER_DEFINITIONS` (around line 233–300).
3. Add a new filter entry inside the `FILTER_DEFINITIONS` dictionary.
4. Test locally, then commit and push.

---

## The Filter Template

Each filter is a Python dictionary with three required keys:

```python
"my-filter-name": {
    "description": "Human-readable explanation of what this filter does",
    "filter_func": lambda inst, info: CONDITION_HERE,
}
```

### Parts of a filter:

- **`"my-filter-name"`**: A unique, kebab-case name (lowercase, hyphens, no spaces).
  - This becomes part of the filename: `fringe-my-filter-name.ics`
  - It's what you share with others: `https://yoursite/fringe-my-filter-name.ics`
  - Example: `"staircase-only"`, `"evening-shows"`, `"free-only"`

- **`"description"`**: A short string (one sentence) explaining the filter.
  - Appears in the log output when the scraper runs.
  - Helps you remember what this calendar is for.
  - Example: `"Only performances at The Staircase venue"`

- **`"filter_func"`**: A function (written as a `lambda` for simplicity) that decides whether to include an instance.
  - Takes two parameters: `inst` (the performance instance) and `info` (show metadata).
  - Returns `True` to **include** the instance, `False` to **exclude** it.
  - Example: `lambda inst, info: not inst.cancelled` (include only non-cancelled)

---

## Available Data: What You Can Test

Inside your filter function, you have access to these fields:

### On `inst` (the performance instance):
| Field | Type | Example | Use |
|-------|------|---------|-----|
| `inst.cancelled` | bool | `True` or `False` | Filter out cancelled shows |
| `inst.venue` | str | `"The Staircase \| Studio Theatre"` | Filter by venue name |
| `inst.clean_title` | str | `"Laughs in the Dark"` | Filter by show title |
| `inst.date_text` | str | `"Wednesday, July 15"` | Filter by date (rare) |
| `inst.time_text` | str | `"7:30pm"` or `"19:30"` | Filter by time |
| `inst.href` | str | `"https://hftco.ca/events/show-slug/"` | Filter by show URL |
| `inst.local_key` | tuple | `(7, 15, 19, 30)` | Month, day, 24h-hour, minute |

### On `info` (show metadata, from the detail page):
| Field | Type | Example | Use |
|-------|------|---------|-----|
| `info.genre` | str | `"Comedy"`, `"Theatre"`, `"Music"` | Filter by genre |
| `info.company` | str | `"Red Rope Theatre"` | Filter by company |
| `info.price` | str | `"Free"`, `"$20"`, `"$15–$25"` | Filter by ticket price |
| `info.warnings` | str | `"Strong language, violence"` | Filter by content warnings |
| `info.description` | str | Long text... | Filter by description keywords |
| `info.flags_by_key` | dict | `{(7,15,19,30): {"RP", "AP"}}` | Filter by special flags (RP/MM/AP) |

---

## Example Filters

### 1. Exclude cancelled shows
```python
"no-cancelled": {
    "description": "All performances except cancelled",
    "filter_func": lambda inst, info: not inst.cancelled,
}
```
**Logic**: Return `True` if the instance is NOT cancelled.

---

### 2. Only a specific venue
```python
"staircase-only": {
    "description": "Only performances at The Staircase",
    "filter_func": lambda inst, info: "The Staircase" in inst.venue,
}
```
**Logic**: Check if the venue name contains the string "The Staircase".
- ✅ Includes all Staircase rooms (Studio Theatre, Bright Room, Elaine May)
- Uses `in` because the full venue name is "The Staircase | Studio Theatre", etc.

---

### 3. Only free outdoor events
```python
"outdoor-only": {
    "description": "Free outdoor events only (Fringe On The Streets, Fringe Boulevard)",
    "filter_func": lambda inst, info: any(
        venue_keyword in inst.venue
        for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
    ),
}
```
**Logic**: Return `True` if the venue contains ANY of the keywords in the list.
- `any()` returns `True` if at least one condition is true.
- This is cleaner than: `"Fringe On The Streets" in inst.venue or "Fringe Boulevard" in inst.venue`

---

### 4. Only performances with special flags (Relaxed Performance, Affinity, etc.)
```python
"affinity-only": {
    "description": "Only Affinity Performances (AP flag)",
    "filter_func": lambda inst, info: "AP" in info.flags_by_key.get(inst.local_key, set()),
}
```
**Logic**: 
- `inst.local_key` is the (month, day, hour, minute) of this performance.
- `info.flags_by_key` is a dictionary mapping that key to a set of flags like `{"RP"}`, `{"MM"}`, `{"AP"}`, etc.
- `.get(inst.local_key, set())` returns the set of flags for this instance, or an empty set if not found.
- `"AP" in ...` checks if the Affinity Performance flag is in that set.

Variations:
```python
# Only Relaxed Performances
"relaxed-only": {
    "description": "Only Relaxed Performances (RP flag)",
    "filter_func": lambda inst, info: "RP" in info.flags_by_key.get(inst.local_key, set()),
}

# Only shows with ANY special flag (RP, MM, or AP)
"special-flags": {
    "description": "Only performances with special flags (RP, MM, or AP)",
    "filter_func": lambda inst, info: bool(info.flags_by_key.get(inst.local_key, set())),
}
```

---

### 5. Only indoor theatre (exclude Fringe On The Streets)
```python
"plays-only": {
    "description": "Indoor theatre only, excludes street/outdoor events",
    "filter_func": lambda inst, info: not any(
        venue_keyword in inst.venue
        for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
    ),
}
```
**Logic**: Exclude venues that contain either keyword.
- Uses `not any()` to invert the logic: "NOT any of these venues".

---

### 6. Only shows by price
```python
"free-only": {
    "description": "Only free performances",
    "filter_func": lambda inst, info: "free" in info.price.lower(),
}
```
**Logic**: Check if the word "free" appears anywhere in the price string (case-insensitive).
- `.lower()` converts "Free" → "free" for matching.
- ✅ Catches "Free", "FREE", "Free – $5 suggested donation", etc.

Paid shows:
```python
"paid-only": {
    "description": "Only paid performances (excludes free)",
    "filter_func": lambda inst, info: info.price and "free" not in info.price.lower(),
}
```

---

### 7. Only comedy
```python
"comedy-only": {
    "description": "Comedy shows only",
    "filter_func": lambda inst, info: "comedy" in info.genre.lower(),
}
```
**Logic**: Check if the genre contains "comedy" (case-insensitive).
- `.lower()` handles "Comedy", "COMEDY", etc.
- Note: You may need to check real genre values on hftco.ca to know what strings to match. Use `--debug` mode to see all genres in `debug_instances.csv`.

---

### 8. Only evening shows (7pm or later)
```python
"evening-only": {
    "description": "Only shows at 7pm or later",
    "filter_func": lambda inst, info: (
        inst.local_key is not None and
        inst.local_key[2] >= 19  # hour index is [2] in (month, day, hour, minute)
    ),
}
```
**Logic**:
- `inst.local_key` is a tuple: `(month, day, hour_24, minute)`.
- Index [2] is the 24-hour hour.
- `>= 19` means 7pm or later (19:00 in 24-hour time).

Variations:
```python
# Only afternoon shows (noon–6pm)
"afternoon-only": {
    "description": "Afternoon shows only (12pm–6pm)",
    "filter_func": lambda inst, info: (
        inst.local_key is not None and
        12 <= inst.local_key[2] < 18
    ),
}

# Only weekend shows (Saturdays and Sundays)
# Note: date_text includes the weekday name; July 15-26, 2026 are Wed–Sun
"weekend-only": {
    "description": "Weekend shows only (Saturday and Sunday)",
    "filter_func": lambda inst, info: inst.date_text.startswith(("Saturday", "Sunday")),
}
```

---

### 9. Combining multiple conditions (AND logic)
```python
"staircase-evening": {
    "description": "Evening shows at The Staircase (7pm or later)",
    "filter_func": lambda inst, info: (
        "The Staircase" in inst.venue and
        inst.local_key is not None and
        inst.local_key[2] >= 19
    ),
}
```
**Logic**: Use `and` to require ALL conditions to be true.
- Return `True` only if BOTH:
  1. The venue contains "The Staircase"
  2. The hour is >= 19 (7pm)

---

### 10. Combining with OR logic
```python
"staircase-or-gasworks": {
    "description": "Performances at The Staircase or The Gasworks",
    "filter_func": lambda inst, info: any(
        venue in inst.venue
        for venue in ["The Staircase", "The Gasworks"]
    ),
}
```
**Logic**: Return `True` if the venue contains ANY of the listed venues.

---

## How to Add Your Filter

### Step 1: Open `scraper.py`

Find this section (around line 233):

```python
FILTER_DEFINITIONS = {
    "all": {
        "description": "All performances including cancelled",
        "filter_func": lambda inst, info: True,
    },
    "no-cancelled": {
        ...
    },
    # ... existing filters ...
}
```

### Step 2: Add your new entry

Insert a comma after the last filter, then add your new one:

```python
FILTER_DEFINITIONS = {
    "all": { ... },
    "no-cancelled": { ... },
    "plays-only": { ... },
    "outdoor-only": { ... },
    
    # YOUR NEW FILTER HERE:
    "my-new-filter": {
        "description": "Your description here",
        "filter_func": lambda inst, info: YOUR_CONDITION,
    },
}
```

**Important**: 
- End each filter with a comma (except the last one).
- Use unique names (no duplicates).
- Single quotes `'` and double quotes `"` are interchangeable in Python.

### Step 3: Test locally

```bash
python scraper.py --debug
```

This will:
1. Fetch the live site (if you have internet).
2. Generate `fringe-all.ics`, `fringe-no-cancelled.ics`, etc.
3. Create debug CSVs so you can verify the filters worked.

Check `docs/fringe-my-new-filter.ics` and verify it has roughly the right number of events. Open it in a text editor and spot-check a few event titles.

### Step 4: Commit and push

```bash
git add scraper.py
git commit -m "Add 'my-new-filter' calendar filter"
git push
```

The workflow will automatically run on the next scheduled time (usually daily at 12:00 UTC), and a new `.ics` file will appear in `docs/`.

### Step 5: Subscribe and share

Your new calendar URL is:
```
https://<your-username>.github.io/<repo-name>/fringe-my-new-filter.ics
```

Share it with anyone who wants this filtered view.

---

## Debugging a Filter

If your filter doesn't work as expected:

### 1. Check the log output
Run locally and look at the output. If your filter has a syntax error, Python will tell you immediately:

```bash
$ python scraper.py --debug
...
SyntaxError: ...
```

### 2. Check the generated .ics file
```bash
# Count events in your new calendar
grep "BEGIN:VEVENT" docs/fringe-my-new-filter.ics | wc -l

# Compare to the full calendar
grep "BEGIN:VEVENT" docs/fringe-all.ics | wc -l
```

If your filter is too strict, you'll see far fewer events.

### 3. Use the debug CSVs
Run with `--debug` and open `debug_instances.csv` in a spreadsheet. Filter or sort by venue/cancelled/date to verify your filter logic is correct.

### 4. Test your condition in Python
Open a Python REPL and test your condition:

```python
# Test: does "The Staircase" appear in "The Staircase | Studio Theatre"?
venue = "The Staircase | Studio Theatre"
print("The Staircase" in venue)  # Should print: True

# Test: is "free" in "Free"?
price = "Free"
print("free" in price.lower())  # Should print: True
```

---

## Common Mistakes

### ❌ Forgetting the comma
```python
"my-filter": {
    "description": "...",
    "filter_func": lambda inst, info: True
}  # ← Missing comma here!
"next-filter": { ... }  # ← Syntax error
```
**Fix**: Add a comma after the closing `}`.

### ❌ Forgetting `get()` for safe dictionary access
```python
# WRONG:
"filter_func": lambda inst, info: "AP" in info.flags_by_key[inst.local_key]

# RIGHT:
"filter_func": lambda inst, info: "AP" in info.flags_by_key.get(inst.local_key, set())
```
Without `.get()`, you'll crash if `inst.local_key` isn't in the dictionary.

### ❌ Comparing strings incorrectly
```python
# WRONG: case-sensitive, won't catch "COMEDY" or "Comedy"
"filter_func": lambda inst, info: info.genre == "comedy"

# RIGHT: case-insensitive
"filter_func": lambda inst, info: "comedy" in info.genre.lower()
```

### ❌ Forgetting to check if a field exists
```python
# WRONG: crashes if info.genre is empty
"filter_func": lambda inst, info: "comedy" in info.genre

# RIGHT: safe
"filter_func": lambda inst, info: info.genre and "comedy" in info.genre.lower()
```

---

## Reference: All Built-in Filters

The scraper comes with these filters pre-defined. Use them as examples:

| Filter Name | Description |
|-------------|-------------|
| `all` | All performances, including cancelled |
| `no-cancelled` | All performances except cancelled |
| `plays-only` | Indoor theatre only (excludes Fringe On The Streets, Fringe Boulevard) |
| `outdoor-only` | Outdoor events only (Fringe On The Streets, Fringe Boulevard) |

---

## Advanced: Conditional Logic

### Multiple conditions with AND
Return `True` only if ALL are true:

```python
"filter_func": lambda inst, info: (
    "The Staircase" in inst.venue and
    not inst.cancelled and
    inst.local_key is not None and
    inst.local_key[2] >= 19
)
```

### Multiple conditions with OR
Return `True` if ANY are true:

```python
"filter_func": lambda inst, info: (
    "The Staircase" in inst.venue or
    "The Gasworks" in inst.venue
)
```

### Inverting logic with NOT
```python
# Only shows that are NOT cancelled
lambda inst, info: not inst.cancelled

# Only shows NOT at Fringe On The Streets
lambda inst, info: "Fringe On The Streets" not in inst.venue
```

---

## Next Steps

1. **Think of a filter you want**: "I want only comedy shows" or "I want only evening performances at The Staircase".
2. **Pick a filter name and description**.
3. **Write the condition** using the examples and reference above.
4. **Test locally** with `python scraper.py --debug`.
5. **Verify** the output by checking the .ics file or debug CSVs.
6. **Commit and share** the new calendar URL.

Good luck! 🎭
