#File to store and retrieve the entries from the server
import sqlite3
from flask import Flask, request, jsonify

app=Flask(__name__)
DB="readings.db"

def init_db():
    conn=sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            temperature REAL,
            humidity REAL,
            motion INTEGER,
            timestamp INTEGER,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

@app.route("/data", methods=["POST"])
def receive_data():
    data= request.get_json()
    conn= sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO readings (device_id, temperature, humidity, motion, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (data["device_id"], data["temperature"], data["humidity"],
          int(data["motion"]), data["timestamp"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 200

@app.route("/readings", methods=["GET"])
def get_readings():
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT * FROM readings ORDER BY received_at DESC LIMIT 20
    """).fetchall()
    conn.close()
    return jsonify(rows), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

