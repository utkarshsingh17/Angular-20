#!/usr/bin/env python3
"""
Simple alert consumer tolerant of nulls.

- Reads from weather.readings
- Safely extracts numeric values (handles strings like "287.2 K", "24.2 km/h", "40.3 m/h", or numeric types)
- Converts K -> C, mph -> km/h, m/s -> km/h, m/h -> km/h (simple conversions)
- If temperature, wind, and precipitation are ALL missing -> send to DLQ
- Otherwise evaluate alert rules on available fields and publish alerts to weather.alerts
"""
import json
import time
import uuid
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP_SERVERS = ["localhost:9092"]
READINGS_TOPIC = "weather.readings"
ALERTS_TOPIC = "weather.alerts"
DLQ_TOPIC = "weather.dlq"
GROUP_ID = "weather.alerts.processor"

# thresholds
TH_HIGH_WIND_KMH = 70.0
TH_FLOOD_MMH = 30.0
TH_STORM_WIND_KMH = 50.0
TH_STORM_PRECIP_MMH = 20.0
TH_TEMP_LOW_C = -20.0
TH_TEMP_HIGH_C = 40.0

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=5
)

consumer = KafkaConsumer(
    READINGS_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    consumer_timeout_ms=1000
)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        s = value.strip().lower()
        if s == "" or s in ("null", "none", "n/a", "na"):
            return True
    return False

def extract_number_and_unit(raw):
    """
    Return tuple (number: float or None, unit: str or None)
    Handles strings like "287.2 K", "30 C", "24.2 km/h", numeric types, or None.
    """
    if is_missing(raw):
        return None, None
    # if already numeric
    if isinstance(raw, (int, float)):
        return float(raw), None
    s = str(raw).strip()
    # replace non-breaking space and normalize spaces
    s = s.replace("\u00A0", " ")
    s = " ".join(s.split())
    # find first number
    import re
    m = re.search(r"([-+]?\d+(?:\.\d+)?)", s)
    if not m:
        return None, None
    num = float(m.group(1))
    unit = s[m.end():].strip().lower()
    return num, unit

def temp_to_celsius(raw):
    num, unit = extract_number_and_unit(raw)
    if num is None:
        return None
    # unit may be "k", "c", "f", or empty
    if unit.startswith("k"):
        return num - 273.15
    if unit.startswith("f"):
        return (num - 32.0) * 5.0 / 9.0
    # assume celsius otherwise
    return float(num)

def wind_to_kmh(raw):
    num, unit = extract_number_and_unit(raw)
    if num is None:
        return None
    # common units: "km/h", "kmh", "mph", "m/s", "m/h"
    if unit.startswith("km"):
        return float(num)
    if unit.startswith("mph"):
        return float(num) * 1.60934
    if unit.startswith("m/s"):
        return float(num) * 3.6
    if unit.startswith("m/h"):
        # meters per hour -> km/h (1 m = 0.001 km)
        return float(num) * 0.001
    # default assume km/h
    return float(num)

def precip_to_mmh(raw):
    num, unit = extract_number_and_unit(raw)
    if num is None:
        return None
    if unit.startswith("mm"):
        return float(num)
    if unit.startswith("in"):
        # inches per hour -> mm/h
        return float(num) * 25.4
    # default assume mm/h
    return float(num)

def publish_alert(alert):
    producer.send(ALERTS_TOPIC, value=alert, key=(alert.get("station_id") or "unknown").encode("utf-8"))

def publish_dlq(record, reason):
    payload = {
        "error": reason,
        "failed_at": now_iso(),
        "record": record
    }
    producer.send(DLQ_TOPIC, value=payload, key=(record.get("station_id") if isinstance(record, dict) and record.get("station_id") else "unknown").encode("utf-8"))

