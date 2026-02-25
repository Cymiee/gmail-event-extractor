from googleapiclient.discovery import build


def build_calendar_service(creds):
    return build("calendar", "v3", credentials=creds)


def create_event(cal_service, calendar_id, event):
    """
    event = dict with keys: summary, start(dt), end(dt), description, location
    """
    body = {
        "summary": event["summary"],
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": {"dateTime": event["start"].isoformat()},
        "end": {"dateTime": event["end"].isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": m} for m in event.get("reminders", [])],
        },
    }
    return cal_service.events().insert(calendarId=calendar_id, body=body).execute()