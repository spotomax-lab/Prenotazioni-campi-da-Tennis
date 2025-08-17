
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Lista dei campi
courts = ["Campo 1", "Campo 2"]

# Orari di apertura
open_time = "08:00:00"
close_time = "22:00:00"

# Durate consentite in minuti
durations = [60, 90, 120]

# Prenotazioni: lista di dizionari con start e end
bookings = []

@app.route("/")
def index():
    return render_template(
        "index.html",
        courts=courts,
        open_time=open_time,
        close_time=close_time,
        durations=durations,
        bookings=bookings
    )

@app.route("/book", methods=["POST"])
def book():
    data = request.get_json()
    court = data["court"]
    start_str = data["start"]
    duration = int(data["duration"])

    # parsing data e calcolo fine
    start = datetime.fromisoformat(start_str)
    end = start + timedelta(minutes=duration)

    # verifica sovrapposizione prenotazioni
    for b in bookings:
        if b["court"] == court:
            existing_start = datetime.fromisoformat(b["start"])
            existing_end = datetime.fromisoformat(b["end"])
            if start < existing_end and end > existing_start:
                return jsonify({"status": "error", "message": "Slot già prenotato"}), 409

    # aggiungi nuova prenotazione
    bookings.append({
        "court": court,
        "start": start.isoformat(),
        "end": end.isoformat()
    })

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
