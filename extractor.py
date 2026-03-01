from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import dateparser
import dateparser.search
from bs4 import BeautifulSoup
from dateutil.tz import gettz

LINK_RE = re.compile(r"(https?://[^\s>\"]+)")
LOCATION_HINTS = ("venue", "location", "room", "auditorium", "hall", "lab", "classroom")


@dataclass
class Extracted:
    summary: str
    start: datetime
    end: datetime
    location: Optional[str]
    link: Optional[str]
    confidence: float


def html_to_text(s: str) -> str:
    return BeautifulSoup(s, "html.parser").get_text(" ", strip=True)


def pick_link(text: str) -> Optional[str]:
    m = LINK_RE.search(text)
    return m.group(1) if m else None


def pick_location(text: str) -> Optional[str]:
    for ln in [x.strip() for x in text.splitlines() if x.strip()]:
        low = ln.lower()
        if any(h in low for h in LOCATION_HINTS):
            return ln.split(":", 1)[1].strip() if ":" in ln else ln
    return None


def _find_dates(text: str, tz_name: str) -> list[datetime]:
    """Use dateparser to find all datetime mentions in text."""
    settings = {
        "TIMEZONE": tz_name,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
        "PREFER_DAY_OF_MONTH": "first",
    }
    results = dateparser.search.search_dates(text, settings=settings) or []
    # results is a list of (matched_string, datetime) tuples
    return [dt for _, dt in results]


def _best_future_date(dates: list[datetime], now: datetime) -> Optional[datetime]:
    """Pick the most likely event date: prefer future, closest to now."""
    future = [d for d in dates if d > now - timedelta(days=2)]
    if future:
        return min(future, key=lambda d: d)
    # all in past — return closest
    return min(dates, key=lambda d: abs((d - now).total_seconds())) if dates else None


def extract_event(subject: str, body_raw: str, default_tz: str) -> Optional[Extracted]:
    body = html_to_text(body_raw) if "<" in body_raw else body_raw
    text = f"{subject}\n{body}".strip()

    tz = gettz(default_tz)
    now = datetime.now(tz)

    dates = _find_dates(text, default_tz)
    if not dates:
        return None

    start = _best_future_date(dates, now)
    if start is None:
        return None

    # If dateparser found a time component (non-midnight), use it; else default to 09:00
    if start.hour == 0 and start.minute == 0:
        start = start.replace(hour=9, minute=0)

    # Look for a second distinct datetime that could be the end time
    end = None
    for d in dates:
        if d != start and abs((d - start).total_seconds()) < 8 * 3600 and d > start:
            end = d
            break
    if end is None:
        end = start + timedelta(hours=1)

    # Confidence scoring
    is_future = start > now - timedelta(days=2)
    conf = 0.80 if is_future else 0.40

    low = text.lower()
    if "workshop" in low:
        conf = max(conf, 0.85)
    elif any(w in low for w in ("competition", "hackathon", "challenge")):
        conf = max(conf, 0.82)
    elif any(w in low for w in ("webinar", "seminar", "talk")):
        conf = max(conf, 0.80)

    # Boost if explicit time mention found alongside date
    if any(d.hour != 0 or d.minute != 0 for d in dates):
        conf = min(conf + 0.10, 0.98)

    return Extracted(
        summary=subject.strip()[:140] or "College event",
        start=start,
        end=end,
        location=pick_location(text),
        link=pick_link(text),
        confidence=conf,
    )
