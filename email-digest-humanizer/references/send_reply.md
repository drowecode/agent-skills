# Send Reply — Workflow, Threading Rules, and Confirmation UX

## Threading

### Gmail
- Every reply **must** include `"threadId": "<original-thread-id>"` in the send payload.
- Without it, Gmail treats the reply as a new standalone message, breaking the thread.
- The `threadId` is returned in every Gmail message object and thread fetch.

### Outlook
- Every reply must target the **latest message ID** in the conversation via `POST /messages/{id}/reply`.
- The relay sets `conversationId` automatically when replying to an existing message — the agent does not need to send it separately.
- Using `POST /sendMail` (new message) instead of `/reply` will create an orphaned message outside the thread.

## Confirmation UX

The `send` command always presents the humanized draft for review before sending, unless `--confirm` is passed explicitly.

Expected interaction:

```
── Reply to Send ──

Hi Sarah,

Works for me — I'll join the 3pm call. Could you send over the agenda doc beforehand?

Thanks

── End ──

Send this reply? [y/N]
```

- `y` → send via relay, print message ID + timestamp.
- Any other input → cancel, print "Send cancelled."

When `--confirm` is passed (e.g. in automated harness flows), the confirmation step is skipped and the reply is sent immediately.

## Agent Instructions

1. Never skip the review step unless `--confirm` is explicitly requested by the user.
2. After a successful send, report the message ID and timestamp.
3. If the send call returns an error, report the error verbatim — do not retry automatically.
4. Do not modify the humanized draft during the send step.
5. If the user asks to edit the draft before sending, reopen the draft file, apply edits, and re-present for confirmation.

## Guardrails

- Do not send to anyone other than the original sender without explicit user confirmation.
- Do not auto-send in a loop across multiple threads without per-thread confirmation.
- Do not strip or alter the humanized text at send time.
- Always use the thread/conversation ID from the original fetch — never derive or guess it.
