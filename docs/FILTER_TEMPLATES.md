# Filter Templates — Copy & Paste Ready

This document provides 15 ready-to-use filters you can copy directly into your `FILTER_DEFINITIONS` dictionary in `scraper.py`. No explanation needed — just copy, paste, and customize the filter name if you want.

---

## Basic Filters

### 1. No Cancelled Shows
```python
"no-cancelled": {
    "description": "All performances except cancelled",
        "cal_name": "Hamilton Fringe 2026 — No Cancellations",
    "filter_func": lambda inst, info: not inst.cancelled,
},
```

### 2. Free Shows Only
```python
"free-only": {
    "description": "Only free performances",
        "cal_name": "Hamilton Fringe 2026 — Free Shows",
    "filter_func": lambda inst, info: info.price and "free" in info.price.lower(),
},
```

### 3. Paid Shows Only
```python
"paid-only": {
    "description": "Only paid performances",
        "cal_name": "Hamilton Fringe 2026 — Paid Shows",
    "filter_func": lambda inst, info: info.price and "free" not in info.price.lower(),
},
```

---

## Venue Filters

### 4. Single Venue: The Staircase
```python
"staircase": {
    "description": "Only The Staircase",
        "cal_name": "Hamilton Fringe 2026 — Staircase",
    "filter_func": lambda inst, info: "The Staircase" in inst.venue,
},
```

### 5. Single Venue: Theatre Aquarius
```python
"aquarius": {
    "description": "Only Theatre Aquarius",
        "cal_name": "Hamilton Fringe 2026 — Theatre Aquarius",
    "filter_func": lambda inst, info: "Theatre Aquarius" in inst.venue,
},
```

### 6. Single Venue: The Westdale
```python
"westdale": {
    "description": "Only The Westdale",
        "cal_name": "Hamilton Fringe 2026 — The Westdale",
    "filter_func": lambda inst, info: "The Westdale" in inst.venue,
},
```

### 7. Indoor Venues Only (Exclude Outdoor)
```python
"indoor-only": {
    "description": "Indoor venues only (excludes Fringe On The Streets, Fringe Boulevard)",
        "cal_name": "Hamilton Fringe 2026 — Indoor Shows",
    "filter_func": lambda inst, info: not any(
        venue_keyword in inst.venue
        for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
    ),
},
```

### 8. Outdoor Events Only
```python
"outdoor-only": {
    "description": "Outdoor events only (Fringe On The Streets, Fringe Boulevard)",
        "cal_name": "Hamilton Fringe 2026 — Outdoor Events",
    "filter_func": lambda inst, info: any(
        venue_keyword in inst.venue
        for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
    ),
},
```

### 9. Multiple Venues (Example: Staircase or Gasworks)
```python
"staircase-or-gasworks": {
    "description": "Only The Staircase or The Gasworks",
        "cal_name": "Hamilton Fringe 2026 — Staircase & Gasworks",
    "filter_func": lambda inst, info: any(
        venue in inst.venue
        for venue in ["The Staircase", "The Gasworks"]
    ),
},
```

---

## Time-Based Filters

### 10. Evening Shows Only (7pm+)
```python
"evening": {
    "description": "Only shows at 7pm or later",
        "cal_name": "Hamilton Fringe 2026 — Evening Shows",
    "filter_func": lambda inst, info: (
        inst.local_key is not None and
        inst.local_key[2] >= 19
    ),
},
```

### 11. Afternoon Shows Only (12pm–6pm)
```python
"afternoon": {
    "description": "Afternoon shows only (12pm–6pm)",
        "cal_name": "Hamilton Fringe 2026 — Afternoon Shows",
    "filter_func": lambda inst, info: (
        inst.local_key is not None and
        12 <= inst.local_key[2] < 18
    ),
},
```

### 12. Morning/Early Shows Only (Before 12pm)
```python
"morning": {
    "description": "Morning shows only (before 12pm)",
        "cal_name": "Hamilton Fringe 2026 — Morning Shows",
    "filter_func": lambda inst, info: (
        inst.local_key is not None and
        inst.local_key[2] < 12
    ),
},
```

### 13. Weekend Shows Only (Saturday & Sunday)
```python
"weekend": {
    "description": "Weekend performances only",
        "cal_name": "Hamilton Fringe 2026 — Weekend Shows",
    "filter_func": lambda inst, info: inst.date_text.startswith(("Saturday", "Sunday")),
},
```

---

## Genre & Content Filters

### 14. Shows With Content Warnings
```python
"has-warnings": {
    "description": "Only shows with content warnings",
        "cal_name": "Hamilton Fringe 2026 — Has Content Warnings",
    "filter_func": lambda inst, info: bool(info.warnings),
},
```

### 15. Shows WITHOUT Content Warnings (Family-Friendly)
```python
"family-friendly": {
    "description": "Only shows with no content warnings",
        "cal_name": "Hamilton Fringe 2026 — Family Friendly",
    "filter_func": lambda inst, info: not info.warnings,
},
```

---

## Special Performance Flags

### 16. Affinity Performances Only
```python
"affinity": {
    "description": "Only Affinity Performances (AP)",
        "cal_name": "Hamilton Fringe 2026 — Affinity Performances",
    "filter_func": lambda inst, info: "AP" in info.flags_by_key.get(inst.local_key, set()),
},
```

