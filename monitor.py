import requests
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# The page has no JSON API — it is server-rendered HTML.
# We check for the Danish closed-text string directly in the HTML.
URL = "https://app.waitly.dk/signup/3c179506-00d9-4cf7-8840-a2d9cfa6a8bd"
CLOSED_TEXT = "Der er desværre lukket for nye tilmeldinger til denne liste"
STATE_FILE = "state.json"
NOTIFICATION_FILE = "notification.txt"


def get_status():
    headers = {
        # Some sites block requests without a real browser User-Agent
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()
    html = response.text

    is_closed = CLOSED_TEXT in html
    return not is_closed  # True = open, False = closed


def get_previous_status():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("is_open")
    return None


def save_status(is_open):
    with open(STATE_FILE, "w") as f:
        json.dump({"is_open": is_open}, f)


def send_notification(message):
    with open(NOTIFICATION_FILE, "w") as f:
        f.write(message)
    subject = message.split('\n', 1)[0]
    print("Notification written:", subject)


def main():
    try:
        is_open = get_status()
    except Exception as e:
        print("Error fetching page:", e)
        sys.exit(0)  # fail silently, retry in 5 min

    previous = get_previous_status()

    print(f"Previous status: {previous} | Current status: {is_open}")

    timestamp = datetime.now(ZoneInfo("Europe/Copenhagen")).strftime("%d-%m-%Y %H:%M")
    status_str = "åben" if is_open else "lukket"

    if previous is None:
        print("First run — sending initial status report.")
        send_notification(
            f"Waitly: Første kørsel — status {status_str}\n"
            f"\nFørste kørsel registreret kl. {timestamp}\n"
            f"\nNuværende status: Listen er {status_str}.\n"
            f"\nSe listen her: {URL}\n"
            f"\n(Dette er en automatisk besked fra dit overvågningsscript)"
        )
    elif is_open != previous:
        if is_open:
            send_notification(
                f"🚨 Waitly-listen er åben NU\n"
                f"\nStatus ændret kl. {timestamp}\n"
                f"\nListen \"A/B Gasværksvej 12 M FL - Ekstern venteliste\" er skiftet fra lukket til åben.\n"
                f"\nTilmeld dig her: {URL}\n"
                f"\n(Dette er en automatisk besked fra dit overvågningsscript)"
            )
        else:
            send_notification(
                f"Waitly-listen er lukket igen\n"
                f"\nStatus ændret kl. {timestamp}\n"
                f"\nListen \"A/B Gasværksvej 12 M FL - Ekstern venteliste\" er skiftet fra åben til lukket.\n"
                f"\nSe listen her: {URL}\n"
                f"\n(Dette er en automatisk besked fra dit overvågningsscript)"
            )
    else:
        print("No change — no notification sent.")
        with open(NOTIFICATION_FILE, "w") as f:
            f.write("")

    save_status(is_open)


if __name__ == "__main__":
    main()
