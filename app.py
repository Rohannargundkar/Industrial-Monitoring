from flask import Flask, jsonify, render_template, request

import csv
import os
import threading
import time
from collections import deque

import config
from processor import VibrationProcessor


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# PROCESSOR
# ============================================================

processor = VibrationProcessor(
    sample_rate=config.ESP32_SAMPLE_RATE_HZ
)


# ============================================================
# DATA LOCK
# ============================================================

data_lock = threading.Lock()


# ============================================================
# SYSTEM STATE
# ============================================================

latest_data = {}

last_sample_time = 0.0

total_energy_Wh = 0.0

last_energy_time = time.time()

last_condition = None

events = []


# ============================================================
# VIBRATION BUFFERS
# ============================================================

WINDOW_SIZE = config.VIBRATION_WINDOW_SIZE

x_buffer = deque(maxlen=WINDOW_SIZE)

y_buffer = deque(maxlen=WINDOW_SIZE)

z_buffer = deque(maxlen=WINDOW_SIZE)


# ============================================================
# CSV
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CSV_FILE = os.path.join(
    BASE_DIR,
    config.CSV_FILE
)

CSV_HEADER = [
    "date",
    "time",
    "x",
    "y",
    "z",
    "voltage",
    "current",
    "power",
    "rms",
    "peak",
    "frequency",
    "condition",
    "energy_Wh"
]


# ============================================================
# INITIALIZE CSV
# ============================================================

def initialize_csv():

    os.makedirs(
        os.path.dirname(CSV_FILE),
        exist_ok=True
    )

    if not os.path.exists(CSV_FILE):

        with open(
            CSV_FILE,
            "w",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow(CSV_HEADER)

        print("CSV created:")
        print(CSV_FILE)

    else:

        print("CSV found:")
        print(CSV_FILE)


# ============================================================
# SAVE DATA
# ============================================================

def save_data(data):

    with open(
        CSV_FILE,
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            data["date"],
            data["time"],
            data["x"],
            data["y"],
            data["z"],
            data["voltage"],
            data["current"],
            data["power"],
            data["rms"],
            data["peak"],
            data["frequency"],
            data["condition"],
            data["energy_Wh"]
        ])


# ============================================================
# CLEAN ELECTRICAL DATA
# ============================================================

def clean_electrical_data(
    voltage,
    current,
    power
):

    # INA219 can show a tiny negative
    # current when no load is connected.
    #
    # Treat very small values as zero.

    if abs(current) < 1.0:

        current = 0.0

    if abs(power) < 0.01:

        power = 0.0

    if voltage < 0:

        voltage = 0.0

    return (
        voltage,
        current,
        power
    )


# ============================================================
# ENERGY
# ============================================================

def update_energy(power):

    global total_energy_Wh

    global last_energy_time

    current_time = time.time()

    elapsed_seconds = (
        current_time
        - last_energy_time
    )

    if elapsed_seconds < 0:

        elapsed_seconds = 0

    # Power is in watts.
    # Energy = power × time.
    #
    # Convert seconds to hours.

    energy_increment = (
        power
        * elapsed_seconds
        / 3600.0
    )

    total_energy_Wh += energy_increment

    last_energy_time = current_time

    return total_energy_Wh


# ============================================================
# EVENTS
# ============================================================

def add_event(
    condition,
    event_time
):

    global last_condition

    if condition == last_condition:

        return

    if condition == "NORMAL":

        message = (
            "Machine condition returned to NORMAL"
        )

    elif condition == "WARNING":

        message = (
            "WARNING: Abnormal vibration detected"
        )

    else:

        message = (
            "DANGER: High vibration detected"
        )

    events.append({
        "time": event_time,
        "condition": condition,
        "message": message
    })

    if len(events) > 20:

        events.pop(0)

    last_condition = condition


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# ============================================================
# LATEST DATA API
# ============================================================

@app.route("/api/data")
def api_data():

    with data_lock:

        return jsonify(
            latest_data
        )


# ============================================================
# SYSTEM STATUS API
# ============================================================

@app.route("/api/status")
def api_status():

    current_time = time.time()

    esp32_connected = (
        last_sample_time > 0
        and
        (
            current_time
            - last_sample_time
        )
        <= config.ESP32_TIMEOUT_SECONDS
    )

    with data_lock:

        data = dict(latest_data)

    rtc_status = "NOT AVAILABLE"

    if data:

        date_value = str(
            data.get("date", "")
        )

        time_value = str(
            data.get("time", "")
        )

        # DS3231 should provide a normal
        # YYYY-MM-DD date.

        if (
            len(date_value) == 10
            and len(time_value) >= 8
            and date_value[:4].isdigit()
            and date_value[4] == "-"
        ):

            rtc_status = "CONNECTED"

    return jsonify({

        "simulation": False,

        "esp32": (
            "USB CONNECTED"
            if esp32_connected
            else
            "USB DISCONNECTED"
        ),

        "wifi": "NOT USED",

        "rtc": rtc_status,

        "sd": "NOT CONNECTED",

        "server": "ONLINE"

    })


# ============================================================
# EVENTS API
# ============================================================

