"""
draft_engine.py — Generates an AI reply draft from a full email thread via AIsa API.
"""

import os

import requests

AISA_API_KEY = os.environ.get("AISA_API_KEY")
AISA_API_URL = "https://api.aisa.one/v1/messages"

SYSTEM_PROMPT = (
    "You are a professional email assistant. Given the email thread below, "
    "write a concise, natural reply on behalf of the recipient. "
    "Do not include a subject line or greeting boilerplate. Just the reply body."
)


def format_thread(thread: list) -> str:
    return "\n\n".join(
        f"From: {m['sender']}\nDate: {m['date']}\n\n{m['body']}"
        for m in thread
    )


def generate_draft(thread: list) -> str:
    """Returns a plain text reply draft based on the full thread context."""
    formatted = format_thread(thread)
    response = requests.post(
        AISA_API_URL,
        headers={
            "Authorization": f"Bearer {AISA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": formatted}],
        },
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]
