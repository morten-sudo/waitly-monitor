import requests
import json
import os
import sys

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
    print("Notification written:", message)


def clear_notification():
    with open(NOTIFICATION_FILE, "w") as f:
        f.write("")


def main():
    try:
        is_open = get_status()
    except Exception as e:
        print("Error fetching page:", e)
        sys.exit(0)  # fail silently, retry in 10 min

    previous = get_previous_status()

    print(f"Previous status: {previous} | Current status: {is_open}")

    if previous is None:
        # First run — save state without sending a notification
        print("First run — saving status without sending notification.")
        clear_notification()
    elif is_open != previous:
        if is_open:
            send_notification(f"🚨 The waitlist at Gasværksvej 12 is now OPEN! {URL}")
        else:
            send_notification("The waitlist is closed again.")
    else:
        print("No change.")
        clear_notification()

    save_status(is_open)


if __name__ == "__main__":
    main()
