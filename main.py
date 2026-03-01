import argparse

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
    parser = argparse.ArgumentParser(description="Gmail → Google Calendar event extractor")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without actually creating calendar events",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] No events will be created.\n")

    creds = get_creds(SCOPES)
    gmail = build_gmail_service(creds)
    cal = build_calendar_service(creds)

    user_id = "me"
    label_id = get_or_create_label_id(gmail, user_id, LABEL_NAME)

    store = load_store("processed.json")  # msg_id -> event_id or None (skipped)

    msg_ids = search_message_ids(gmail, user_id, GMAIL_QUERY, MAX_RESULTS)
    if not msg_ids:
        print("No matching emails found.")
        return

    print(f"Found {len(msg_ids)} emails.\n")

    added = 0
    skipped = 0
    errors = 0

    for i, msg_id in enumerate(msg_ids, start=1):
        if msg_id in store:
            continue

        try:
            meta = read_message_metadata(gmail, user_id, msg_id)
            full_msg = read_message_full(gmail, user_id, msg_id)
            body = extract_body_text(full_msg)

            extracted = extract_event(
                meta["subject"], body or meta["snippet"], default_tz=DEFAULT_TZ
            )

            if not extracted:
                print(f"SKIP (no date found):          {meta['subject']}")
                store[msg_id] = None
                save_store(store, "processed.json")
                skipped += 1
                continue

            if extracted.confidence < MIN_CONFIDENCE:
                print(f"SKIP (low confidence {extracted.confidence:.2f}):  {meta['subject']}")
                store[msg_id] = None
                save_store(store, "processed.json")
                skipped += 1
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

            print("=" * 70)
            print(f"{i}. {meta['subject']}")
            print(f"   Start:    {extracted.start}")
            print(f"   End:      {extracted.end}")
            print(f"   Conf:     {extracted.confidence:.2f}")
            if extracted.location:
                print(f"   Location: {extracted.location}")

            if args.dry_run:
                print("   [DRY RUN] Skipping calendar insert.")
                added += 1
                continue

            created = create_event(cal, CALENDAR_ID, event_payload)
            event_id = created.get("id")
            print(f"   Link:     {created.get('htmlLink')}")

            store[msg_id] = event_id
            save_store(store, "processed.json")
            add_label(gmail, user_id, msg_id, label_id)
            added += 1

        except Exception as e:
            print(f"ERROR on message {msg_id}: {e}")
            errors += 1

    print(f"\nDone. Added: {added}  Skipped: {skipped}  Errors: {errors}")


if __name__ == "__main__":
    main()
