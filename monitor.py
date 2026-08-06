import requests
import json
import os
import sys
from twilio.rest import Client

# ── Konfiguration ──────────────────────────────────────────────
# Siden har ingen JSON-API - den er server-renderet HTML.
# Vi tjekker derfor for den danske lukket-tekst direkte i HTML'en.
URL = "https://app.waitly.dk/signup/3c179506-00d9-4cf7-8840-a2d9cfa6a8bd"
LUKKET_TEKST = "Der er desværre lukket for nye tilmeldinger til denne liste"
STATE_FILE = "state.json"

# Twilio-oplysninger hentes fra GitHub Secrets (miljøvariabler)
TWILIO_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN = os.environ["PRIMARY_AUTH_TOKEN"]
TWILIO_FROM = os.environ["TWILIO_FROM_NUMBER"]
TWILIO_TO = os.environ["TWILIO_TO_NUMBER"]


def hent_status():
    """Henter aktuel status for ventelisten ved at tjekke HTML-indholdet.

    Siden har ingen JSON-API, så vi tjekker om lukket-teksten
    stadig findes på siden. Er den der IKKE længere, er listen sandsynligvis åben.
    """
    headers = {
        # Nogle sider blokerer requests uden en almindelig browser User-Agent
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()
    html = response.text

    er_lukket = LUKKET_TEKST in html
    return not er_lukket  # True = åben, False = lukket


def hent_forrige_status():
    """Læser sidst kendte status fra state.json, hvis den findes."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("er_aaben")
    return None


def gem_status(er_aaben):
    with open(STATE_FILE, "w") as f:
        json.dump({"er_aaben": er_aaben}, f)


def send_sms(besked):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(body=besked, from_=TWILIO_FROM, to=TWILIO_TO)
    print("SMS sendt:", besked)


def main():
    try:
        nu_aaben = hent_status()
    except Exception as e:
        print("Fejl under API-kald:", e)
        sys.exit(0)  # fejler stille, prøver igen om 10 min

    forrige = hent_forrige_status()

    print(f"Forrige status: {forrige} | Nuværende status: {nu_aaben}")

    if forrige is None:
        # Første kørsel — bare gem status, send ikke sms endnu
        print("Første kørsel — gemmer status uden at sende besked.")
    elif nu_aaben != forrige:
        if nu_aaben:
            send_sms(f"🚨 Ventelisten på Gasværksvej 12 er nu ÅBEN! {URL}")
        else:
            send_sms("Ventelisten er nu lukket igen.")
    else:
        print("Ingen ændring.")

    gem_status(nu_aaben)


if __name__ == "__main__":
    main()
