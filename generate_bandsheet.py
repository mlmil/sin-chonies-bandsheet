#!/usr/bin/env python3
"""
Sin Chonies — Band Sheet Generator
Fetches the Google Calendar via public iCal URL and writes bandsheet-data.json
for the static HTML page to consume.
"""
import json
import os
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Optional

from icalevents.icalevents import events

# --- CONFIGURATION -----------------------------------------------------------
# Public iCal URL for Sin Chonies calendar.
# Can be overridden via BAND_ICAL_URL environment variable.
DEFAULT_ICAL_URL = "https://calendar.google.com/calendar/ical/4fa4b7d105b67016c021fb6f7feddaffde40f5b734d900a90b2737f4027b3dc9%40group.calendar.google.com/public/basic.ics"
PUBLIC_ICAL_URL = os.getenv("BAND_ICAL_URL", DEFAULT_ICAL_URL)
TIMEZONE = "America/Los_Angeles"
LOOK_AHEAD_DAYS = 180
# -----------------------------------------------------------------------------

TZ = ZoneInfo(TIMEZONE)


# ── Helpers ────────────────────────────────────────────────                  

def format_time(dt) -> Optional[str]:
    """Return a compact time string like '@8PM' or '@9:30PM', or None if missing/all-day.

    CRITICAL: None return value indicates missing time data. Returning None will cause
    the gig to display as TBA in the bandsheet, serving as an alert flag that the
    calendar entry is incomplete and needs correction.

    Never infer or assume event times — if it's not explicitly in the calendar,
    return None and let the gig render as TBA.
    """
    if dt is None:
        return None
    # icalevents may return date objects for all-day events
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return None
    if dt.hour == 0 and dt.minute == 0:
        return None
    hour = dt.hour
    minute = dt.minute
    period = "PM" if hour >= 12 else "AM"
    hour12 = hour % 12 or 12
    if minute:
        return f"@{hour12}:{minute:02d}{period}"
    return f"@{hour12}{period}"


def format_date(d: date) -> str:
    """Return date string like 'SAT 5-16-26' (no leading zeros)."""
    day_abbr = d.strftime('%a').upper()
    month = d.month
    day = d.day
    year = d.year % 100  # Last two digits of year
    return f"{day_abbr} {month}-{day}-{year}"


def extract_venue_city(venue_str: str, venue_name: Optional[str] = None) -> str:
    """Extract venue and city from full address. Only return if actual venue exists.

    If venue_name is provided (from event title), use it with city from venue_str.
    E.g. 'The Sewer - Ventura' → 'The Sewer, Ventura'
    Or title='The Shores' + location='Oxnard, CA, USA' → 'The Shores, Oxnard'
    But 'Oxnard, CA, USA' alone (no title) → 'TBA'
    Strips out zip codes and coordinates.

    CRITICAL: Returns 'TBA' if venue or city data is incomplete or missing.
    TBA serves as an alert flag that the calendar entry needs correction.
    Never infer or assume venue/city data — if it's not in the calendar, return TBA.
    """
    if not venue_str or venue_str == "TBD":
        return "TBA"

    # Try hyphen-separated format first (e.g., "The Sewer - Ventura")
    if " - " in venue_str:
        parts = [p.strip() for p in venue_str.split(" - ")]
        if len(parts) == 2:
            venue, city = parts
            # Remove zip codes and state abbreviations from city
            city = " ".join(word for word in city.split() if not word.isdigit() and len(word) > 2)
            return f"{venue}, {city}".strip()

    # Try comma-separated format
    parts = [p.strip() for p in venue_str.split(',')]
    first_part = parts[0] if parts else ""

    # List of city/state names that indicate incomplete calendar entry (no venue)
    city_names = ["Oxnard", "Ventura", "Santa Barbara", "Newbury Park", "Thousand Oaks"]

    # If first part is just a city and we have a venue_name, use venue_name + city
    if first_part in city_names and venue_name:
        return f"{venue_name}, {first_part}".strip()
    
    # If first part is just a city (and no venue_name), return TBA
    if first_part in city_names:
        return "TBA"

    # If we have venue name + city, format it
    if len(parts) >= 2:
        venue = first_part
        city = parts[-2] if len(parts) > 2 else parts[1]
        # Remove zip codes and state abbreviations
        city = " ".join(word for word in city.split() if not word.isdigit() and len(word) > 2)
        return f"{venue}, {city}".strip()

    return first_part if first_part else "TBA"


