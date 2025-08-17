from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Lista globale delle prenotazioni (in memoria)
bookings = []

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint per ottenere tutte le prenotazioni
@app.route('/get_bookings')
def get_bookings():
    return jsonify(bookings)

# Endpoint per aggiungere una nuova prenotazione
@app.route('/add_booking', methods=['POST'])
def add_booking():
    data = request.get_json()
    player = data.get('player')
    court = data.get('court')
    start_str = data.get('start')  # ISO format
    end_str = data.get('end')      # ISO format

    # Conversione in datetime
    start_dt = datetime.fromisoformat(start_str)
    end_dt = datetime.fromisoformat(end_str)

    # Salva prenotazione
    booking = {
        'title': player,
        'start': start_dt.isoformat(),
        'end': end_dt.isoformat(),
        'court': court
    }
    bookings.append(booking)
    return jsonify({"status": "success"})
    
if __name__ == '__main__':
    app.run(debug=True)
