from logger import setup_logger
import requests
import socket
import os

logger = setup_logger()

def user_analyzer(visitor_ip, user_agent, ipinfo_token):
    IPINFO_TOKEN = ipinfo_token
    known_bots = ["googlebot", "bingbot", "baiduspider", "yandex", "duckduckbot", "facebook", "microsoft"]
    bot_detected = False

    hostname = None
    org = "Organizzazione sconosciuta"
    country = "Paese sconosciuto"
    city = "Città sconosciuta"

    if any(bot in user_agent.lower() for bot in known_bots):
        bot_detected = True

    try:
        hostname = socket.gethostbyaddr(visitor_ip)[0]
    except Exception:
        hostname = "Hostname non risolto"

    try:
        response = requests.get(f"https://ipinfo.io/{visitor_ip}/json", headers={"Authorization": f"Bearer {IPINFO_TOKEN}"})
        response.raise_for_status()
        ip_data = response.json()

        org = ip_data.get("org", org)
        country = ip_data.get("country", country)
        city = ip_data.get("city", city)

        if any(bot in org.lower() for bot in known_bots):
            bot_detected = True

    except requests.RequestException as e:
        logger.error(f"Errore durante la chiamata a IPInfo per {visitor_ip}: {e}")


    return bot_detected, {
        "hostname": hostname,
        "org": org,
        "country": country,
        "city": city
    }
