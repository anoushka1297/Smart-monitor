# Smart Monitor- Edge-to-Cloud IoT Monitoring System

A distributed sensing system that collects real-world environmental data from an ESP32, sends it over WiFi to a Python/Flask backend, persists it to a database, detects anomalies, and sends AI-generated natural language alerts to Telegram.

Built as a learning project to understand the full stack of an IoT pipeline-from microcontroller firmware and wireless networking, through backend API design and data storage, to LLM-based alerting.

---

## Architecture

```
[ DHT22 + PIR Sensors ]
        │
        ▼
[ ESP32 (C++/Arduino framework) ]
        │  WiFi->HTTP POST (JSON)
        ▼
[ Flask Server ]
        │
        ├──► [ SQLite Database ] — stores every reading
        │
        └──► [ Anomaly Detection ] — rule-based checks on recent readings
                    │
                    ▼ (if anomaly detected)
            [ Gemini API ]— generates a natural-language alert
                    │
                    ▼
            [ Telegram Bot ]— sends alert to chatbot on phone
```

---

## Features

- **Real-time sensor ingestion**- ESP32 reads temperature, humidity, and motion every 30 seconds and POSTs them as JSON to the backend
- **Persistent storage** — all readings logged to SQLite with timestamps
- **Rule-based anomaly detection**:
  - **Thermal runaway/fire** — detects rapid temperature rise over a smoothed 3-minute window, with an absolute high-temperature cutoff
  - **Humidity /mould risk** — flags sustained high humidity (greater than 80% averaged over 1 hour) combined with an effectively empty room (low motion count, with tolerance for sensor false positives)
- **LLM-generated alerts** — when an anomaly is detected, recent readings and the anomaly type are sent to the Gemini API, which drafts a short, human-readable alert message
- **Telegram notifications** — the generated alert is pushed directly to a Telegram chat

---

## Hardware

- ESP32 (WROOM-32 dev board)
- DHT22 temperature & humidity sensor
- HC-SR501 PIR motion sensor
- Breadboard + jumper wires
- 10kΩ pull-up resistor (for DHT22 data line)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Firmware | C++ (Arduino framework for ESP32) |
| Networking | WiFi (802.11), HTTP |
| Backend | Python, Flask |
| Database | SQLite |
| Alert generation | Google Gemini API |
| Notifications | Telegram Bot API |

---

## How It Works

1. The ESP32 connects to WiFi and reads temperature, humidity, and motion every 30 seconds.
2. It serializes the readings into a JSON payload and sends it via HTTP POST to `/data` on the Flask server.
3. The server parses the JSON, runs `analyse_readings()` against recent history from the database, and stores the new reading.
4. If `analyse_readings()` flags an anomaly, the server calls the Gemini API with the anomaly type and current readings to generate a short alert message.
5. The generated message is sent to a Telegram chat via the Telegram Bot API.
6. Stored readings can be retrieved via `GET /readings`.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/data` | Receives a sensor reading as JSON, stores it, and triggers anomaly detection |
| `GET` | `/readings` | Returns the most recent 20 stored readings |

### Example payload (`POST /data`)

```json
{
  "device_id": "room_1",
  "temperature": 28.1,
  "humidity": 72,
  "motion": 1,
  "timestamp": 1716710400
}
```

---

## Setup

### Backend

```bash
git clone <repo-url>
cd smart-monitor
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_key
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Run the server:

```bash
python server.py
```

The server listens on `0.0.0.0:5000`.

### Firmware

1. Open `esp32_code.ino` in the Arduino IDE
2. Install the ESP32 board package and the following libraries: `DHT sensor library` (Adafruit), `Adafruit Unified Sensor`, `ArduinoJson`
3. Before uploading the code, fill in your credentials at the top of the file:
 ```cpp
#define WIFI_SSID "your_wifi_name"
#define WIFI_PASSWORD "your_wifi_password"
#define SERVER_URL "http://server-ip:5000/data"
```
The server-ip can be obtained by running:
```bash
# Mac/Linux
ifconfig | grep "inet "

# Windows
ipconfig
```

4. Wire the DHT22 and PIR sensors to the ESP32 (see wiring diagram below)
5. Flash to the ESP32 and open the Serial Monitor to confirm WiFi connection and successful POST responses

### Wiring 

### Schematic layout
<img width="897" height="730" alt="Screenshot 2026-06-22 at 5 29 16 AM" src="https://github.com/user-attachments/assets/518af266-18ef-438f-8306-b177316e0411" />

### Physical breaboard layout
<img width="1600" height="1200" alt="WhatsApp Image 2026-06-22 at 04 48 24" src="https://github.com/user-attachments/assets/bf37cc45-0221-46bf-96bd-9928376a4364" />

---
## Images

### Serial Monitor
<img width="861" height="813" alt="Screenshot 2026-06-19 at 6 17 07 PM" src="https://github.com/user-attachments/assets/dba111d9-2aa7-4217-b250-a08138bb27af" />

### Database Entries
<img width="1149" height="314" alt="Screenshot 2026-06-19 at 6 20 30 PM" src="https://github.com/user-attachments/assets/e88c2bc4-c2e7-4759-a8e1-4d9c99da3276" />

### Backend Server Logs
<img width="1390" height="306" alt="Screenshot 2026-06-19 at 6 16 56 PM" src="https://github.com/user-attachments/assets/0266fa58-628f-4b38-afe1-cc2c683e2f27" />

### Telegram Alerts 

<img width="786" height="755" alt="Screenshot 2026-08-05 at 11 18 39 PM" src="https://github.com/user-attachments/assets/65a6f38d-79d3-4575-bc4b-ac50c3d0b7e5" />

---

## Anomaly Detection Logic

The system keeps a rolling window of past readings and checks two conditions on every new reading:

**Fire / thermal runaway**
- Compares a smoothed average of the two most recent readings against a smoothed average of readings from approx. 3 minutes earlier
- Triggers if the rise is greater than or equal to 4°C, or if the current reading exceeds an absolute high-temperature cutoff
- Smoothing (averaging adjacent readings rather than comparing single points) prevents a single noisy sensor reading from causing a false alarm

**Humidity / mould risk**
- Averages humidity over the last hour of readings
- Triggers if the average is ≥80% **and** the room has been effectively empty (total motion events over the hour below a small tolerance threshold, to account for PIR false positives)

---

## What I Learned

This project was primarily an exercise in understanding how each layer of a networked embedded system fits together: from radio-level WiFi and the TCP/IP stack, through HTTP and Flask's request/response model, to sensor communication protocols (DHT22's single-wire timing-based protocol vs PIR's simple digital output), database design, rule-based anomaly detection with noise tolerance, and integrating third-party APIs (Gemini, Telegram). 

The LLM integration (anomaly classification via Gemini API) was not strictly necessary for this project— since only two anomaly types exist (thermal runaway/fire risk and humidity/mould risk), a simple if/else condition would have sufficed. It was included for learning purposes, to explore how language models can be embedded into IoT pipelines for natural language reasoning over sensor data.


