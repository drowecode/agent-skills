# AgentMail Integration

Backend reference for `email-digest-humanizer`. AgentMail (https://agentmail.to) gives agents two-way inboxes via simple API key auth — no OAuth, no consent screens, no `credentials.json`.

Docs: https://docs.agentmail.to

---

## Setup

1. Sign up at https://agentmail.to
2. Generate an API key from the dashboard
3. Export it before launching the agent:

```bash
export AGENTMAIL_API_KEY=your_key_here
export AISA_API_KEY=your_key_here   # for draft generation + humanizer fallback
```

That's it. `is_ready()` returns `True` as soon as `AGENTMAIL_API_KEY` is non-empty.

---

## Required environment variables

| Var | Purpose |
|---|---|
| `AGENTMAIL_API_KEY` | Authenticates every AgentMail SDK call (read inbox, fetch thread, send reply). |
| `AISA_API_KEY` | Used by `draft_engine.py` for AI-drafted replies and by `humanizer_runner.py` as a fallback when the local Humanizer skill isn't installed. |

---

## SDK shape (verified against the installed `agentmail` package)

The SDK is **inbox-scoped for writes**, but exposes a **flat top-level `client.threads`** for reads across all inboxes the key can see. That lets `fetch_digest` and `fetch_thread` ignore inbox routing entirely; only `send_reply` needs the inbox id (which it pulls off the latest message in the thread).

### Client construction

```python
from agentmail import AgentMail
client = AgentMail(api_key=os.environ["AGENTMAIL_API_KEY"])
```

### Methods used by `agentmail_adapter.py`

```python
# 1) Digest — list unread threads across all inboxes
response = client.threads.list(limit=20, labels=["unread"])
# response.threads -> List[ThreadItem]
# ThreadItem fields: inbox_id, thread_id, labels, timestamp (datetime),
#                    senders (List[str]), recipients (List[str]),
#                    subject, preview, last_message_id, message_count, ...

# 2) Expand — fetch a single thread with all messages
thread = client.threads.get(thread_id)
# thread.messages -> List[Message]
# Message fields: inbox_id, thread_id, message_id, labels, timestamp,
#                 from_, to, cc, bcc, subject, text, html,
#                 extracted_text, extracted_html, in_reply_to, references, ...

# 3) Reply — inbox-scoped, requires inbox_id + message_id from the thread
result = client.inboxes.messages.reply(
    inbox_id=latest.inbox_id,
    message_id=latest.message_id,
    text=body,
)
# result -> SendMessageResponse (.message_id)
```

### Other client surface (not used here but available)

- `client.inboxes.{create,get,list,update,delete}` — manage inboxes
- `client.inboxes.messages.{send,forward,reply_all,update}` — full message ops
- `client.inboxes.drafts.{create,send,update,...}` — server-side drafts
- `client.webhooks`, `client.websockets` — push delivery
- `client.api_keys`, `client.domains`, `client.organizations`, `client.metrics`

---

## Notes & assumptions

- **Unread filter:** `client.threads.list(labels=["unread"])` is how the digest filters. AgentMail tracks read state via labels; "unread" is the assumed standard label name. If it returns nothing on a known-unread inbox, swap the label name in `agentmail_adapter.fetch_digest`.
- **Sender grouping:** `ThreadItem.senders` is a `List[str]`. The adapter groups by `senders[0]` (the primary sender). Threads with multiple senders fall under the first one.
- **Date formatting:** `timestamp` is a `datetime`, so the adapter uses `f"{ts.strftime('%b')} {ts.day}"` — cross-platform (no `%-d`, no `%#d`).
- **Reply requires `inbox_id`:** there's no thread-level reply endpoint. `send_reply` re-fetches the thread to grab `inbox_id` + `message_id` off the latest message before calling `client.inboxes.messages.reply`.
- **Plain-text extraction priority:** `Message.text` → `Message.extracted_text` → HTML-stripped `Message.html`/`extracted_html`.
