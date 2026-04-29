"""
agentmail_adapter.py — Email backend backed by AgentMail (agentmail.to).

Authenticated via AGENTMAIL_API_KEY. No OAuth.

The AgentMail SDK is inbox-scoped for write operations but exposes a
flat top-level `client.threads` for reads across all inboxes the API
key can see.

SDK methods used:
  client.threads.list(limit, labels=["unread"]) -> ListThreadsResponse(.threads: List[ThreadItem])
  client.threads.get(thread_id)                 -> Thread (with .messages populated)
  client.inboxes.messages.reply(inbox_id, message_id, text=body) -> SendMessageResponse

See references/agentmail.md for full notes.

Public functions:
  fetch_digest(max_results=20) -> list[dict]
  fetch_thread(thread_id)      -> list[dict]
  send_reply(thread_id, body)  -> dict
"""

import os
import re
from datetime import datetime

from agentmail import AgentMail


def _client() -> AgentMail:
    api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AGENTMAIL_API_KEY not set. Get a key at https://agentmail.to "
            "and export AGENTMAIL_API_KEY=<your_key>."
        )
    return AgentMail(api_key=api_key)


def _format_date(ts) -> str:
    """ts is a datetime (Thread/Message.timestamp). Cross-platform 'Mon D'."""
    if ts is None:
        return ""
    if isinstance(ts, datetime):
        return f"{ts.strftime('%b')} {ts.day}"
    return str(ts)


def _primary_sender(senders: list[str]) -> str:
    if not senders:
        return "Unknown"
    return senders[0]


def _extract_plain_body(message) -> str:
    """Extract plain text body from an AgentMail Message.

    Prefers the literal text/plain part, then extracted_text, then strips
    HTML from the html/extracted_html part as a last resort.
    """
    text = getattr(message, "text", None)
    if text:
        return text.strip()
    extracted = getattr(message, "extracted_text", None)
    if extracted:
        return extracted.strip()
    html = getattr(message, "html", None) or getattr(message, "extracted_html", None)
    if html:
        return re.sub(r"<[^>]+>", " ", html).strip()
    return ""


def fetch_digest(max_results: int = 20) -> list[dict]:
    """List unread threads grouped by primary sender, most-frequent first."""
    client = _client()
    response = client.threads.list(limit=max_results, labels=["unread"])
    threads = getattr(response, "threads", []) or []

    groups: dict[str, dict] = {}
    for t in threads:
        sender = _primary_sender(t.senders)
        if sender not in groups:
            groups[sender] = {
                "sender": sender,
                "subject": t.subject or "(no subject)",
                "date": _format_date(t.timestamp),
                "message_id": t.last_message_id,
                "thread_id": t.thread_id,
                "count": 0,
            }
        groups[sender]["count"] += 1

    return sorted(groups.values(), key=lambda g: -g["count"])


def fetch_thread(thread_id: str) -> list[dict]:
    """Fetch all messages in a thread."""
    client = _client()
    thread = client.threads.get(thread_id)
    out = []
    for msg in (thread.messages or []):
        out.append({
            "sender": msg.from_ or "Unknown",
            "subject": msg.subject or "(no subject)",
            "date": _format_date(msg.timestamp),
            "body": _extract_plain_body(msg),
            "message_id": msg.message_id,
        })
    return out


def send_reply(thread_id: str, body: str) -> dict:
    """Reply to the latest message in the thread, preserving thread context.

    AgentMail's reply endpoint is inbox-scoped, so we fetch the thread first
    to resolve inbox_id and the latest message_id.
    """
    client = _client()
    thread = client.threads.get(thread_id)
    messages = thread.messages or []
    if not messages:
        raise ValueError(f"Thread {thread_id} has no messages to reply to.")
    latest = messages[-1]
    result = client.inboxes.messages.reply(
        inbox_id=latest.inbox_id,
        message_id=latest.message_id,
        text=body,
    )
    return {
        "id": getattr(result, "message_id", "") or getattr(result, "id", ""),
        "thread_id": thread_id,
    }
