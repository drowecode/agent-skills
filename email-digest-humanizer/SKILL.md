---
name: email-digest-humanizer
description: "Reads unread Gmail inbox via OAuth, groups emails into a digest by sender, drafts AI replies using the full thread as context, runs each draft through the Humanizer skill to strip AI-writing patterns, then sends the humanized reply — threaded correctly using threadId. Trigger when the user asks to check email, draft replies, clear inbox, or respond to messages without manually composing."
homepage: https://aisa.one
metadata: {"aisa":{"emoji":"📬","requires":{"bins":["python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY","compatibility":["openclaw","claude-code","hermes"]}}
---

# Email Digest Humanizer 📬

**OAuth Gmail access, AI-drafted replies, humanizer-polished sends — fully agent-native.**

---

## Setup

```bash
cd email-digest-humanizer
bash setup.sh
```

Place `credentials.json` (downloaded from Google Cloud Console) in the skill root before first use.

---

## Agent behavior

The agent is the sole interface. No CLI, no terminal prompts.

### On first use (not authenticated)

```python
from scripts.email_client import is_ready, get_auth_url, authorize
```

1. Call `is_ready()` — if `False`, call `get_auth_url()`
2. Tell the user:
   > "To connect your Gmail, open this link and paste the code back here: {url}"
3. When the user pastes the code, call `authorize(code)`
4. Confirm: "You're connected! Ask me to check your emails anytime."

---

### Reading emails

```python
from scripts.email_client import get_digest
```

1. Call `get_digest()`
2. Display as a numbered list:

```
📬 You have X unread emails:

1. Karen Sheng — "Re: onboarding" (Apr 22)
2. Newegg — "Gaming Sale" (Apr 22)
3. Google Cloud — "Welcome to Free Trial" (Apr 20)
```

3. Tell the user: "Reply with a number to expand any email and see a draft reply."

---

### Expanding an email

```python
from scripts.email_client import get_thread_with_draft
```

1. User says "expand 1" or "open the Karen email"
2. Call `get_thread_with_draft(thread_id)`
3. Display:

```
📧 From: Karen Sheng
Subject: Re: onboarding
Date: Apr 22

[full email body]

✏️ Suggested reply:
[humanized draft]

Send this reply? (yes / edit / skip)
```

4. If user says **yes** → call `send(thread_id, draft)`
5. If user says **edit** → let them type changes, then call `send(thread_id, edited_body)`
6. If user says **skip** → return to digest

---

### Sending

```python
from scripts.email_client import send
```

Always present the draft for review before calling `send`. Never auto-send.

---

## API Reference

```python
from scripts.email_client import (
    get_auth_url,           # -> str: OAuth consent URL
    authorize,              # (code: str) -> {"success": True} | {"error": "..."}
    is_ready,               # -> bool
    get_digest,             # -> list of email dicts
    get_thread_with_draft,  # (thread_id: str) -> {"thread": [...], "draft": "..."}
    send,                   # (thread_id: str, body: str) -> {"success": True, "message_id": "..."} | {"error": "..."}
)
```

### Email dict shape (from `get_digest`)

```json
{
  "sender": "Karen Sheng <karen@example.com>",
  "subject": "Re: onboarding",
  "date": "Apr 22",
  "message_id": "abc123",
  "thread_id": "xyz789"
}
```

### Thread message shape (from `get_thread_with_draft`)

```json
{
  "sender": "Karen Sheng <karen@example.com>",
  "subject": "Re: onboarding",
  "date": "Apr 22",
  "body": "Hey Daniel, just wanted to follow up...",
  "message_id": "abc123"
}
```

---

## Guardrails

- Never send a reply without explicit user confirmation.
- Never skip the Humanizer pass — always run the draft through humanize before presenting it.
- Do not synthesize thread content — use only the actual fetched message bodies.
- If `send` returns `{"error": "..."}`, report the error and do not retry automatically.
- Do not read or act on emails outside the unread set unless the user explicitly requests it.
- If the user asks to send to a different recipient than the original sender, confirm before proceeding.

---

## Dependencies

- `AISA_API_KEY` — AIsa platform key (AI draft generation + humanizer fallback)
- `credentials.json` — Google OAuth client secrets (from Google Cloud Console)
- `python3` 3.8+
- `google-auth-oauthlib`, `google-api-python-client`, `requests`
- **Humanizer skill** (optional) — [`github.com/blader/humanizer`](https://github.com/blader/humanizer) — if absent, falls back to AIsa API rewrite

---

## Module Map

| File | Role |
|---|---|
| `scripts/email_client.py` | Agent-facing API — primary entry point |
| `scripts/setup_oauth.py` | OAuth flow functions (no browser, no prompts) |
| `scripts/gmail_adapter.py` | Gmail API calls (fetch, thread, send) |
| `scripts/draft_engine.py` | Generates draft via AIsa API |
| `scripts/humanizer_runner.py` | Runs Humanizer skill or AIsa rewrite fallback |
