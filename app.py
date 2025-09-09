#!/usr/bin/env python3
import json
import random
import time
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "weather.readings"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=5
)

# sample station ids
STATIONS = ["STATION001", "STATION002", "STATION_A", "STATION-XYZ", "STN99"]

def random_temp():
    # some sensors report Celsius, some Fahrenheit, and some with degree symbol or extra spaces
    c = random.uniform(-30, 45)
    if random.random() < 0.2:
        # return Fahrenheit occasionally
        f = c * 9/5 + 32
        formats = [f"{f:.1f} F", f"{f:.0f}F", f"{f:.1f} °F"]
        return random.choice(formats)
    else:
        formats = [f"{c:.1f} C", f"{c:.0f}C", f"{c:.1f}°C", f"{c:.1f} C "]
        return random.choice(formats)

def random_wind():
    kmh = random.uniform(0, 120)
    if random.random() < 0.15:
        # mph occasionally
        mph = kmh / 1.60934
        return f"{mph:.1f} mph"
    else:
        return random.choice([f"{kmh:.0f} km/h", f"{kmh:.1f}km/h", f"{kmh:.1f} km/h"])

def random_precip():
    mmh = random.uniform(0, 60)
    if random.random() < 0.1:
        # inch/hour
        inh = mmh / 25.4
        return f"{inh:.2f} in/h"
    else:
        return random.choice([f"{mmh:.1f} mm/h", f"{mmh:.0f}mm/h"])

def random_humidity():
    h = random.uniform(10, 100)
    return random.choice([f"{h:.0f} %", f"{h:.1f}%", f"{h:.0f}%"])

def random_pressure():
    p = random.uniform(950, 1050)
    return f"{p:.0f} hPa"

def gen_message():
    # occasionally set some fields to None or empty to simulate missing values
    temperature = random_temp() if random.random() > 0.05 else None
    wind_speed = random_wind() if random.random() > 0.05 else None
    precipitation = random_precip() if random.random() > 0.1 else None
    humidity = random_humidity() if random.random() > 0.05 else None
    pressure = random_pressure() if random.random() > 0.1 else None

    msg = {
        "station_id": random.choice(STATIONS),
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "precipitation": precipitation,
        "pressure": pressure,
        # ISO timestamp, sometimes with space separator or without timezone
        "reading_timestamp": random.choice([
            datetime.now(timezone.utc).isoformat(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.utcnow().isoformat()[:-3]
        ]),
        "location": random.choice(["New York, USA", "Mumbai, India", "Bengaluru", "London, UK", None])
    }
    return msg

def main():
    print(f"Starting producer to topic {TOPIC} -> bootstrap: {BOOTSTRAP_SERVERS}")
    try:
        while True:
            msg = gen_message()
            # create a key for partitioning based on station_id
            key = (msg["station_id"] or str(uuid.uuid4())).encode("utf-8")
            producer.send(TOPIC, value=msg, key=key)
            # flush occasionally
            if random.random() < 0.05:
                producer.flush()
            print(f"Produced: {json.dumps(msg)}")
            time.sleep(random.uniform(0.4, 1.5))
    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()
