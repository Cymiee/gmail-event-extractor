# gmail-event-extractor

# Gmail Triage MVP (v0)

Small Python script that:
- searches Gmail for useful college emails (workshops/competitions/exams/etc.)
- prints subject/from/date/snippet
- labels processed emails so they don't get re-processed

## Setup
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download `credentials.json` into the repo root (do not commit it)

## Run
```bash
python -m venv .venv
source .venv/bin/activate   # mac/linux
# .venv\Scripts\activate    # windows

pip install -r requirements.txt
python main.py