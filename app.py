#!/usr/bin/env python3
#!/usr/bin/env python3
#!/usr/bin/env python3
"""
producer_json.py
Read records from a JSON file (array of objects) and publish them to Kafka topic `weather.readings`.

Usage:
    python producer_json.py --file data/dummy_data1.json --repeat 1 --interval 0.5
"""
import argparse
import json
import os
import time
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "weather.readings"

def create_producer(bootstrap_servers):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=5
    )

def load_json_array(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON file must contain an array of objects")
        return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", required=True, help="Path to JSON file containing array of objects")
    parser.add_argument("--repeat", "-r", type=int, default=1, help="How many times to replay the file (default 1). Use 0 for infinite.")
    parser.add_argument("--interval", "-i", type=float, default=0.5, help="Seconds between messages (default 0.5)")
    parser.add_argument("--bootstrap", nargs="+", default=BOOTSTRAP_SERVERS, help="Kafka bootstrap servers")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        raise SystemExit(f"File not found: {args.file}")

    records = load_json_array(args.file)
    producer = create_producer(args.bootstrap)

    try:
        iteration = 0
        while True:
            iteration += 1
            count = 0
            for record in records:
                station_id = str(record.get("station_id") or f"station-{count}")
                producer.send(TOPIC, value=record, key=station_id.encode("utf-8"))
                count += 1
                print(f"Produced ({count}): {json.dumps(record, ensure_ascii=False)}")
                time.sleep(args.interval)
            producer.flush()
            print(f"Finished sending {count} records (iteration #{iteration})")

            if args.repeat == 0:
                continue
            if iteration >= args.repeat:
                break
    except KeyboardInterrupt:
        print("Producer interrupted.")
    finally:
        producer.flush()
        producer.close()
        print("Producer closed.")

if __name__ == "__main__":
    main()
