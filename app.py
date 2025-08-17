
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
import json

app = Flask(__name__)

# Lista dei campi
courts = ["Campo 1", "Campo 2"]

# Orari di apertura
open_time = "08:00:00"
close_time = "22:00:00"

# Durate consentite in minuti
durations = [60, 90, 120]

DB_FILE = "bookings.db"

# --- FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            court TEXT NOT NULL,
            user TEXT NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_bookings():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT court, user, start, end FROM bookings")
    rows = cur.fetchall()
    conn.close()
    bookings = []
    for r in rows:
        bookings.append({
            "court": r[0],
            "user": r[1],
            "start": r[2],
            "end": r[3]
        })
    return bookings

def add_booking(court, user, start, end):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO bookings (court, user, start, end) VALUES (?, ?, ?, ?)", 
                (court, user, start, end))
    conn.commit()
    conn.close()

# Inizializza DB alla partenza
init_db()

@app.route("/")
def index():
    bookings = get_bookings()
    bookings_json = json.dumps(bookings)
    return render_template(
        "index.html",
        courts=courts,
        open_time=open_time,
        close_time=close_time,
        durations=durations,
        bookings_json=bookings_json
    )

@app.route("/book", methods=["POST"])
def book():
    data = request.get_json()
    court = data["court"]
    user = data["user"].strip()
    start_str = data["start"]
    duration = int(data["duration"])

    if not user:
        return jsonify({"status": "error", "message": "Inserisci il nome del giocatore"}), 400

    # parsing data e calcolo fine
    start = datetime.fromisoformat(start_str)
    end = start + timedelta(minutes=duration)

    # verifica sovrapposizione prenotazioni
    bookings = get_bookings()
    for b in bookings:
        if b["court"] == court:
            existing_start = datetime.fromisoformat(b["start"])
            existing_end = datetime.fromisoformat(b["end"])
            if start < existing_end and end > existing_start:
                return jsonify({"status": "error", "message": "Slot già prenotato"}), 409

    # aggiungi nuova prenotazione
    add_booking(court, user, start.isoformat(), end.isoformat())

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
