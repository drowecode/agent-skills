# Gmail OAuth Flow

**OAuth 2.0 authorization for Gmail read + send access. Powered by AIsa.**

## Required Scopes

| Scope | Purpose |
|---|---|
| `https://www.googleapis.com/auth/gmail.readonly` | Read inbox, list messages, fetch threads |
| `https://www.googleapis.com/auth/gmail.send` | Send replies |

## Flow

1. Agent calls `POST /apis/v1/oauth/gmail/authorize` with `AISA_API_KEY`.
2. Relay returns `{"auth_url": "https://accounts.google.com/o/oauth2/..."}`.
3. User opens the URL in a browser and completes Google's consent screen.
4. Google redirects to the relay callback with an authorization code.
5. Relay exchanges the code for an access token and returns it to the agent.
6. Agent stores the token in `EMAIL_ACCESS_TOKEN_GMAIL` for the session only.

## Token Policy

- Only the short-lived access token is stored — in an environment variable, never on disk.
- Refresh tokens are handled server-side by the relay and are never exposed to the agent.
- Tokens are scoped to the session; they are discarded when the session ends.

## Agent Instructions

When the user asks to authorize Gmail:

1. Call `python3 {baseDir}/scripts/email_client.py authorize --provider gmail`.
2. Return the `auth_url` to the user and instruct them to open it in a browser.
3. After they confirm authorization, the relay will have issued a token.
4. Instruct the user to set `export EMAIL_ACCESS_TOKEN_GMAIL=<token>` in the shell, or do so if the harness allows env injection.
5. Proceed with `digest` only after the token is confirmed set.

## Guardrails

- Never ask for the user's Google password.
- Never store the access token in a file.
- Never log or print the raw token in output.
- If the token is expired, re-run `authorize` — do not attempt manual refresh.
