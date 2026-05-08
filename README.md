# Sin Chonies Band Sheet

![Sin Chonies Digital Banner](2025%20Digital%20Banner%20w_qr%20and%20logo%2016x9.png)

A fully automated band scheduling system that fetches gig data from Google Calendar and generates a static HTML bandsheet. Displays upcoming performances, member availability, and free weekends at a glance.

**Live site:** https://mlmil.github.io/sin-chonies-bandsheet/

## How It Works

The bandsheet pulls event data from the Sin Chonies Google Calendar via a **secret iCal feed**, parses event details (date, time, venue, location), and outputs a JSON file that the HTML dashboard consumes. The system is designed to catch incomplete calendar entries and display them as "TBA" to alert for missing or invalid data.

### Data Integrity

**Critical rule:** The system never infers, assumes, or generates missing calendar data. If a gig is missing time, venue, or city information, it displays as "TBA" to flag that the calendar entry needs correction.

## Automation Stack

| Component | What It Does | Schedule |
|-----------|-------------|----------|
| **GitHub Actions** (`update.yml`) | Fetches calendar via secret iCal URL, generates `bandsheet-data.json`, commits & pushes | Daily 7 AM PT + on demand |
| **daily_check.py** | 5-point validator: URL sync, bandsheet health, email scan, Drive folder audit, cross-band conflict check. Emails report to band. | Daily 8:05 AM PT (cron) |
| **GigProcessor.gs** | Google Apps Script — when a new gig is added to the calendar, auto-creates a Drive folder with Notes doc + Google Maps link | On calendar event update |
| **index.html** | Static dashboard consuming `bandsheet-data.json` — "This Week", "Booked Gigs", "Members Out", "Free Weekends" | Served via GitHub Pages |

## Cross-Band Conflict Detection

The `daily_check.py` validator checks both the Sin Chonies and Neon Blonde calendars for same-day gigs affecting shared members (**Mike, Alfred, Dave**). If both bands are booked on the same date, a **CRITICAL** alert is included in the daily email report.

Reports are sent to: `sin.chonies.inc@gmail.com` and `neonblondevc@gmail.com`

## Files

- `generate_bandsheet.py` — Main script. Fetches calendar events via iCal and generates `bandsheet-data.json`
- `bandsheet-data.json` — Generated output file containing formatted gig list, member availability, and free weekends
- `index.html` — Static HTML dashboard that displays the bandsheet
- `daily_check.py` — Validator and email reporter (5 checks: sync, health, email scan, folder audit, cross-band)
- `GigProcessor.gs` — Google Apps Script for Drive folder auto-creation (deploy to script.google.com)
- `requirements.txt` — Python dependencies
- `run_sinchonies.sh` — Helper script to run the generator
- `.github/workflows/update.yml` — GitHub Actions automation

## Requirements

- Python 3.9+
- `icalevents` library (see requirements.txt)
- `icalendar` library (for daily_check.py)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the generator:
   ```bash
   python3 generate_bandsheet.py
   ```

3. Open `index.html` in a browser or serve locally:
   ```bash
   python3 -m http.server 8888
   ```
   Then visit `http://localhost:8888`

## Configuration

The script uses the Sin Chonies Google Calendar via iCal URL (set in `generate_bandsheet.py`). In production, the GitHub Actions workflow uses the **secret iCal URL** stored in the `BAND_ICAL_URL` repository secret — this keeps the private calendar URL out of the source code.

Override via environment variable:
```bash
BAND_ICAL_URL="https://your-calendar-url" python3 generate_bandsheet.py
```

## Output Format

The bandsheet displays gigs in format: `DAY DATE TIME — VENUE, CITY`

Example:
```
FRI 5-8-26 @6PM — Bombay, Ventura
SAT 5-23-26 @8:30PM — Garage, Ventura
```

If any required data is missing, the entire entry shows as TBA:
```
FRI 5-15-26 — TBA
```

## Calendar Entry Guidelines

For clean bandsheet output:

- **Event title:** Venue name (e.g., "The Shores")
- **Event time:** Actual start time (not all-day)
- **Event location:** Format as "Venue - City" or "City, State, Country"
  - Good: `The Sewer - Ventura` or `Oxnard, CA, USA`
  - Avoid: City-only entries without venue in title

Member availability entries (out, vacation, etc.) use keywords like "out", "unavailable", "vacation", "off" in the event title and are tracked separately.

## Timezone

Default timezone is America/Los_Angeles. Modify in `generate_bandsheet.py` if needed:
```python
TIMEZONE = "America/Los_Angeles"
```

## Infrastructure

- **Google Cloud Project:** `cinchones-gmail-drive`
- **OAuth:** Desktop app client (for daily_check.py Gmail/Drive API access)
- **Google Apps Script:** GigProcessor.gs (calendar event trigger → Drive folder creation)
- **Hosting:** GitHub Pages (`mlmil.github.io/sin-chonies-bandsheet/`)
