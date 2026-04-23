# Digest Table Format

Display the unread inbox digest as a fixed-width table with three columns.

## Column Widths

| Column | Width | Truncate |
|---|---|---|
| Sender | 30 chars | yes, with … |
| Subject Preview | 55 chars | yes, with … |
| Emails | 7 chars, right-aligned | no |

## Example Output

```
Sender                          Subject Preview                                          Emails
─────────────────────────────────────────────────────────────────────────────────────────────
Sarah Chen <sarah@example.com>  Re: Q2 Budget Review                                         3  [18f3a7b9c2d4]
DevOps Alerts <ops@infra.io>    [WARN] Disk usage at 87% on prod-db-01 — 2026-04-…           7  [19a4b8c0d3e5]
newsletter@acme.io              This week in product — April 19                              1  [1ab2c3d4e5f6]
```

## After Digest

Prompt the user:

```
Enter a sender name or thread ID to view the full thread, or 'q' to quit:
```

Accept:
- Partial sender name match (case-insensitive)
- Full thread ID / conversation ID
- Row number (1-indexed)
