# gmail-event-extractor

Scans Gmail for college event emails (workshops, competitions, hackathons, seminars, etc.) and automatically creates Google Calendar events from them.

## How it works
1. Searches Gmail using a keyword query (last 14 days, unlabelled)
2. Extracts event date/time/location from the email body using natural language parsing
3. Creates a Google Calendar event if extraction confidence is high enough
4. Labels processed emails so they aren't re-evaluated next run

## Setup

### 1. Google Cloud credentials
1. Create a Google Cloud project
2. Enable the **Gmail API** and **Google Calendar API**
3. Create OAuth credentials (Desktop app)
4. Download `credentials.json` into the repo root (do **not** commit it)

### 2. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate   # mac/linux
# .venv\Scripts\activate    # windows

pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env to set your timezone, calendar ID, etc.
```

## Run

Normal run (creates calendar events):
```bash
python main.py
```

Dry run (prints what would be created, no events created):
```bash
python main.py --dry-run
```

On first run, a browser window will open for Google OAuth. After that, `token.json` is reused automatically.

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_TZ` | `Asia/Dubai` | Your local timezone |
| `CALENDAR_ID` | `primary` | Google Calendar to add events to |
| `MAX_RESULTS` | `15` | Max emails to fetch per run |
| `MIN_CONFIDENCE` | `0.70` | Minimum confidence to create an event |