### 17. Relaxed Performances Only
```python
"relaxed": {
    "description": "Only Relaxed Performances (RP)",
        "cal_name": "Hamilton Fringe 2026 — Relaxed Performances",
    "filter_func": lambda inst, info: "RP" in info.flags_by_key.get(inst.local_key, set()),
},
```

### 18. Mask-Mandatory Performances Only
```python
"mask-mandatory": {
    "description": "Only Mask-Mandatory Performances (MM)",
        "cal_name": "Hamilton Fringe 2026 — Mask-Mandatory Performances",
    "filter_func": lambda inst, info: "MM" in info.flags_by_key.get(inst.local_key, set()),
},
```

### 19. Any Special Performance Flag
```python
"special-access": {
    "description": "Only performances with special flags (RP, MM, or AP)",
        "cal_name": "Hamilton Fringe 2026 — Special Access Performances",
    "filter_func": lambda inst, info: bool(info.flags_by_key.get(inst.local_key, set())),
},
```

---

## Combination Filters (Multiple Conditions)

### 20. Evening Performances at The Staircase
```python
"staircase-evening": {
    "description": "Evening shows at The Staircase (7pm+)",
        "cal_name": "Hamilton Fringe 2026 — Staircase Evenings",
    "filter_func": lambda inst, info: (
        "The Staircase" in inst.venue and
        inst.local_key is not None and
        inst.local_key[2] >= 19
    ),
},
```

### 21. Free Outdoor Events
```python
"free-outdoor": {
    "description": "Free outdoor events only",
        "cal_name": "Hamilton Fringe 2026 — Free Outdoor Events",
    "filter_func": lambda inst, info: (
        any(
            venue_keyword in inst.venue
            for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
        ) and
        info.price and
        "free" in info.price.lower()
    ),
},
```

### 22. Indoor, Paid, Evening Shows
```python
"paid-indoor-evening": {
    "description": "Paid indoor shows at 7pm or later",
        "cal_name": "Hamilton Fringe 2026 — Paid Indoor Evenings",
    "filter_func": lambda inst, info: (
        not any(
            venue_keyword in inst.venue
            for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
        ) and
        info.price and
        "free" not in info.price.lower() and
        inst.local_key is not None and
        inst.local_key[2] >= 19
    ),
},
```

### 23. Family-Friendly Indoor Theater
```python
"family-theater": {
    "description": "No warnings + indoor only",
        "cal_name": "Hamilton Fringe 2026 — Family Theatre",
    "filter_func": lambda inst, info: (
        not info.warnings and
        not any(
            venue_keyword in inst.venue
            for venue_keyword in ["Fringe On The Streets", "Fringe Boulevard"]
        )
    ),
},
```

### 24. Accessible Performances (Special Flags) at The Staircase
```python
"staircase-accessible": {
    "description": "Accessible performances (RP/MM/AP) at The Staircase",
        "cal_name": "Hamilton Fringe 2026 — Staircase Accessible",
    "filter_func": lambda inst, info: (
        "The Staircase" in inst.venue and
        bool(info.flags_by_key.get(inst.local_key, set()))
    ),
},
```

---

## How to Use These Templates

1. Pick one (or more) from the list above.
2. Copy the entire dictionary entry (the lines from `"filter-name":` through the closing `},`).
3. Open `scraper.py` and find the `FILTER_DEFINITIONS` section.
4. Paste it into the dictionary, making sure to add a comma after it (unless it's the last filter).
5. If you want to rename the filter, change the part in quotes at the start (e.g., `"staircase"` → `"my-staircase"`).
6. Test: `python scraper.py --debug`
7. Commit and push.

---

## Customization Tips

### Change a venue name
Replace `"The Staircase"` with any other venue. To find exact venue names, run `python scraper.py --debug` once and check `debug_instances.csv`.

### Change a price threshold
Replace `"free"` with any keyword in the price field (e.g., `"$20"`).

### Change a time threshold
Replace `19` (7pm) with any hour in 24-hour format:
- `9` = 9am
- `12` = noon
- `15` = 3pm
- `18` = 6pm
- `20` = 8pm
- `22` = 10pm

### Add a third venue to a filter
In a filter with `for venue in ["The Staircase", "The Gasworks"]`, add a comma and the new venue:
```python
for venue in ["The Staircase", "The Gasworks", "The Westdale"]
```

### Combine two filters with OR logic
Use `or` to match either condition:
```python
"filter_func": lambda inst, info: (
    "The Staircase" in inst.venue or
    "Theatre Aquarius" in inst.venue
),
```

### Combine two filters with AND logic
Use `and` to require both conditions:
```python
"filter_func": lambda inst, info: (
    "The Staircase" in inst.venue and
    inst.local_key is not None and
    inst.local_key[2] >= 19
),
```

---

## Testing Your Filter

After you add a new filter:

```bash
# Run the scraper
python scraper.py --debug

# Count events in your new filter
grep "BEGIN:VEVENT" docs/fringe-YOUR-FILTER-NAME.ics | wc -l

# Compare to the full calendar
grep "BEGIN:VEVENT" docs/fringe-all.ics | wc -l
```

If the numbers look reasonable (your filter should have fewer events than "all"), you're good!

---

## Still Stuck?

See `FILTERS_GUIDE.md` for detailed explanations, troubleshooting, and how to write filters from scratch.
