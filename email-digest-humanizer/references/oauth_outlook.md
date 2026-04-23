# Outlook OAuth Flow (Microsoft Graph)

**OAuth 2.0 authorization for Outlook/Microsoft Graph read + send access. Powered by AIsa.**

## Required Scopes

| Scope | Purpose |
|---|---|
| `Mail.Read` | Read inbox, list messages, fetch conversation threads |
| `Mail.Send` | Send replies |
| `offline_access` | Allows relay to refresh token server-side (not exposed to agent) |

## Flow

1. Agent calls `POST /apis/v1/oauth/outlook/authorize` with `AISA_API_KEY`.
2. Relay returns `{"auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."}`.
3. User opens the URL and completes Microsoft's consent screen.
4. Microsoft redirects to the relay callback with an authorization code.
5. Relay exchanges for access + refresh tokens; only the access token is returned.
6. Agent stores the token in `EMAIL_ACCESS_TOKEN_OUTLOOK` for the session only.

## Token Policy

- Only the short-lived access token is in scope for the agent.
- The relay manages refresh server-side; refresh tokens are never exposed.
- Tokens are session-scoped and never written to disk.

## Agent Instructions

When the user asks to authorize Outlook:

1. Call `python3 {baseDir}/scripts/email_client.py authorize --provider outlook`.
2. Return the `auth_url` to the user and ask them to open it in a browser.
3. After consent, instruct the user to set `export EMAIL_ACCESS_TOKEN_OUTLOOK=<token>`.
4. Proceed with `digest` only once the token env var is set.

## Guardrails

- Never ask for the user's Microsoft password or MFA codes.
- Never store the access token in any file.
- Never print the raw token value.
- If auth fails, re-run `authorize` — do not attempt to reuse an expired token.
- Personal Microsoft accounts and work/school (Azure AD) accounts are both supported via the `/common` tenant endpoint.