def event_date(dt) -> date:
    """Normalise an event start to a plain date."""
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def is_weekend(d: date) -> bool:
    return d.weekday() in (4, 5)  # Friday = 4, Saturday = 5


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(TZ)
    today = now.date()
    start_date = now
    end_date = now + timedelta(days=LOOK_AHEAD_DAYS)

    print(f"Fetching Sin Chonies calendar events ({today} → {end_date.date()})…")
    all_events = events(url=PUBLIC_ICAL_URL, start=start_date, end=end_date)
    print(f"  ↳ {len(all_events)} raw events fetched.")

    # ── Classify events ──────────────────────────────────────────────────────
    # CRITICAL DATA INTEGRITY RULE:
    # Never infer, assume, or generate missing calendar data. If any gig has
    # incomplete or missing time, venue, or city data, display 'TBA' to serve
    # as an alert flag. TBA indicates the calendar entry needs correction.
    # This ensures the bandsheet always reflects exactly what's in the calendar,
    # nothing more, nothing less.

    gigs: list[dict] = []
    member_outs: dict[str, list[tuple[date, date]]] = {}
    member_keywords = {
        "out", "unavailable", "absent", "blocked",
        "vacation", "off", "birthday", "gone", "no-go",
    }

    booked_dates: set[date] = set()

    for e in all_events:
        title = (e.summary or "").strip()
        title_lower = title.lower()

        # Detect "member out" entries
        is_out = any(kw in title_lower for kw in member_keywords)

        if is_out:
            member_name = title.split()[0].capitalize()
            start_d = event_date(e.start)
            end_d = event_date(e.end) if e.end else start_d
            member_outs.setdefault(member_name, []).append((start_d, end_d))
        else:
            d = event_date(e.start)
            # Only add gigs that are today or in the future
            if d >= today:
                booked_dates.add(d)
                gigs.append(
                    {
                        "date": d,
                        "time_str": format_time(e.start),
                        "venue": (getattr(e, "location", None) or "TBD").strip(),
                        "title": title,
                    }
                )

    gigs.sort(key=lambda g: g["date"])

    # Debug: preview gigs to verify dates are parsed
    try:
        print("DEBUG gigs preview:", [
            (g['date'].isoformat(), g['title'], g['venue'], g['time_str']) for g in gigs[:5]
        ])
    except Exception as err:
        print(f"DEBUG: Failed to preview gigs: {err}")

    # ── This Week ────────────────────────────────────────────────────────────
    week_start = today
    week_end = today + timedelta(days=(6 - today.weekday()) % 7 or 7)  # through Sunday

    this_week: list[str] = []
    for g in gigs:
        if week_start <= g["date"] <= week_end:
            time_str = g['time_str']
            venue = extract_venue_city(g['venue'], g['title'])

            # CRITICAL: If any field is incomplete/missing, display TBA as alert
            # to flag that the calendar entry needs correction
            if time_str is None or venue == "TBA":
                this_week.append(f"{format_date(g['date'])} — TBA")
            else:
                this_week.append(f"{format_date(g['date'])} {time_str} — {venue}")

    # ── Booked Gigs (formatted) ──────────────────────────────────────────────
    booked_gigs: list[str] = []
    for g in gigs:
        time_str = g['time_str']
        venue = extract_venue_city(g['venue'], g['title'])

        # CRITICAL: If any field is incomplete/missing, display TBA as alert
        # to flag that the calendar entry needs correction
        if time_str is None or venue == "TBA":
            booked_gigs.append(f"{format_date(g['date'])} — TBA")
        else:
            booked_gigs.append(f"{format_date(g['date'])} {time_str} — {venue}")

    # ── Members Out (formatted) ──────────────────────────────────────────────
    members_out_lines: list[str] = []
    for name, ranges in sorted(member_outs.items()):
        for start_d, end_d in sorted(ranges):
            line = f"- {name}: {start_d.strftime('%a %m-%d-%Y').upper()}"
            if (end_d - start_d).days > 1:
                line += f" to {end_d.strftime('%a %m-%d-%Y').upper()}"
            members_out_lines.append(line)

    # ── Free Weekends ────────────────────────────────────────────────────────
    free_weekends: list[str] = []
    d = today
    while d <= (today + timedelta(days=LOOK_AHEAD_DAYS)):
        if is_weekend(d) and d not in booked_dates:
            day_name = "FRI" if d.weekday() == 4 else "SAT"
            free_weekends.append(f"- {day_name} {d.strftime('%B %d')}")
        d += timedelta(days=1)

    # ── Write JSON ───────────────────────────────────────────────────────────
    bandsheet = {
        "updated": now.strftime("%B %d, %Y @ %I:%M %p"),
        "this_week": this_week,
        "booked_gigs": booked_gigs,
        "members_out": members_out_lines,
        "free_weekends": free_weekends,
    }

    out_path = os.path.join(os.path.dirname(__file__) or ".", "bandsheet-data.json")
    with open(out_path, "w") as f:
        json.dump(bandsheet, f, indent=2)

    print(f"✅  bandsheet-data.json written — "
          f"{len(booked_gigs)} gigs, {len(members_out_lines)} member-outs, "
          f"{len(free_weekends)} free weekend days.")


if __name__ == "__main__":
    main()
