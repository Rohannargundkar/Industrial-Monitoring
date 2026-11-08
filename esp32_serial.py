import serial
import requests
import time


# ============================================================
# CONFIGURATION
# ============================================================

PORT = "COM5"

BAUD_RATE = 115200

FLASK_URL = "http://127.0.0.1:5000/api/esp32"


# ============================================================
# START
# ============================================================

print("=" * 60)
print(" INDUSTRIAL MONITORING SYSTEM")
print(" ESP32 -> FLASK SERIAL BRIDGE")
print("=" * 60)

print()


# ============================================================
# SERIAL CONNECTION
# ============================================================

try:

    ser = serial.Serial(
        PORT,
        BAUD_RATE,
        timeout=1
    )

except Exception as error:

    print("Could not connect to ESP32.")
    print()
    print(error)

    input("\nPress ENTER to exit...")
    raise SystemExit


print("ESP32 connected on", PORT)

time.sleep(2)

print("Waiting for ESP32 data...")
print()


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        line = (
            ser.readline()
            .decode(
                "utf-8",
                errors="ignore"
            )
            .strip()
        )


        if not line:
            continue


        # ----------------------------------------------------
        # Ignore CSV header
        # ----------------------------------------------------

        if line.startswith("date,time"):

            continue


        # ----------------------------------------------------
        # ESP32 startup message
        # ----------------------------------------------------

        if line == "ESP32_READY":

            print("ESP32 ready.")

            continue


        # ----------------------------------------------------
        # RTC warning
        # ----------------------------------------------------

        if line.startswith("WARNING"):

            print("ESP32:", line)

            continue


        # ----------------------------------------------------
        # Sensor errors
        # ----------------------------------------------------

        if line.startswith("ERROR"):

            print("ESP32:", line)

            continue


        # ----------------------------------------------------
        # Split CSV
        # ----------------------------------------------------

        values = line.split(",")


        if len(values) != 8:

            continue


        try:

            # ------------------------------------------------
            # RTC
            # ------------------------------------------------

            date_value = values[0]

            time_value = values[1]


            # ------------------------------------------------
            # ADXL345
            # ------------------------------------------------

            x = float(values[2])

            y = float(values[3])

            z = float(values[4])


            # ------------------------------------------------
            # INA219
            # ------------------------------------------------

            voltage = float(values[5])

            current = float(values[6])

            power = float(values[7])


            # ------------------------------------------------
            # BUILD DATA
            # ------------------------------------------------

            data = {

                "date": date_value,

                "time": time_value,

                "x": x,

                "y": y,

                "z": z,

                "voltage": voltage,

                "current": current,

                "power": power
            }


            # ------------------------------------------------
            # SEND TO FLASK
            # ------------------------------------------------

            response = requests.post(

                FLASK_URL,

                json=data,

                timeout=2
            )


            # ------------------------------------------------
            # OUTPUT
            # ------------------------------------------------

            if response.status_code != 200:

                print(
                    "Flask error:",
                    response.status_code
                )

            else:

                print(
                    date_value,
                    time_value,
                    "|",
                    "X:", round(x, 3),
                    "|",
                    "Y:", round(y, 3),
                    "|",
                    "Z:", round(z, 3),
                    "|",
                    "V:", round(voltage, 3),
                    "|",
                    "I:", round(current, 3),
                    "|",
                    "P:", round(power, 3)
                )


        except ValueError:

            print(
                "Invalid ESP32 data:",
                line
            )


except KeyboardInterrupt:

    print()
    print("Serial bridge stopped.")


finally:

    ser.close()