"""
email_client.py — Agent-native API for the email-digest-humanizer skill.

No terminal interaction, no print statements, no argparse.
The agent is the interface for all user interaction.

Public API:
  get_auth_url()                  -> dict
  authorize(code)                 -> dict
  is_ready()                      -> bool
  get_digest()                    -> list
  get_thread_with_draft(thread_id) -> dict
  send(thread_id, body)           -> dict
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentmail_adapter import fetch_digest, fetch_thread, send_reply
from agentmail_auth import get_setup_instructions, is_ready as _is_ready
from draft_engine import generate_draft
from humanizer_runner import humanize


def get_auth_url() -> dict:
    """AgentMail uses API keys — return setup instructions instead of an OAuth URL."""
    info = get_setup_instructions()
    return {"instructions": info["instructions"]}


def authorize(code: str = "") -> dict:
    """No-op for AgentMail. Kept for API compatibility."""
    return {
        "success": True,
        "message": (
            "AgentMail uses API keys, no OAuth required. "
            "Set AGENTMAIL_API_KEY and you're ready."
        ),
    }


def is_ready() -> bool:
    """Return True if AGENTMAIL_API_KEY is set."""
    return _is_ready()


def get_digest() -> list:
    """Return list of unread email dicts for the agent to display."""
    return fetch_digest()


def get_thread_with_draft(thread_id: str) -> dict:
    """Return the full thread messages and a humanized draft reply."""
    thread = fetch_thread(thread_id)
    raw_draft = generate_draft(thread)
    humanized = humanize(raw_draft)
    return {
        "thread": thread,
        "draft": humanized,
    }


def send(thread_id: str, body: str) -> dict:
    """Send the reply. Returns {"success": True, "message_id": "..."} or {"error": "..."}"""
    try:
        result = send_reply(thread_id, body)
        return {"success": True, "message_id": result.get("id", "")}
    except Exception as exc:
        return {"error": str(exc)}
