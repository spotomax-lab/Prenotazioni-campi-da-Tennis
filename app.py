
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Lista dei campi
courts = ["Campo 1", "Campo 2"]

# Orari di apertura
open_time = "08:00:00"
close_time = "22:00:00"

# Durate consentite in minuti
durations = [60, 90, 120]

# Prenotazioni: dizionario {campo: [orari prenotati]}
bookings = {}

# Route principale
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

# Route per prenotare uno slot
@app.route("/book", methods=["POST"])
def book():
    data = request.get_json()
    court = data["court"]
    start = data["start"]
    duration = int(data["duration"])

    # inizializza la lista se non esiste
    if court not in bookings:
        bookings[court] = []

    # verifica se lo slot è già prenotato
    if start in bookings[court]:
        return jsonify({"status": "error", "message": "Slot già prenotato"}), 409

    bookings[court].append(start)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
