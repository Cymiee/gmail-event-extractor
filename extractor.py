# extractor.py

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from dateutil.tz import gettz

LINK_RE = re.compile(r"(https?://[^\s>]+)")
DATE_LINE_RE = re.compile(r"date\s*:\s*(.+)", re.IGNORECASE)
TIME_LINE_RE = re.compile(
    r"time\s*:\s*([0-9]{1,2}(?::[0-9]{2})?\s*[ap]m)\s*[-–to]+\s*([0-9]{1,2}(?::[0-9]{2})?\s*[ap]m)",
    re.IGNORECASE,
)

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


def _parse_month_day(date_str: str, tz_name: str) -> Optional[datetime]:
    """
    Parses strings like 'February 19, Thursday' or 'Feb 19'.
    If year is missing, uses current year, and if the date would be far in the past,
    bumps to next year.
    """
    tz = gettz(tz_name)
    now = datetime.now(tz)

    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(\d{1,2})\b",
        date_str,
        re.IGNORECASE,
    )
    if not m:
        return None

    month_map = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    month_key = m.group(1).lower()
    month = month_map["sept" if month_key.startswith("sept") else month_key[:3]]
    day = int(m.group(2))

    year_match = re.search(r"\b(20\d{2})\b", date_str)
    year = int(year_match.group(1)) if year_match else now.year

    dt = datetime(year, month, day, 9, 0, tzinfo=tz)  # default 09:00

    # If year was missing and date is clearly in the past, assume next year
    if not year_match and dt < now - timedelta(days=2):
        dt = datetime(year + 1, month, day, 9, 0, tzinfo=tz)

    return dt


def _parse_time_one(s: str) -> tuple[int, int, str]:
    s = s.strip().lower()
    ampm = "am" if "am" in s else "pm"
    s = s.replace("am", "").replace("pm", "").strip()
    if ":" in s:
        h_str, m_str = s.split(":", 1)
    else:
        h_str, m_str = s, "0"
    h, m = int(h_str), int(m_str)

    if ampm == "am":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12

    return h, m, ampm


def _parse_time_range(start_s: str, end_s: str) -> tuple[int, int, int, int]:
    sh, sm, sampm = _parse_time_one(start_s)
    eh, em, eampm = _parse_time_one(end_s)

    # Heuristic: posters often write "9am-12am" but mean 12pm (noon)
    # If start is morning and end is "12am", interpret end as 12pm.
    if sh < 12 and eh == 0 and eampm == "am":
        eh = 12

    return sh, sm, eh, em


def extract_event(subject: str, body_raw: str, default_tz: str) -> Optional[Extracted]:
    body = html_to_text(body_raw) if "<" in body_raw else body_raw
    text = f"{subject}\n{body}".strip()

    tz = gettz(default_tz)
    now = datetime.now(tz)

    # 1) Structured parse first: Date: ... + Time: ...
    date_m = DATE_LINE_RE.search(text)
    if date_m:
        base = _parse_month_day(date_m.group(1), default_tz)
        if base:
            time_m = TIME_LINE_RE.search(text)
            if time_m:
                sh, sm, eh, em = _parse_time_range(time_m.group(1), time_m.group(2))
                start = base.replace(hour=sh, minute=sm)
                end = base.replace(hour=eh, minute=em)
                if end <= start:
                    end = end + timedelta(days=1)
            else:
                start = base
                end = base + timedelta(hours=1)

            # Don’t create events in the past (common if you run script late)
            if start < now - timedelta(days=2):
                conf = 0.40
            else:
                conf = 0.95

            low = text.lower()
            if "workshop" in low:
                conf = max(conf, 0.85)
            elif "competition" in low or "hackathon" in low or "challenge" in low:
                conf = max(conf, 0.80)

            return Extracted(
                summary=(subject.strip()[:140] or "College event"),
                start=start,
                end=end,
                location=pick_location(text),
                link=pick_link(text),
                confidence=conf,
            )

    # 2) Fallback: if no “Date:” line exists, skip (safer than “default=now”)
    return None
