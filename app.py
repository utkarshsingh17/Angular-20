#!/usr/bin/env python3
#!/usr/bin/env python3
"""
producer_file.py
Read rows from a CSV or JSON file and publish them to Kafka topic `weather.readings`.
Usage:
    python producer_file.py --file data/dummy_data.csv --repeat 1 --interval 0.5
"""
import argparse
import csv
import json
import time
import os
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "weather.readings"

def create_producer(bootstrap_servers):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=5
    )

def read_csv_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize empty strings to None
            for k, v in list(row.items()):
                if v is not None:
                    v = v.strip()
                row[k] = v if v != "" else None
            yield row

def read_jsonl_rows(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            yield json.loads(line)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", required=True, help="Path to CSV or JSONL file")
    parser.add_argument("--repeat", "-r", type=int, default=1, help="How many times to replay the file (default 1). Use 0 for infinite.")
    parser.add_argument("--interval", "-i", type=float, default=0.5, help="Seconds between messages (default 0.5)")
    parser.add_argument("--bootstrap", nargs="+", default=BOOTSTRAP_SERVERS, help="Kafka bootstrap servers")
    args = parser.parse_args()

    path = args.file
    if not os.path.exists(path):
        raise SystemExit(f"File not found: {path}")

    producer = create_producer(args.bootstrap)
    try:
        iteration = 0
        while True:
            iteration += 1
            # choose reader by extension
            ext = os.path.splitext(path)[1].lower()
            if ext in [".json", ".jsonl"]:
                rows = read_jsonl_rows(path)
            else:
                rows = read_csv_rows(path)

            count = 0
            for row in rows:
                # Use station_id as key if present to keep partitioning consistent
                key = None
                station_key = row.get("station_id") or row.get("station id") or row.get("station")
                if station_key:
                    key = str(station_key).encode("utf-8")
                producer.send(TOPIC, value=row, key=key)
                count += 1
                print(f"Produced ({count}): {json.dumps(row, ensure_ascii=False)}")
                time.sleep(args.interval)

            producer.flush()
            print(f"Finished file iteration #{iteration}")

            if args.repeat == 0:
                continue
            if iteration >= args.repeat:
                break
    except KeyboardInterrupt:
        print("Producer interrupted by user.")
    finally:
        producer.flush()
        producer.close()
        print("Producer closed.")

if __name__ == "__main__":
    main()
