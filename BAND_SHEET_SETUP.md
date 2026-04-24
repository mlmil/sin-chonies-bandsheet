# 🎸 Band Sheet Generator & GitHub Automation Guide

This document provides a complete walkthrough for setting up a Google Calendar to JSON sync for any band, including automated daily updates via GitHub Actions.

---

## Phase 1: Google Cloud Setup
You need a "Project" in Google Cloud to allow your script to access Google Calendar.

1.  **Create a Project**: Go to the [Google Cloud Console](https://console.cloud.google.com/). Create a **New Project**.
2.  **Enable the API**:
    *   Search for "Google Calendar API".
    *   Click **Enable**.
3.  **Configure the OAuth Consent Screen**:
    *   Navigate to **APIs & Services > OAuth consent screen**.
    *   Select **External**.
    *   Fill in the App Name (e.g., "Band Sheet Sync").
    *   **Test Users**: Add the Gmail address of the band's calendar.
4.  **Create Credentials**:
    *   Go to **APIs & Services > Credentials**.
    *   Click **Create Credentials > OAuth client ID**.
    *   Select **Desktop App**.
    *   Download the JSON file and rename it to `client_secret.json`.

---

## Phase 2: Local Setup & Token Generation

1.  **Prepare your folder**: Place your `client_secret.json` in a new folder.
2.  **Install dependencies**:
    ```bash
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
    ```
3.  **Create `get_token.py`**:
    Copy this script to generate the long-term access token.

    ```python
    from google_auth_oauthlib.flow import InstalledAppFlow
    import json

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def main():
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        token_dict = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }
        
        print("\n--- COPY THE JSON BELOW FOR GITHUB SECRETS ---")
        print(json.dumps(token_dict))

    if __name__ == '__main__':
        main()
    ```

4.  **Run it**: `python3 get_token.py`. Login via the browser and **copy the JSON output** for later.

---

## Phase 3: Repository Files

### 1. `.gitignore`
Create a file named `.gitignore` to keep your secrets off GitHub.
```text
client_secret.json
token.json
.env
venv/
__pycache__/
bandsheet-data.json
```

### 2. `requirements.txt`
```text
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

### 3. `generate_bandsheet.py`
This is your main script. Update the `CALENDAR_ID` at the top.

```python
#!/usr/bin/env python3
import json
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- CONFIG ---
CALENDAR_ID = "your_band_email@gmail.com"
TOKEN_ENV_VAR = "BAND_TOKEN_JSON" 
TIMEZONE = "America/Los_Angeles"
# --------------

PT_TZ = ZoneInfo(TIMEZONE)
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_calendar_events():
    token_json = os.environ.get(TOKEN_ENV_VAR)
    if not token_json:
        print(f"ERROR: {TOKEN_ENV_VAR} secret not found")
        sys.exit(1)

    creds_data = json.loads(token_json)
    creds = Credentials(
        token=creds_data.get("access_token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data.get("token_uri"),
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        scopes=SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)
    today = datetime.now(PT_TZ).date()
    time_min = datetime.combine(today, datetime.min.time(), tzinfo=PT_TZ).isoformat()
    time_max = datetime.combine(today + timedelta(days=180), datetime.max.time(), tzinfo=PT_TZ).isoformat()

    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy="startTime"
    ).execute()

    return events_result.get("items", [])

def main():
    events = get_calendar_events()
    bandsheet = {
        "updated": datetime.now(PT_TZ).strftime("%B %d, %Y @ %I:%M %p"),
        "events": events
    }
    
    with open("bandsheet-data.json", "w") as f:
        json.dump(bandsheet, f, indent=2)
    print("Success: bandsheet-data.json updated.")

if __name__ == "__main__":
    main()
```

---

## Phase 4: GitHub Automation

1.  **Add Secret**: In your GitHub Repo, go to **Settings > Secrets and variables > Actions**. Add a secret named `BAND_TOKEN_JSON` and paste the JSON you copied from Phase 2.
2.  **Add Workflow**: Create `.github/workflows/update.yml`:

```yaml
name: Update Band Sheet
on:
  schedule:
    - cron: '0 10 * * *'
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: { python-version: '3.10' }
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Script
        env:
          BAND_TOKEN_JSON: ${{ secrets.BAND_TOKEN_JSON }}
        run: python generate_bandsheet.py
      - name: Commit changes
        run: |
          git config --global user.name 'BandBot'
          git config --global user.email 'bot@band.com'
          git add bandsheet-data.json
          git commit -m "Automated Sync" || exit 0
          git push
```
