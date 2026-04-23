"""
setup_oauth.py — Agent-friendly Gmail OAuth library for email-digest-humanizer.

Never opens a browser or prints to stdout. The agent handles all user interaction.

Public API:
  is_authenticated() → bool
  get_auth_url()     → str
  exchange_code(code: str) → Credentials
  get_credentials()  → Credentials
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(_SKILL_DIR, "token.json")
CREDS_PATH = os.path.join(_SKILL_DIR, "credentials.json")

_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

_flow = None


def is_authenticated() -> bool:
    """Return True if token.json exists and credentials are valid (not expired)."""
    if not os.path.exists(TOKEN_PATH):
        return False
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return creds is not None and creds.valid


def get_auth_url() -> str:
    """Return the Google OAuth consent URL. Present this to the user."""
    global _flow
    _flow = Flow.from_client_secrets_file(CREDS_PATH, scopes=SCOPES)
    _flow.redirect_uri = _REDIRECT_URI
    auth_url, _ = _flow.authorization_url(access_type="offline", prompt="consent")
    return auth_url


def exchange_code(code: str) -> Credentials:
    """Exchange the authorization code for credentials and save to token.json."""
    global _flow
    if _flow is None:
        raise RuntimeError("Call get_auth_url() before exchange_code()")
    _flow.fetch_token(code=code)
    creds = _flow.credentials
    with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
        fh.write(creds.to_json())
    return creds



def get_credentials() -> Credentials:
    """Load credentials from token.json, refreshing automatically if expired."""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return creds
