"""
agentmail_auth.py — Lightweight readiness check for AgentMail.

AgentMail uses API key authentication, so there is no OAuth flow, no
consent URL, no token file. The agent just needs AGENTMAIL_API_KEY in
the environment.
"""

import os


def is_ready() -> bool:
    """Returns True if AGENTMAIL_API_KEY is set and non-empty."""
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    return bool(key.strip())


def get_setup_instructions() -> dict:
    """Returns instructions for getting an AgentMail API key."""
    return {
        "instructions": (
            "Go to https://agentmail.to, create an account, generate an "
            "API key, and set AGENTMAIL_API_KEY in your environment."
        ),
        "env_var": "AGENTMAIL_API_KEY",
        "url": "https://agentmail.to",
    }
