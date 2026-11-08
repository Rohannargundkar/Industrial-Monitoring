#include <Wire.h>

#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <Adafruit_INA219.h>
#include <RTClib.h>


// ============================================================
// SENSOR OBJECTS
// ============================================================

Adafruit_ADXL345_Unified accel =
    Adafruit_ADXL345_Unified(12345);

Adafruit_INA219 ina219;

RTC_DS3231 rtc;


// ============================================================
// SAMPLING
// ============================================================

unsigned long lastSample = 0;

const unsigned long SAMPLE_INTERVAL = 10;   // 10 ms = 100 Hz


// ============================================================
// SETUP
// ============================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    // ESP32 I2C
    Wire.begin(21, 22);


    // ========================================================
    // ADXL345
    // ========================================================

    if (!accel.begin())
    {
        Serial.println("ERROR,ADXL345");
        while (1);
    }

    accel.setRange(ADXL345_RANGE_4_G);

    accel.setDataRate(
        ADXL345_DATARATE_100_HZ
    );


    // ========================================================
    // INA219
    // ========================================================

    if (!ina219.begin())
    {
        Serial.println("ERROR,INA219");
        while (1);
    }


    // ========================================================
    // DS3231
    // ========================================================

    if (!rtc.begin())
    {
        Serial.println("ERROR,DS3231");
        while (1);
    }


    // --------------------------------------------------------
    // RTC WARNING
    // --------------------------------------------------------

    if (rtc.lostPower())
    {
        Serial.println(
            "WARNING,RTC_CLOCK_LOST_POWER"
        );
    }


    // ========================================================
    // CSV HEADER
    // ========================================================

    Serial.println(
        "date,time,x,y,z,voltage,current,power"
    );


    Serial.println(
        "ESP32_READY"
    );
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
    unsigned long currentMillis = millis();


    if (currentMillis - lastSample >= SAMPLE_INTERVAL)
    {
        lastSample += SAMPLE_INTERVAL;

        readSensors();
    }
}


// ============================================================
// READ ALL SENSORS
// ============================================================

void readSensors()
{
    // ========================================================
    // ADXL345
    // ========================================================

    sensors_event_t event;

    accel.getEvent(&event);

    float x = event.acceleration.x;
    float y = event.acceleration.y;
    float z = event.acceleration.z;


    // ========================================================
    // INA219
    // ========================================================

    float voltage =
        ina219.getBusVoltage_V();

    float current =
        ina219.getCurrent_mA();

    float power =
        ina219.getPower_mW() / 1000.0;


    // ========================================================
    // DS3231
    // ========================================================

    DateTime now = rtc.now();


    // ========================================================
    // DATE
    // ========================================================

    Serial.print(now.year());
    Serial.print("-");

    if (now.month() < 10)
        Serial.print("0");

    Serial.print(now.month());
    Serial.print("-");

    if (now.day() < 10)
        Serial.print("0");

    Serial.print(now.day());

    Serial.print(",");


    // ========================================================
    // TIME
    // ========================================================

    if (now.hour() < 10)
        Serial.print("0");

    Serial.print(now.hour());

    Serial.print(":");

    if (now.minute() < 10)
        Serial.print("0");

    Serial.print(now.minute());

    Serial.print(":");

    if (now.second() < 10)
        Serial.print("0");

    Serial.print(now.second());

    Serial.print(",");


    // ========================================================
    // ACCELERATION
    // ========================================================

    Serial.print(x, 3);
    Serial.print(",");

    Serial.print(y, 3);
    Serial.print(",");

    Serial.print(z, 3);
    Serial.print(",");


    // ========================================================
    // ELECTRICAL
    // ========================================================

    Serial.print(voltage, 3);
    Serial.print(",");

    Serial.print(current, 3);
    Serial.print(",");

    Serial.println(power, 3);
}

/*

RTC_DS3231 rtc;

void setup()
{
    Serial.begin(115200);
    delay(1000);

    Wire.begin(21, 22);

    if (!rtc.begin())
    {
        Serial.println("ERROR,DS3231");
        while (1);
    }

    // ONE-TIME RTC SET
    rtc.adjust(DateTime(2026, 10, 6, 17, 6 , 0));

    Serial.println("RTC TIME SET");

    DateTime now = rtc.now();

    Serial.print("RTC: ");
    Serial.print(now.year());
    Serial.print("-");
    Serial.print(now.month());
    Serial.print("-");
    Serial.print(now.day());
    Serial.print(" ");

    Serial.print(now.hour());
    Serial.print(":");

    if (now.minute() < 10)
        Serial.print("0");

    Serial.print(now.minute());
    Serial.print(":");

    if (now.second() < 10)
        Serial.print("0");

    Serial.println(now.second());
}

void loop()
{
}
*/