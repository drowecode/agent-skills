#!/usr/bin/env python3
"""
gmail_adapter.py — Gmail API calls via the AIsa relay.

Handles:
  - Fetching unread messages and building a grouped digest
  - Fetching a full thread by threadId
  - Sending a reply, preserving threadId so it stays in the existing thread
"""

import base64
import json
import sys
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))
from setup_oauth import get_credentials


def get_service():
    from googleapiclient.discovery import build
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def fetch_digest(service) -> list[dict]:
    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=20,
    ).execute()

    stubs = result.get("messages", [])
    digest = []
    for stub in stubs:
        detail = service.users().messages().get(
            userId="me",
            id=stub["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        raw_date = headers.get("Date", "")
        try:
            dt = parsedate_to_datetime(raw_date)
            date_str = dt.strftime("%b %-d")
        except Exception:
            date_str = raw_date
        digest.append({
            "sender": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "date": date_str,
            "message_id": detail["id"],
            "thread_id": detail.get("threadId", stub["id"]),
        })
    return digest


def fetch_thread(service, thread_id: str) -> list[dict]:
    data = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full",
    ).execute()

    messages = []
    for msg in data.get("messages", []):
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        raw_date = headers.get("Date", "")
        try:
            dt = parsedate_to_datetime(raw_date)
            date_str = dt.strftime("%b %-d")
        except Exception:
            date_str = raw_date

        messages.append({
            "sender": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "date": date_str,
            "body": _extract_plain_body(payload),
            "message_id": msg["id"],
        })
    return messages


def send_reply(service, thread_id: str, body: str) -> dict:
    data = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="metadata",
    ).execute()

    latest = data["messages"][-1]
    headers = {h["name"]: h["value"] for h in latest.get("payload", {}).get("headers", [])}

    to = headers.get("From", "")
    raw_subject = headers.get("Subject", "")
    subject = raw_subject if raw_subject.startswith("Re:") else f"Re: {raw_subject}"
    message_id = headers.get("Message-ID", "")

    mime = "\r\n".join([
        f"To: {to}",
        f"Subject: {subject}",
        f"In-Reply-To: {message_id}",
        f"References: {message_id}",
        "Content-Type: text/plain; charset=utf-8",
        "MIME-Version: 1.0",
        "",
        body,
    ])
    encoded = base64.urlsafe_b64encode(mime.encode("utf-8")).decode("ascii").rstrip("=")
    return service.users().messages().send(
        userId="me",
        body={"raw": encoded, "threadId": thread_id},
    ).execute()


def _extract_plain_body(payload: dict) -> str:
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace").strip()
    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace").strip()
    return ""


class GmailAdapter:
    def __init__(self, base_url: str, api_key: str, access_token: str) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._token = access_token

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self._base}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "X-OAuth-Token": self._token,
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, payload: dict) -> Any:
        url = f"{self._base}{path}"
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "X-OAuth-Token": self._token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def fetch_digest(self, days: int = 7) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
        data = self._get(
            "/apis/v1/gmail/messages",
            {"q": f"is:unread after:{since}", "maxResults": 100},
        )
        messages = data.get("messages", [])

        # Group by sender (From header)
        groups: dict[str, dict] = {}
        for stub in messages:
            detail = self._get(f"/apis/v1/gmail/messages/{stub['id']}", {"format": "metadata"})
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            sender = headers.get("From", "Unknown")
            subject = headers.get("Subject", "(no subject)")
            thread_id = detail.get("threadId", stub["id"])

            if sender not in groups:
                groups[sender] = {
                    "sender": sender,
                    "subject_preview": subject[:80],
                    "count": 0,
                    "thread_id": thread_id,
                }
            groups[sender]["count"] += 1

        return sorted(groups.values(), key=lambda x: -x["count"])

    def fetch_thread(self, thread_id: str) -> list[dict]:
        data = self._get(f"/apis/v1/gmail/threads/{thread_id}", {"format": "full"})
        messages = []
        for msg in data.get("messages", []):
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            body = _extract_body(msg.get("payload", {}))
            messages.append(
                {
                    "id": msg["id"],
                    "thread_id": thread_id,
                    "date": headers.get("Date", ""),
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "subject": headers.get("Subject", ""),
                    "body": body,
                }
            )
        return messages

    def send_reply(self, thread_id: str, body: str) -> dict:
        # Fetch thread to derive To/Subject for the reply
        thread_data = self._get(f"/apis/v1/gmail/threads/{thread_id}", {"format": "metadata"})
        msgs = thread_data.get("messages", [])
        last = msgs[-1] if msgs else {}
        last_headers = {
            h["name"]: h["value"]
            for h in last.get("payload", {}).get("headers", [])
        }

        to = last_headers.get("From", "")
        subject = last_headers.get("Subject", "Re:")
        if not subject.startswith("Re:"):
            subject = "Re: " + subject

        raw_message = _build_mime(to=to, subject=subject, body=body, thread_id=thread_id)
        return self._post(
            "/apis/v1/gmail/messages/send",
            {"raw": raw_message, "threadId": thread_id},
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_body(payload: dict) -> str:
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        import base64
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def _build_mime(to: str, subject: str, body: str, thread_id: str) -> str:
    import base64
    msg_lines = [
        f"To: {to}",
        f"Subject: {subject}",
        "Content-Type: text/plain; charset=utf-8",
        "MIME-Version: 1.0",
        "",
        body,
    ]
    raw = "\r\n".join(msg_lines).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
