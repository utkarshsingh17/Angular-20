#!/usr/bin/env python3
import json
from kafka import KafkaConsumer
import time

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "weather.readings"
GROUP_ID = "weather.consumer.group"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset="earliest",    # for dev; in prod likely 'latest'
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    consumer_timeout_ms=1000
)

def main():
    print(f"Starting consumer for topic {TOPIC} -> bootstrap: {BOOTSTRAP_SERVERS}")
    try:
        while True:
            for msg in consumer:
                # msg.value is already deserialized JSON
                received_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
                print(f"[{received_ts}] Partition:{msg.partition} Offset:{msg.offset} Key:{msg.key} Value:{json.dumps(msg.value)}")
            # consumer timed out waiting for messages - sleep briefly and continue
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
