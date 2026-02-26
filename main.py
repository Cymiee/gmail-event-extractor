from auth import get_creds
from gmail import (
    build_gmail_service,
    get_or_create_label_id,
    search_message_ids,
    read_message_metadata,
    add_label,
    read_message_full,
    extract_body_text,
)
from calendar_client import build_calendar_service, create_event
from extractor import extract_event
from store import load_store, save_store

from config import (
    SCOPES,
    LABEL_NAME,
    GMAIL_QUERY,
    MAX_RESULTS,
    DEFAULT_TZ,
    CALENDAR_ID,
    MIN_CONFIDENCE,
    REMINDERS,
)


def main():
    creds = get_creds(SCOPES)
    gmail = build_gmail_service(creds)
    cal = build_calendar_service(creds)

    user_id = "me"
    label_id = get_or_create_label_id(gmail, user_id, LABEL_NAME)

    store = load_store("processed.json")  # msg_id -> event_id

    msg_ids = search_message_ids(gmail, user_id, GMAIL_QUERY, MAX_RESULTS)
    if not msg_ids:
        print("No matching emails found.")
        return

    print(f"Found {len(msg_ids)} emails:\n")

    for i, msg_id in enumerate(msg_ids, start=1):
        if msg_id in store:
            continue

        meta = read_message_metadata(gmail, user_id, msg_id)

        full_msg = read_message_full(gmail, user_id, msg_id)
        body = extract_body_text(full_msg)

        extracted = extract_event(
            meta["subject"], body or meta["snippet"], default_tz=DEFAULT_TZ
        )
        if not extracted:
            print(f"SKIP (no datetime): {meta['subject']}")
            continue

        if extracted.confidence < MIN_CONFIDENCE:
            print(
                f"SKIP (low confidence {extracted.confidence:.2f}): {meta['subject']}"
            )
            continue

        desc = ""
        if extracted.link:
            desc += f"Link: {extracted.link}\n"
        desc += f"From: {meta['from']}\n"

        event_payload = {
            "summary": extracted.summary,
            "start": extracted.start,
            "end": extracted.end,
            "location": extracted.location or "",
            "description": desc.strip(),
            "reminders": REMINDERS,
        }

        created = create_event(cal, CALENDAR_ID, event_payload)
        event_id = created.get("id")

        print("=" * 70)
        print(f"{i}. ADDED: {meta['subject']}")
        print(f"Start: {extracted.start}")
        print(f"Link:  {created.get('htmlLink')}")

        store[msg_id] = event_id
        save_store(store, "processed.json")

        # Only label after successfully creating calendar event
        add_label(gmail, user_id, msg_id, label_id)

    print("\nDone.")


if __name__ == "__main__":
    main()
