# Waitly Monitor — Project Overview

## Purpose
Monitors a Waitly waitlist signup page for status changes and sends email
notifications via Gmail SMTP. Runs automatically every 5 minutes during
active hours (06:00–23:00 Copenhagen time).

## Repository
- **GitHub:** https://github.com/morten-sudo/waitly-monitor (public)
- **Local path:** /Users/mortensondergaard/Projects/Waitly
- **Branch:** main

## Files
| File | Purpose |
|---|---|
| `monitor.py` | Fetches the Waitly page, detects status, writes notification.txt |
| `.github/workflows/check.yml` | GitHub Actions workflow — quiet hours, email, state commit |
| `state.json` | Persists last known status (`{"is_open": true/false}`) |
| `notification.txt` | Written by monitor.py each run; first line = email subject, rest = body |

## How It Works

### Trigger
The GitHub Actions workflow is **not** triggered by GitHub's built-in scheduler
(unreliable). Instead, **cron-job.org** calls the GitHub API every 5 minutes
to trigger a `workflow_dispatch` event:
- **cron-job.org URL:** `https://api.github.com/repos/morten-sudo/waitly-monitor/actions/workflows/check.yml/dispatches`
- **Method:** POST
- **Headers:** `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`
- **Body:** `{"ref": "main"}`

### Workflow Steps (check.yml)
1. **Check quiet hours** — reads Copenhagen local time via `TZ=Europe/Copenhagen date +%H`. Sets `skip=true` if hour ≥ 23 or < 6. All subsequent steps are skipped during quiet hours; the job still completes as success.
2. **Check out repo** — checks out main branch
3. **Set up Python 3.12** — installs Python
4. **Install dependencies** — `pip install requests` (only dependency)
5. **Run check** — runs `monitor.py`
6. **Check whether notification should be sent** — checks if `notification.txt` has content (`-s` test)
7. **Send email via Gmail** — inline Python using `smtplib.SMTP_SSL` on port 465. Splits `notification.txt` on first newline: first line → subject, rest → body. Strips spaces and `\xa0` from app password to handle copy-paste encoding issues.
8. **Commit updated status to repo** — commits `state.json` back with `[skip ci]`. Runs with `if: always()` so it fires even if the email step fails.

### monitor.py Logic
1. Fetches the Waitly signup page HTML with a browser User-Agent
2. Checks if the Danish closed-text string is present in the HTML:
   `"Der er desværre lukket for nye tilmeldinger til denne liste"`
3. If the string is absent → list is open (`is_open: true`)
4. Reads previous status from `state.json`
5. Writes to `notification.txt` on **every run** — three message variants:
   - **First run** (`previous is None`): simple status report
   - **Status changed** (`is_open != previous`): urgent open/closed messages
   - **No change**: plain "Status uændret" report

### Email Format
`notification.txt` always has the format:
```
SUBJECT LINE
(blank line)
Body text...
```
The email step splits on the first `\n` to extract subject and body.

**Message variants:**

| Situation | Subject | Emoji |
|---|---|---|
| First run | `Waitly: Første kørsel — status {åben/lukket}` | None |
| List opened | `🚨 Waitly-listen er åben NU` | 🚨 |
| List closed again | `Waitly-listen er lukket igen` | None |
| No change | `Waitly: Status uændret (åben/lukket)` | None |

All messages include a Copenhagen timestamp (`DD-MM-YYYY HH:MM`) and the signup URL.

## Waitly Target
- **URL:** `https://app.waitly.dk/signup/3c179506-00d9-4cf7-8840-a2d9cfa6a8bd`
- **List name:** A/B Gasværksvej 12 M FL - Ekstern venteliste
- **Detection:** Absence of the Danish closed-text string in the page HTML

## GitHub Actions Secrets
Set in repo Settings → Secrets and variables → Actions:

| Secret | Description |
|---|---|
| `GMAIL_ADDRESS` | Gmail address used for sending and receiving notifications |
| `GMAIL_APP_PASSWORD` | Gmail App Password (16 chars; spaces stripped automatically by the script) |

## State Management
- `state.json` contains `{"is_open": true}` or `{"is_open": false}`
- Written by `monitor.py` at the end of every run
- Committed back to the repo by the workflow with `[skip ci]` to avoid loops
- To trigger a test email manually: flip `state.json` to `{"is_open": true}`, push, then run `gh workflow run check.yml --repo morten-sudo/waitly-monitor`

## Triggering a Test Email Manually
```bash
# From the local repo directory:
git pull origin main
# Edit state.json to {"is_open": true}
git add state.json && git commit -m "Temporarily flip state.json to trigger test email" && git push origin main
gh workflow run check.yml --repo morten-sudo/waitly-monitor
```

## Known Issues / Design Decisions
- **GitHub scheduler unreliable:** The built-in cron trigger (`schedule:`) never fired reliably after the repo was made public. cron-job.org is used instead as an external trigger via `workflow_dispatch`.
- **Gmail App Password encoding:** When copied from Google's UI, the spaces between character groups are `\xa0` (non-breaking spaces), which breaks ASCII encoding in `smtplib`. The script strips all spaces and `\xa0` from the password before use.
- **body_path not supported:** `dawidd6/action-send-mail@v3` does not support `body_path`. The email step uses inline Python (`smtplib`) instead.
- **Quiet hours state:** The "Commit updated status" step uses `if: always() && steps.quiet_hours.outputs.skip != 'true'` so state.json is only committed when a real check ran, but still commits even if the email step fails.
- **CLOSED_TEXT is Danish:** The string we check for in the HTML is Danish (`"Der er desværre lukket..."`) — this is intentional and must not be translated, as it is the literal text on the Waitly page.

## Dependencies
- Python 3.12
- `requests` (pip) — fetching the Waitly page
- `smtplib`, `email.mime.text`, `zoneinfo`, `datetime` — all standard library
- No Twilio dependency (removed; early commits contain Twilio references in history)
