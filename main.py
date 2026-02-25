from auth import get_creds
from gmail import (
    build_gmail_service,
    get_or_create_label_id,
    search_message_ids,
    read_message_metadata,
    add_label,
)
from config import SCOPES, LABEL_NAME, GMAIL_QUERY, MAX_RESULTS


def main():
    creds = get_creds(SCOPES)
    gmail = build_gmail_service(creds)

    user_id = "me"
    label_id = get_or_create_label_id(gmail, user_id, LABEL_NAME)

    msg_ids = search_message_ids(gmail, user_id, GMAIL_QUERY, MAX_RESULTS)

    if not msg_ids:
        print("No matching emails found.")
        return

    print(f"Found {len(msg_ids)} emails:\n")

    for i, msg_id in enumerate(msg_ids, start=1):
        meta = read_message_metadata(gmail, user_id, msg_id)

        print("=" * 70)
        print(f"{i}. {meta['subject']}")
        print(f"From: {meta['from']}")
        print(f"Date: {meta['date']}")
        print(f"Snippet: {meta['snippet']}\n")

        # Mark as processed (label it)
        add_label(gmail, user_id, msg_id, label_id)

    print("\nDone. Labeled processed emails as:", LABEL_NAME)


if __name__ == "__main__":
    main()