#!/usr/bin/env python3
"""
humanizer_runner.py — Runs text through the Humanizer skill.

Resolution order:
  1. HUMANIZER_PATH env var — path to a local humanizer install
  2. humanizer Python package on sys.path
  3. Fallback: AIsa API rewrite pass with a warnings.warn notice
"""

import os
import sys
import warnings

import requests

AISA_API_KEY = os.environ.get("AISA_API_KEY")
AISA_API_URL = "https://api.aisa.one/v1/messages"

_SYSTEM_PROMPT = (
    "Rewrite the following text to remove all signs of AI-generated writing. "
    "Remove filler phrases like 'I hope this finds you well', avoid em-dashes, "
    "eliminate corporate buzzwords like 'circle back' and 'touch base', use simple "
    "direct language, vary sentence length naturally. "
    "Return only the rewritten text, nothing else."
)


def humanize(text: str) -> str:
    humanizer_path = os.environ.get("HUMANIZER_PATH")
    if humanizer_path and os.path.isdir(humanizer_path):
        sys.path.insert(0, humanizer_path)

    try:
        from humanizer import Humanizer  # type: ignore
        return Humanizer().rewrite(text)
    except ImportError:
        pass

    warnings.warn(
        "Humanizer skill not found. Set HUMANIZER_PATH or install from "
        "https://github.com/blader/humanizer — running inline fallback."
    )

    response = requests.post(
        AISA_API_URL,
        headers={
            "Authorization": f"Bearer {AISA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": text}],
        },
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]