@app.route("/api/events")
def api_events():

    with data_lock:

        return jsonify(
            list(events)
        )


# ============================================================
# HISTORY API
# ============================================================

@app.route("/api/history")
def api_history():

    try:

        if not os.path.exists(CSV_FILE):

            return jsonify([])

        with open(
            CSV_FILE,
            "r",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            rows = list(reader)

        # Return latest 100 records.

        rows = rows[-100:]

        return jsonify(rows)

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# ESP32 DATA API
# ============================================================

@app.route(
    "/api/esp32",
    methods=["POST"]
)
def receive_esp32_data():

    global latest_data

    global last_sample_time


    # ========================================================
    # GET JSON
    # ========================================================

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "status": "error",
            "message": "No JSON data received"
        }), 400


    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required_fields = [

        "date",
        "time",

        "x",
        "y",
        "z",

        "voltage",
        "current",
        "power"

    ]


    for field in required_fields:

        if field not in data:

            return jsonify({

                "status": "error",

                "message":
                    f"Missing field: {field}"

            }), 400


    # ========================================================
    # CONVERT SENSOR VALUES
    # ========================================================

    try:

        x = float(data["x"])

        y = float(data["y"])

        z = float(data["z"])

        voltage = float(
            data["voltage"]
        )

        current = float(
            data["current"]
        )

        power = float(
            data["power"]
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "status": "error",

            "message":
                "Invalid numeric sensor value"

        }), 400


    # ========================================================
    # CLEAN ELECTRICAL DATA
    # ========================================================

    (
        voltage,
        current,
        power
    ) = clean_electrical_data(
        voltage,
        current,
        power
    )


    # ========================================================
    # UPDATE SAMPLE TIME
    # ========================================================

    last_sample_time = time.time()


    # ========================================================
    # ADD VIBRATION SAMPLE
    # ========================================================

    x_buffer.append(x)

    y_buffer.append(y)

    z_buffer.append(z)


    # ========================================================
    # WAIT FOR COMPLETE WINDOW
    # ========================================================

    if len(x_buffer) < WINDOW_SIZE:

        return jsonify({

            "status": "buffering",

            "samples":
                len(x_buffer),

            "required":
                WINDOW_SIZE

        })


    # ========================================================
    # REAL VIBRATION PROCESSING
    # ========================================================

    result = processor.process(

        list(x_buffer),

        list(y_buffer),

        list(z_buffer)

    )


    # ========================================================
    # PROCESSING RESULTS
    # ========================================================

    rms = result["rms"]

    peak = result["peak"]

    frequency = (
        result["dominant_frequency"]
    )

    condition = result["condition"]


    # ========================================================
    # ENERGY
    # ========================================================

    energy = update_energy(
        power
    )


    # ========================================================
    # EVENT
    # ========================================================

    add_event(

        condition,

        data["time"]

    )


    # ========================================================
    # BUILD FINAL DATA
    # ========================================================

    processed_data = {

        "date":
            str(data["date"]),

        "time":
            str(data["time"]),

        "x":
            round(x, 3),

        "y":
            round(y, 3),

        "z":
            round(z, 3),

        "voltage":
            round(voltage, 3),

        "current":
            round(current, 3),

        "power":
            round(power, 3),

        "rms":
            round(
                float(rms),
                4
            ),

        "peak":
            round(
                float(peak),
                4
            ),

        "frequency":
            round(
                float(frequency),
                2
            ),

        "condition":
            condition,

        "energy_Wh":
            round(
                energy,
                6
            )
    }


    # ========================================================
    # SAVE CSV
    # ========================================================

    save_data(
        processed_data
    )


    # ========================================================
    # UPDATE LATEST DATA
    # ========================================================

    with data_lock:

        latest_data = (
            processed_data.copy()
        )


    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    print(

        "ESP32 DATA:",

        processed_data["date"],

        processed_data["time"],

        "| X:",
        processed_data["x"],

        "| Y:",
        processed_data["y"],

        "| Z:",
        processed_data["z"],

        "| V:",
        processed_data["voltage"],

        "| I:",
        processed_data["current"],

        "| P:",
        processed_data["power"],

        "| RMS:",
        processed_data["rms"],

        "| Peak:",
        processed_data["peak"],

        "| F:",
        processed_data["frequency"],

        "| Condition:",
        processed_data["condition"]

    )


    return jsonify({

        "status": "received",

        "condition":
            condition,

        "samples":
            WINDOW_SIZE

    })


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        " INDUSTRIAL MONITORING SYSTEM"
    )

    print(
        " REAL ESP32 USB MODE"
    )

    print("=" * 60)

    print()

    initialize_csv()

    print()

    print("Sample rate:",
          config.ESP32_SAMPLE_RATE_HZ,
          "Hz")

    print(
        "Processing window:",
        config.VIBRATION_WINDOW_SIZE,
        "samples"
    )

    print()

    print("Dashboard:")

    print(
        "http://127.0.0.1:5000"
    )

    print()

    print(
        "Simulation: DISABLED"
    )

    print(
        "ESP32 source: USB SERIAL"
    )

    print()

    app.run(

        host=config.SERVER_HOST,

        port=config.SERVER_PORT,

        debug=False

    )