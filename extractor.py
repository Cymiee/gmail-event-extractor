# extractor.py

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil import parser as dtparser
from dateutil.tz import gettz
from bs4 import BeautifulSoup


LINK_RE = re.compile(r"(https?://[^\s>]+)")
LOCATION_HINTS = ("venue", "location", "room", "auditorium", "hall", "lab", "classroom")


@dataclass
class Extracted:
    summary: str
    start: datetime
    end: datetime
    location: str | None
    link: str | None
    confidence: float


def html_to_text(s: str) -> str:
    # If it's HTML, BeautifulSoup will clean it.
    return BeautifulSoup(s, "html.parser").get_text(" ", strip=True)


def pick_link(text: str) -> str | None:
    m = LINK_RE.search(text)
    return m.group(1) if m else None


def pick_location(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if any(h in low for h in LOCATION_HINTS):
            # crude split
            if ":" in ln:
                return ln.split(":", 1)[1].strip() or None
            return ln
    return None


def extract_datetime(subject: str, body: str, default_tz: str) -> tuple[datetime | None, float]:
    """
    Returns (datetime, confidence).
    We try best-effort parsing using fuzzy dateutil.
    """
    tzinfo = gettz(default_tz)
    text = f"{subject}\n{body}"

    # Prefer lines likely to contain schedule
    candidates = []
    for ln in text.splitlines():
        low = ln.lower()
        if any(k in low for k in ["date", "time", "when", "schedule", "on ", "at ", "from ", "to ", "timing"]):
            candidates.append(ln.strip())

    # fallback chunk
    candidates.append(text[:1200])

    for c in candidates:
        try:
            dt = dtparser.parse(c, fuzzy=True, default=datetime.now(tzinfo))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tzinfo)

            # confidence heuristic: if candidate had explicit date words
            conf = 0.85 if any(ch.isdigit() for ch in c) else 0.70
            return dt, conf
        except Exception:
            continue

    return None, 0.0


def extract_event(subject: str, body_raw: str, default_tz: str) -> Extracted | None:
    # body might be snippet/plain/html; normalize
    body = html_to_text(body_raw) if "<html" in body_raw.lower() or "<div" in body_raw.lower() else body_raw
    text = f"{subject}\n{body}".strip()

    dt, dt_conf = extract_datetime(subject, body, default_tz)
    if not dt:
        return None

    low = text.lower()

    # duration heuristic
    if "workshop" in low:
        duration = timedelta(hours=1, minutes=30)
        type_conf = 0.80
    elif "hackathon" in low or "competition" in low or "challenge" in low:
        duration = timedelta(hours=2)
        type_conf = 0.75
    elif "webinar" in low or "talk" in low or "seminar" in low or "guest" in low:
        duration = timedelta(hours=1)
        type_conf = 0.70
    else:
        duration = timedelta(hours=1)
        type_conf = 0.60

    link = pick_link(text)
    loc = pick_location(text)

    confidence = min(1.0, (dt_conf * 0.6 + type_conf * 0.4))

    return Extracted(
        summary=subject.strip()[:140] if subject else "College event",
        start=dt,
        end=dt + duration,
        location=loc,
        link=link,
        confidence=confidence,
    )