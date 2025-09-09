#!/usr/bin/env python3
"""
spark_producer.py

Two modes:
1) one-shot: read a JSON array file and publish all rows to Kafka topic `weather.readings`.
   Usage: spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 producer/spark_producer.py \
            --input data/dummy_data1.json --mode file --bootstrap localhost:9092 --topic weather.readings

2) directory-stream: watch a directory of JSON (each file is a JSON object per line or JSON array),
   and stream new files to Kafka. Use --mode stream and --input data/stream_dir
"""
import argparse
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_json, struct, col

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Input JSON file or input directory")
    parser.add_argument("--mode", "-m", choices=["file", "stream"], default="file", help="file = one-shot, stream = watch directory")
    parser.add_argument("--bootstrap", default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="weather.readings", help="Kafka topic to publish")
    parser.add_argument("--checkpoint", default="checkpoints/producer_ckpt", help="Checkpoint dir for streaming mode")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("SparkProducer").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    if args.mode == "file":
        # read JSON array of objects (entire file)
        df = spark.read.option("multiline", True).json(args.input)
        # ensure we have a string value column for Kafka
        kafka_df = df.select(to_json(struct([col(c) for c in df.columns])).alias("value"))
        kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as value")
        # write to Kafka (one-shot)
        kafka_df.write.format("kafka") \
            .option("kafka.bootstrap.servers", args.bootstrap) \
            .option("topic", args.topic) \
            .save()
        print(f"Published {df.count()} records from {args.input} to topic {args.topic}")

    else:
        # streaming mode: watch directory where new json files will appear
        # files can be JSON lines (one json object per line) or multi-line json objects if `multiline` is set
        df_stream = spark.readStream.schema("reading_id STRING, station_id STRING, temperature STRING, humidity STRING, wind_speed STRING, precipitation STRING, pressure STRING, reading_timestamp STRING, location STRING").json(args.input)
        kafka_df = df_stream.select(to_json(struct([col(c) for c in df_stream.columns])).alias("value"))
        kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as value")

        query = kafka_df.writeStream.format("kafka") \
            .option("kafka.bootstrap.servers", args.bootstrap) \
            .option("topic", args.topic) \
            .option("checkpointLocation", args.checkpoint) \
            .start()
        query.awaitTermination()

if __name__ == "__main__":
    main()
