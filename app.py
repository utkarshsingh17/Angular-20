#!/usr/bin/env python3
"""
consumer.py
Simple Kafka consumer that prints messages from weather.readings
"""
import json
import time
from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "weather.readings"
GROUP_ID = "weather.consumer.group"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset="earliest",   # start from beginning if no offset committed
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    consumer_timeout_ms=1000
)

def main():
    print(f"Starting consumer for topic {TOPIC}")
    try:
        while True:
            for msg in consumer:
                received_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
                key = msg.key.decode("utf-8") if msg.key else None
                print(f"[{received_ts}] partition:{msg.partition} offset:{msg.offset} key:{key} value:{json.dumps(msg.value, ensure_ascii=False)}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()
        print("Consumer closed.")

if __name__ == "__main__":
    main()
