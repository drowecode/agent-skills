#!/usr/bin/env python3
"""
outlook_adapter.py — Microsoft Graph / Outlook calls via the AIsa relay.

Handles:
  - Fetching unread messages and building a grouped digest
  - Fetching all messages in a conversationId thread
  - Sending a reply, preserving conversationId for correct threading
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


class OutlookAdapter:
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
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = self._get(
            "/apis/v1/outlook/messages",
            {
                "filter": f"isRead eq false and receivedDateTime ge {since}",
                "$top": 100,
                "$select": "from,subject,conversationId,receivedDateTime",
                "$orderby": "receivedDateTime desc",
            },
        )
        messages = data.get("value", [])

        groups: dict[str, dict] = {}
        for msg in messages:
            sender_obj = msg.get("from", {}).get("emailAddress", {})
            sender = f"{sender_obj.get('name', '')} <{sender_obj.get('address', '')}>".strip()
            subject = msg.get("subject", "(no subject)")
            conv_id = msg.get("conversationId", "")

            if sender not in groups:
                groups[sender] = {
                    "sender": sender,
                    "subject_preview": subject[:80],
                    "count": 0,
                    "conversation_id": conv_id,
                }
            groups[sender]["count"] += 1

        return sorted(groups.values(), key=lambda x: -x["count"])

    def fetch_thread(self, conversation_id: str) -> list[dict]:
        data = self._get(
            "/apis/v1/outlook/messages",
            {
                "filter": f"conversationId eq '{conversation_id}'",
                "$top": 50,
                "$select": "from,toRecipients,subject,body,receivedDateTime,conversationId",
                "$orderby": "receivedDateTime asc",
            },
        )
        messages = []
        for msg in data.get("value", []):
            sender_obj = msg.get("from", {}).get("emailAddress", {})
            body_content = msg.get("body", {}).get("content", "")
            messages.append(
                {
                    "id": msg.get("id", ""),
                    "conversation_id": conversation_id,
                    "date": msg.get("receivedDateTime", ""),
                    "from": f"{sender_obj.get('name', '')} <{sender_obj.get('address', '')}>",
                    "to": ", ".join(
                        r.get("emailAddress", {}).get("address", "")
                        for r in msg.get("toRecipients", [])
                    ),
                    "subject": msg.get("subject", ""),
                    "body": _strip_html(body_content),
                }
            )
        return messages

    def send_reply(self, conversation_id: str, body: str) -> dict:
        # Fetch the most recent message in the conversation to reply to its ID
        data = self._get(
            "/apis/v1/outlook/messages",
            {
                "filter": f"conversationId eq '{conversation_id}'",
                "$top": 1,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject",
            },
        )
        msgs = data.get("value", [])
        if not msgs:
            raise ValueError(f"No messages found for conversationId {conversation_id}")

        last_id = msgs[0]["id"]
        result = self._post(
            f"/apis/v1/outlook/messages/{last_id}/reply",
            {
                "message": {
                    "body": {"contentType": "Text", "content": body}
                }
            },
        )
        return result or {"id": last_id, "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_html(html: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()
