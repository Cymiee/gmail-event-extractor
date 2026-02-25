from googleapiclient.discovery import build


def build_gmail_service(creds):
    return build("gmail", "v1", credentials=creds)


def get_or_create_label_id(service, user_id, label_name):
    """
    Returns labelId for label_name. Creates it if it doesn't exist.
    """
    resp = service.users().labels().list(userId=user_id).execute()
    for lab in resp.get("labels", []):
        if lab["name"] == label_name:
            return lab["id"]

    created = service.users().labels().create(
        userId=user_id,
        body={
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    ).execute()

    return created["id"]


def search_message_ids(service, user_id, query, max_results=10):
    resp = service.users().messages().list(
        userId=user_id, q=query, maxResults=max_results
    ).execute()
    return [m["id"] for m in resp.get("messages", [])]


def read_message_metadata(service, user_id, msg_id):
    """
    Reads just metadata so it's fast. (Subject/From/Date + snippet)
    """
    msg = service.users().messages().get(
        userId=user_id,
        id=msg_id,
        format="metadata",
        metadataHeaders=["Subject", "From", "Date"],
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    return {
        "id": msg_id,
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
    }


def add_label(service, user_id, msg_id, label_id):
    service.users().messages().modify(
        userId=user_id,
        id=msg_id,
        body={"addLabelIds": [label_id], "removeLabelIds": []},
    ).execute()