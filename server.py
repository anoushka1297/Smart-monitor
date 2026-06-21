
#File to store and retrieve the entries from the server
import sqlite3
from flask import Flask, request, jsonify
import requests 

import os
from dotenv import load_dotenv
load_dotenv() #to import the api keys, token, chatid

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
init_db()
def analyse_readings(data): #returns true if theres an anomaly (and the type) 
    conn=sqlite3.connect(DB)
    readings=conn.execute("""SELECT temperature, humidity, motion, timestamp 
    FROM readings 
    ORDER BY id DESC 
    LIMIT 150""").fetchall()
    conn.close()
    if len(readings)<6:
        return False, None
    
    baseline_temp = (readings[5][0] + readings[4][0]) / 2

    current_state_temp =(data["temperature"]+ readings[0][0]) /2
    temp_increase = current_state_temp-baseline_temp
    if temp_increase >= 4.0: 
        return True,"fire"

    if len(readings) >= 120:
        past_humidity =[row[1] for row in readings[0:120]]
        past_motion =[row[2] for row in readings[0:120]]

        all_humidity =[data["humidity"]] + past_humidity
        all_motion = [int(data["motion"])]+ past_motion

        avg_humidity_1hr = sum(all_humidity)/len(all_humidity)

        total_motion_events = sum(all_motion)
        is_room_effectively_empty = total_motion_events <= 3

        if avg_humidity_1hr >= 80.0 and is_room_effectively_empty:
            return True, "humidity" 

    return False, None



def get_llm_summary(data, anomaly_type):
    api_key= os.environ.get("Gemini_API_key")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload={
        "contents": [{
            "parts": [{
                "text": (
                    f"Sensor anomaly detected in a room. Type: {anomaly_type}. "
                    f"Current readings: temperature={data['temperature']}C, "
                    f"humidity={data['humidity']}%, motion={data['motion']}. "
                    f"please write a brief 2 sentence alert message."
                    f"(additional context if needed: temp/humidity sensor data and motion PIR sensor data "
                    f"collected from esp32 analysed for anomalies; LLM api triggered if anomaly "
                    f"detected for summarised brief alert to send to telegram)"
		    f"this isnt a random room; this is the user's room. none of the program jargon (motion=0 etc) should be "
	            f"included in response. purely user-friendly only"
                )
            }]
        }]
    }
    
    response= requests.post(url, json=payload)
    result =response.json()
    
    
    if "candidates" in result and result["candidates"]:
        return result["candidates"][0]["content"]["parts"][0]["text"]

def send_telegram(message):
    token=os.environ.get("Telegram_Token")
    chat_id=os.environ.get("Telegram_Chat_ID")
    url=f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

@app.route("/data", methods=["POST"])
def receive_data():
    data= request.get_json()
    anomaly, anomaly_type= analyse_readings(data)
    if anomaly:
        summary= get_llm_summary(data, anomaly_type)
        send_telegram(summary) 
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
    app.run(host="0.0.0.0", port=5000, debug=True)

