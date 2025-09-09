#!/usr/bin/env python3
"""
consumer/alert_consumer.py

Enhanced consumer:
 - consumes from topic 'weather.readings'
 - normalizes fields using utils.parser
 - evaluates alert rules and publishes alerts to 'weather.alerts'
 - sends malformed messages to 'weather.dlq'
"""
import json
import time
import uuid
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from utils import parser

BOOTSTRAP_SERVERS = ["localhost:9092"]
READINGS_TOPIC = "weather.readings"
ALERTS_TOPIC = "weather.alerts"
DLQ_TOPIC = "weather.dlq"
GROUP_ID = "weather.alerts.processor"

# Thresholds (configurable)
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

def build_cleaned(record: dict):
    """Return a cleaned dict with standardized numeric fields and raw copy."""
    cleaned = {}
    cleaned["station_id"] = record.get("station_id")
    cleaned["reading_id"] = record.get("reading_id")
    cleaned["location"] = record.get("location")
    # Parse fields using parser
    try:
        cleaned["temperature_c"] = None if record.get("temperature") is None else round(parser.parse_temperature(record.get("temperature")), 2)
    except Exception:
        cleaned["temperature_c"] = None
    try:
        cleaned["wind_speed_kmh"] = None if record.get("wind_speed") is None else round(parser.parse_wind_speed(record.get("wind_speed")), 2)
    except Exception:
        cleaned["wind_speed_kmh"] = None
    try:
        cleaned["precipitation_mmh"] = None if record.get("precipitation") is None else round(parser.parse_precipitation(record.get("precipitation")), 2)
    except Exception:
        cleaned["precipitation_mmh"] = None
    try:
        cleaned["humidity_pct"] = None if record.get("humidity") is None else round(parser.parse_humidity(record.get("humidity")), 2)
    except Exception:
        cleaned["humidity_pct"] = None
    try:
        cleaned["pressure_hpa"] = None if record.get("pressure") is None else round(parser.parse_pressure(record.get("pressure")), 2)
    except Exception:
        cleaned["pressure_hpa"] = None

    # reading_timestamp -> pass through if present; else annotate with processing time
    rt = record.get("reading_timestamp")
    cleaned["reading_timestamp"] = rt if rt else now_iso()
    # keep original raw
    cleaned["raw"] = record
    return cleaned

def evaluate_alerts(cleaned: dict):
    """
    Returns a list of alert dicts (may be empty). Each alert dict has:
      alert_id, station_id, alert_type, severity, value, unit, timestamp, raw_reading
    """
    alerts = []
    t = cleaned.get("temperature_c")
    w = cleaned.get("wind_speed_kmh")
    p = cleaned.get("precipitation_mmh")

    # Storm: priority — if storm triggers, mark critical and do not emit separate high wind / flood
    if (w is not None and p is not None) and (w > TH_STORM_WIND_KMH and p >= TH_STORM_PRECIP_MMH):
        alerts.append({
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Storm",
            "severity": "critical",
            "value": {"wind_speed_kmh": w, "precipitation_mmh": p},
            "timestamp": now_iso(),
            "raw_reading": cleaned["raw"]
        })
        # return immediately so we don't duplicate with lower-priority alerts
        return alerts

    # High wind
    if w is not None and w > TH_HIGH_WIND_KMH:
        alerts.append({
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "High Wind",
            "severity": "warning",
            "value": {"wind_speed_kmh": w},
            "timestamp": now_iso(),
            "raw_reading": cleaned["raw"]
        })

    # Flood warning
    if p is not None and p > TH_FLOOD_MMH:
        alerts.append({
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Flood",
            "severity": "warning",
            "value": {"precipitation_mmh": p},
            "timestamp": now_iso(),
            "raw_reading": cleaned["raw"]
        })

    # Extreme temperature
    if t is not None and (t < TH_TEMP_LOW_C or t > TH_TEMP_HIGH_C):
        alerts.append({
            "alert_id": str(uuid.uuid4()),
            "station_id": cleaned.get("station_id"),
            "alert_type": "Extreme Temperature",
            "severity": "critical",
            "value": {"temperature_c": t},
            "timestamp": now_iso(),
            "raw_reading": cleaned["raw"]
        })

    return alerts

def publish_alert(alert: dict):
    producer.send(ALERTS_TOPIC, value=alert, key=(alert.get("station_id") or "unknown").encode("utf-8"))

def publish_dlq(record: dict, reason: str):
    payload = {
        "error": reason,
        "failed_at": now_iso(),
        "record": record
    }
    producer.send(DLQ_TOPIC, value=payload, key=(record.get("station_id") or "unknown").encode("utf-8"))

def main():
    print(f"Starting alert consumer -> readings:{READINGS_TOPIC}, alerts:{ALERTS_TOPIC}, dlq:{DLQ_TOPIC}")
    try:
        while True:
            for msg in consumer:
                try:
                    record = msg.value
                    cleaned = build_cleaned(record)
                    # If critical numeric parsing failed for everything, send to DLQ
                    # (we define critical fields as at least one of temp/wind/precip must parse)
                    if cleaned["temperature_c"] is None and cleaned["wind_speed_kmh"] is None and cleaned["precipitation_mmh"] is None:
                        # not enough data to evaluate alerts; but still log and continue
                        publish_dlq(record, "Insufficient numeric fields (temp/wind/precip failed to parse)")
                        print(f"[DLQ] Insufficient numeric fields for record: {record.get('reading_id') or 'unknown'}")
                        continue

                    alerts = evaluate_alerts(cleaned)
                    if not alerts:
                        # no alerts, optionally we could store cleaned record elsewhere; for now just log
                        print(f"[OK] No alerts for station={cleaned.get('station_id')} reading_id={cleaned.get('reading_id')}")
                    else:
                        for alert in alerts:
                            publish_alert(alert)
                            print(f"[ALERT] Published: {alert['alert_type']} station={alert['station_id']} severity={alert['severity']}")

                except Exception as e:
                    # Unexpected error processing this message — send to DLQ with exception text
                    reason = f"processing_exception: {str(e)}"
                    publish_dlq(msg.value if hasattr(msg, "value") else {"raw": str(msg)}, reason)
                    print(f"[ERROR] Exception processing message: {reason}")
            # consumer timed out, short sleep to avoid busy loop
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
