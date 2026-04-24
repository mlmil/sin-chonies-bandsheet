# 🎸 Simple Band Sheet Generator (iCal Version)

This guide shows you how to sync a Google Calendar to a JSON band sheet using a **Secret iCal URL**. This is the easiest method and does **not** require setting up a Google Cloud project or OAuth tokens.

---

## Phase 1: Get the "Secret Address" from Google
The band needs to find the special link that allows the script to read their calendar.

1.  Open **Google Calendar** on a computer.
2.  On the left, find the band's calendar under "My calendars."
3.  Click the **three dots (⋮)** next to the calendar and choose **Settings and sharing**.
4.  Scroll all the way to the bottom to the **Integrate calendar** section.
5.  Find the box labeled **Secret address in iCal format**.
6.  **Copy this URL**. (It should look like `https://calendar.google.com/calendar/ical/.../basic.ics`)

---

## Phase 2: Local Script Setup

1.  **Install the necessary library**:
    ```bash
    pip install icalevents
    ```

2.  **Create `generate_bandsheet.py`**:
    Paste the code below. **Important**: Change the `ICAL_URL` at the top to the one you copied in Phase 1.

```python
#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta, date
from icalevents.icalevents import events

# --- CONFIGURATION ---
# Use an environment variable for the URL (best for GitHub)
# or just paste it here for testing:
ICAL_URL = os.environ.get("BAND_ICAL_URL", "PASTE_YOUR_LINK_HERE")
TIMEZONE = "America/Los_Angeles"
# ---------------------

def format_time(dt):
    """Convert datetime to band sheet format: @8PM or @9:30PM."""
    if not dt or dt.hour == 0 and dt.minute == 0:
        return None
    hour = dt.hour
    minute = dt.minute
    period = "PM" if hour >= 12 else "AM"
    hour12 = hour % 12 or 12
    if minute:
        return f"@{hour12}:{minute:02d}{period}"
    return f"@{hour12}{period}"

def main():
    print("Fetching calendar events via iCal...")
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=180)
    
    # Fetch events
    all_events = events(url=ICAL_URL, start=start_date, end=end_date)
    
    gigs = []
    member_outs = {}
    member_keywords = {"out", "unavailable", "absent", "blocked", "vacation", "off", "birthday"}

    for e in all_events:
        title = e.summary.lower()
        is_member_out = any(k in title for k in member_keywords)
        
        if is_member_out:
            member_name = e.summary.split()[0].capitalize()
            if member_name not in member_outs:
                member_outs[member_name] = []
            member_outs[member_name].append((e.start.date(), e.end.date()))
        else:
            gigs.append({
                "date": e.start.date(),
                "time_str": format_time(e.start),
                "venue": e.location or "TBD",
                "title": e.summary
            })

    # Sort gigs by date
    gigs.sort(key=lambda x: x["date"])

    bandsheet = {
        "updated": datetime.now().strftime("%B %d, %Y @ %I:%M %p"),
        "booked_gigs": [
            f"{g['date'].strftime('%a %m-%d-%Y').upper()} {g['time_str'] or ''} — {g['venue']}"
            for g in gigs
        ],
        "members_out": [
            f"- {m}: {start.strftime('%a %m-%d-%Y').upper()}" + 
            (f" to {end.strftime('%a %m-%d-%Y').upper()}" if (end-start).days > 1 else "")
            for m, dates in member_outs.items()
            for start, end in dates
        ]
    }

    with open("bandsheet-data.json", "w") as f:
        json.dump(bandsheet, f, indent=2)
    
    print(f"Success! {len(gigs)} gigs and {len(member_outs)} member outs saved.")

if __name__ == "__main__":
    main()
```

---

## Phase 3: GitHub Automation

1.  **Add the URL to GitHub Secrets**:
    *   In your GitHub Repo, go to **Settings > Secrets and variables > Actions**.
    *   Create a **New repository secret** named `BAND_ICAL_URL`.
    *   Paste the **Secret iCal Address** you copied from Google.
2.  **Add the Workflow**:
    Create a file `.github/workflows/update.yml` in your repo:

```yaml
name: Update Band Sheet
on:
  schedule:
    - cron: '0 10 * * *' # Every morning
  workflow_dispatch:      # Manual button
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: { python-version: '3.10' }
      - name: Install dependencies
        run: pip install icalevents
      - name: Run Script
        env:
          BAND_ICAL_URL: ${{ secrets.BAND_ICAL_URL }}
        run: python generate_bandsheet.py
      - name: Commit changes
        run: |
          git config --global user.name 'BandBot'
          git config --global user.email 'bot@band.com'
          git add bandsheet-data.json
          git commit -m "Automated Sync" || exit 0
          git push
```

---

## Summary for the Band
1.  Paste your **Secret iCal URL** into the GitHub Secret `BAND_ICAL_URL`.
2.  The script will now run every morning and update `bandsheet-data.json`.
3.  No Google Cloud keys or logins are ever required!
