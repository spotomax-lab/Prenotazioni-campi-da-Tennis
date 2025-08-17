
import os
import sqlite3
from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, url_for, abort
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo(os.getenv("APP_TZ", "Europe/Rome"))
OPEN_TIME = time.fromisoformat(os.getenv("OPEN_TIME", "08:00"))
CLOSE_TIME = time.fromisoformat(os.getenv("CLOSE_TIME", "22:00"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
COURTS = os.getenv("COURTS", "Campo 1,Campo 2").split(",")

DB_PATH = os.getenv("DB_PATH", "booking.db")

ALLOWED_DURATIONS = [60, 90, 120]  # minutes
SLOT_STEP_MINUTES = 30  # start times step

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        court TEXT NOT NULL,
        start_utc TEXT NOT NULL,
        end_utc TEXT NOT NULL,
        name TEXT NOT NULL,
        contact TEXT,
        note TEXT,
        cancel_code TEXT NOT NULL
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_court_start ON bookings(court, start_utc);")
    conn.commit()
    conn.close()

def to_utc(dt_local):
    return (dt_local.replace(tzinfo=APP_TZ)).astimezone(ZoneInfo("UTC"))

def to_local(dt_utc):
    return (dt_utc.replace(tzinfo=ZoneInfo("UTC"))).astimezone(APP_TZ)

def times_for_day(day_local):
    # generate possible start times at SLOT_STEP_MINUTES between OPEN_TIME and CLOSE_TIME - min(ALLOWED_DURATIONS)
    start_dt = datetime.combine(day_local, OPEN_TIME, APP_TZ)
    last_start = datetime.combine(day_local, CLOSE_TIME, APP_TZ) - timedelta(minutes=min(ALLOWED_DURATIONS))
    slots = []
    cur = start_dt
    while cur <= last_start:
        slots.append(cur)
        cur += timedelta(minutes=SLOT_STEP_MINUTES)
    return slots

def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

@app.get("/")
def index():
    return render_template("index.html", courts=COURTS, durations=ALLOWED_DURATIONS, open_time=str(OPEN_TIME), close_time=str(CLOSE_TIME))

@app.get("/admin")
def admin_page():
    return render_template("admin.html")

@app.post("/admin/login")
def admin_login():
    data = request.get_json(force=True)
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.get("/api/slots")
def api_slots():
    date_str = request.args.get("date")
    try:
        day_local = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    slots_local = times_for_day(day_local)
    # fetch bookings for this day
    day_start_utc = to_utc(datetime.combine(day_local, time(0,0)))
    day_end_utc = to_utc(datetime.combine(day_local + timedelta(days=1), time(0,0)))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE start_utc >= ? AND start_utc < ?", (day_start_utc.isoformat(), day_end_utc.isoformat()))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # Build response
    bookings = []
    for r in rows:
        start_local = to_local(datetime.fromisoformat(r["start_utc"]))
        end_local = to_local(datetime.fromisoformat(r["end_utc"]))
        bookings.append({
            "id": r["id"],
            "court": r["court"],
            "start": start_local.isoformat(),
            "end": end_local.isoformat(),
            "name": r["name"],
            "note": r.get("note") if isinstance(r, dict) else None,
        })

    times_str = [dt.isoformat() for dt in slots_local]
    return jsonify({
        "courts": COURTS,
        "allowed_durations": ALLOWED_DURATIONS,
        "times": times_str,
        "bookings": bookings
    })

@app.post("/api/book")
def api_book():
    data = request.get_json(force=True)
    court = data.get("court")
    start_iso = data.get("start")
    duration = int(data.get("duration", 0))
    name = data.get("name", "").strip()
    contact = data.get("contact", "").strip()
    note = data.get("note", "").strip()

    if court not in COURTS:
        return jsonify({"error": "Campo non valido."}), 400
    if duration not in ALLOWED_DURATIONS:
        return jsonify({"error": "Durata non consentita."}), 400
    try:
        start_local = datetime.fromisoformat(start_iso).astimezone(APP_TZ)
    except Exception:
        return jsonify({"error": "Formato data/ora non valido."}), 400
    # align to step
    if start_local.minute % 30 != 0:
        return jsonify({"error": "L'orario deve iniziare a :00 o :30."}), 400
    # within opening hours
    if not (time(OPEN_TIME.hour, OPEN_TIME.minute) <= start_local.time() <= time(CLOSE_TIME.hour, CLOSE_TIME.minute)):
        return jsonify({"error": "Orario fuori dall'orario di apertura."}), 400

    end_local = start_local + timedelta(minutes=duration)
    # conflict check
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT start_utc, end_utc FROM bookings WHERE court = ?", (court,))
    existing = cur.fetchall()
    start_utc = to_utc(start_local)
    end_utc = to_utc(end_local)
    for row in existing:
        s = datetime.fromisoformat(row["start_utc"]).replace(tzinfo=ZoneInfo("UTC"))
        e = datetime.fromisoformat(row["end_utc"]).replace(tzinfo=ZoneInfo("UTC"))
        if overlaps(start_utc, end_utc, s, e):
            return jsonify({"error": "Fascia oraria già occupata."}), 409
    if len(name) < 2:
        return jsonify({"error": "Inserisci un nome valido."}), 400

    # generate cancel code
    import secrets
    cancel_code = secrets.token_hex(3)  # 6 hex chars

    cur.execute("""
    INSERT INTO bookings (court, start_utc, end_utc, name, contact, note, cancel_code)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (court, start_utc.isoformat(), end_utc.isoformat(), name, contact, note, cancel_code))
    conn.commit()
    booking_id = cur.lastrowid
    conn.close()

    return jsonify({"ok": True, "booking_id": booking_id, "cancel_code": cancel_code})

@app.post("/api/cancel")
def api_cancel():
    data = request.get_json(force=True)
    booking_id = data.get("booking_id")
    code = data.get("cancel_code", "")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT cancel_code FROM bookings WHERE id = ?", (booking_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Prenotazione non trovata."}), 404
    if row["cancel_code"] != code:
        return jsonify({"error": "Codice di annullamento non valido."}), 401
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.get("/api/admin/export")
def admin_export():
    if request.args.get("password") != ADMIN_PASSWORD:
        return abort(401)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY start_utc ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.get("/manifest.webmanifest")
def manifest():
    return send_from_directory("static", "manifest.json")

@app.get("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)