def evaluate_and_publish(cleaned):
    t = cleaned.get("temperature_c")
    w = cleaned.get("wind_speed_kmh")
    p = cleaned.get("precipitation_mmh")

    # storm priority
    if (w is not None and p is not None) and (w > TH_STORM_WIND_KMH and p >= TH_STORM_PRECIP_MMH):
        alert = {
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Storm",
            "severity": "critical",
            "value": {"wind_speed_kmh": w, "precipitation_mmh": p},
            "timestamp": now_iso(),
            "raw_reading": cleaned.get("raw")
        }
        publish_alert(alert)
        print(f"[ALERT] Storm station={cleaned.get('station_id')} w={w} p={p}")
        return

    if w is not None and w > TH_HIGH_WIND_KMH:
        alert = {
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "High Wind",
            "severity": "warning",
            "value": {"wind_speed_kmh": w},
            "timestamp": now_iso(),
            "raw_reading": cleaned.get("raw")
        }
        publish_alert(alert)
        print(f"[ALERT] High Wind station={cleaned.get('station_id')} w={w}")

    if p is not None and p > TH_FLOOD_MMH:
        alert = {
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Flood",
            "severity": "warning",
            "value": {"precipitation_mmh": p},
            "timestamp": now_iso(),
            "raw_reading": cleaned.get("raw")
        }
        publish_alert(alert)
        print(f"[ALERT] Flood station={cleaned.get('station_id')} p={p}")

    if t is not None and (t < TH_TEMP_LOW_C or t > TH_TEMP_HIGH_C):
        alert = {
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Extreme Temperature",
            "severity": "critical",
            "value": {"temperature_c": t},
            "timestamp": now_iso(),
            "raw_reading": cleaned.get("raw")
        }
        publish_alert(alert)
        print(f"[ALERT] Extreme Temp station={cleaned.get('station_id')} t={t}")

def main():
    print(f"Starting alert consumer (tolerant to nulls). Topics -> readings:{READINGS_TOPIC}, alerts:{ALERTS_TOPIC}, dlq:{DLQ_TOPIC}")
    try:
        while True:
            for msg in consumer:
                try:
                    record = msg.value
                    # debug print first record if needed:
                    # print("[DEBUG] record:", record)

                    cleaned = {
                        "raw": record,
                        "station_id": record.get("station_id") if isinstance(record, dict) else None,
                        "reading_id": record.get("reading_id") if isinstance(record, dict) else None
                    }

                    # parse fields safely
                    cleaned["temperature_c"] = None
                    cleaned["wind_speed_kmh"] = None
                    cleaned["precipitation_mmh"] = None
                    # try temperature
                    try:
                        raw_temp = record.get("temperature") if isinstance(record, dict) else None
                        if not is_missing(raw_temp):
                            cleaned["temperature_c"] = round(temp_to_celsius(raw_temp), 2) if temp_to_celsius(raw_temp) is not None else None
                    except Exception:
                        cleaned["temperature_c"] = None

                    # wind
                    try:
                        raw_wind = record.get("wind_speed") if isinstance(record, dict) else None
                        if not is_missing(raw_wind):
                            cleaned["wind_speed_kmh"] = round(wind_to_kmh(raw_wind), 2) if wind_to_kmh(raw_wind) is not None else None
                    except Exception:
                        cleaned["wind_speed_kmh"] = None

                    # precipitation
                    try:
                        raw_prec = record.get("precipitation") if isinstance(record, dict) else None
                        if not is_missing(raw_prec):
                            cleaned["precipitation_mmh"] = round(precip_to_mmh(raw_prec), 2) if precip_to_mmh(raw_prec) is not None else None
                    except Exception:
                        cleaned["precipitation_mmh"] = None

                    # If all three missing -> DLQ
                    if cleaned["temperature_c"] is None and cleaned["wind_speed_kmh"] is None and cleaned["precipitation_mmh"] is None:
                        publish_dlq(record, "Insufficient numeric fields (all of temperature/wind/precip missing)")
                        print(f"[DLQ] Insufficient numeric fields for record: {cleaned.get('reading_id') or 'unknown'} station:{cleaned.get('station_id') or 'unknown'}")
                        continue

                    # Evaluate alerts for available fields
                    evaluate_and_publish(cleaned)

                except Exception as e:
                    publish_dlq(record if isinstance(record, dict) else {"raw": str(record)}, f"processing_exception: {str(e)}")
                    print("[ERROR] exception processing message:", str(e))
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping alert consumer (user interrupt)...")
    finally:
        consumer.close()
        producer.flush()
        producer.close()
        print("Alert consumer closed.")

if __name__ == "__main__":
    main()
