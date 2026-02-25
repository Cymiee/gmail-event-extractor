# Scopes:
# - gmail.modify lets us add a label so we don't re-process emails
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

LABEL_NAME = "AutoCalendar/Reviewed"
MAX_RESULTS = 15

# A simple query you can tweak.
# - newer_than:14d keeps it recent
# - -label:"AutoCalendar/Reviewed" prevents duplicates
GMAIL_QUERY = (
    'newer_than:14d '
    f'-label:"{LABEL_NAME}" '
    '(workshop OR competition OR quiz OR exam OR midsem OR compre OR deadline OR register)'
)
