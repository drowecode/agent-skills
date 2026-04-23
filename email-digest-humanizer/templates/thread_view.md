# Thread View Format

Display the full thread in chronological order with clear message boundaries.

## Example Output

```
── Thread (3 messages) ──

[Mon, 14 Apr 2026 09:12:33 +0000] Sarah Chen <sarah@example.com>
Subject: Q2 Budget Review

Hi,

Can we sync this week to go through the Q2 budget numbers? I've attached
the draft spreadsheet.

Let me know what times work for you.

Sarah

────────────────────────────────────────────────────────────────

[Mon, 14 Apr 2026 11:47:02 +0000] You <you@example.com>
Subject: Re: Q2 Budget Review

Sure, Thursday afternoon works. Sending a calendar invite.

────────────────────────────────────────────────────────────────

[Tue, 15 Apr 2026 08:03:11 +0000] Sarah Chen <sarah@example.com>
Subject: Re: Q2 Budget Review

Actually, could we do Wednesday instead? I have a conflict Thursday.

────────────────────────────────────────────────────────────────
```

## After Thread Display

Offer the reply option:

```
Reply to this thread? [y/N]  (or type a steering instruction, e.g. "confirm Wednesday works")
```

If the user types an instruction directly, use it as the `--instruction` value for the draft step.
