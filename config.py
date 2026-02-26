SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
]

LABEL_NAME = "AutoCalendar/Reviewed"
DEFAULT_TZ = "Asia/Dubai"  # change if needed
CALENDAR_ID = "primary"

MAX_RESULTS = 15

# No quizzes/exams/LMS:
GMAIL_QUERY = (
    "newer_than:14d "
    f'-label:"{LABEL_NAME}" '
    "("
    "workshop OR competition OR hackathon OR webinar OR seminar OR talk OR guest "
    'OR "register" OR registration OR deadline OR submit OR submissions OR event '
    'OR "limited spots" OR "sign up" OR date OR time OR venue'
    ") "
    '-(quiz OR exam OR midsem OR compre OR LMS OR answerkey OR "seating arrangement")'
)

# Only create events if extraction confidence is >= this
MIN_CONFIDENCE = 0.70

# reminders in minutes
REMINDERS = [24 * 60, 2 * 60]
