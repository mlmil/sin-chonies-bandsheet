# Sin Chonies Band Sheet

A Python-based band scheduling system that fetches gig data from Google Calendar and generates a static HTML bandsheet. Displays upcoming performances, member availability, and free weekends at a glance.

## How It Works

The bandsheet pulls event data from a public Google Calendar iCal feed, parses event details (date, time, venue, location), and outputs a JSON file that the HTML dashboard consumes. The system is designed to catch incomplete calendar entries and display them as "TBA" to alert for missing or invalid data.

### Data Integrity

**Critical rule:** The system never infers, assumes, or generates missing calendar data. If a gig is missing time, venue, or city information, it displays as "TBA" to flag that the calendar entry needs correction.

## Files

- `generate_bandsheet.py` — Main script. Fetches calendar events and generates `bandsheet-data.json`
- `bandsheet-data.json` — Generated output file containing formatted gig list, member availability, and free weekends
- `index.html` — Static HTML dashboard that displays the bandsheet
- `requirements.txt` — Python dependencies
- `run_sinchonies.sh` — Helper script to run the generator

## Requirements

- Python 3.9+
- `icalevents` library (see requirements.txt)

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

The script uses a public Google Calendar iCal URL (set in `generate_bandsheet.py`):

```python
DEFAULT_ICAL_URL = "https://calendar.google.com/calendar/ical/[CALENDAR_ID]/public/basic.ics"
```

Override via environment variable:
```bash
BAND_ICAL_URL="https://your-calendar-url" python3 generate_bandsheet.py
```

## Output Format

The bandsheet displays gigs in format: `DAY DATE TIME — VENUE, CITY`

Example:
```
FRI 4-24-26 @9PM — The Shores, Oxnard
SAT 5-2-26 @10PM — The Sewer, Ventura
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
