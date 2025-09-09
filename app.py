#!/usr/bin/env python3
"""
spark_alert_consumer.py

Structured Streaming job:
 - read from Kafka `weather.readings`
 - parse JSON -> columns
 - clean/standardize numeric fields
 - generate alerts per rules and write alerts to Kafka topic `weather.alerts`
 - write DLQ entries to Kafka topic `weather.dlq` when temp/wind/precip all missing
 - optionally write cleaned records to `weather.cleaned`
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, when, regexp_extract,
    expr, lit, concat_ws, current_timestamp
)
from pyspark.sql.types import StructType, StructField, StringType

# Configs
KAFKA_BOOTSTRAP = "localhost:9092"
INPUT_TOPIC = "weather.readings"
ALERTS_TOPIC = "weather.alerts"
DLQ_TOPIC = "weather.dlq"
CLEANED_TOPIC = "weather.cleaned"
CHECKPOINT_BASE = "checkpoints/spark_alert"

# Thresholds
TH_HIGH_WIND_KMH = 70.0
TH_FLOOD_MMH = 30.0
TH_STORM_WIND_KMH = 50.0
TH_STORM_PRECIP_MMH = 20.0
TH_TEMP_LOW_C = -20.0
TH_TEMP_HIGH_C = 40.0

# JSON schema for incoming messages (strings allowed; null tolerated)
json_schema = StructType([
    StructField("reading_id", StringType(), True),
    StructField("station_id", StringType(), True),
    StructField("temperature", StringType(), True),
    StructField("humidity", StringType(), True),
    StructField("wind_speed", StringType(), True),
    StructField("precipitation", StringType(), True),
    StructField("pressure", StringType(), True),
    StructField("reading_timestamp", StringType(), True),
    StructField("location", StringType(), True),
])

spark = SparkSession.builder.appName("SparkAlertConsumer").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Read from Kafka
raw = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", INPUT_TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

# Extract JSON string and parse into columns
json_str = raw.selectExpr("CAST(value AS STRING) as json_str")
parsed = json_str.select(from_json(col("json_str"), json_schema).alias("data")).select("data.*")

# helper regex extract function
num_extract = lambda c: regexp_extract(c, r"([-+]?\d+(?:\.\d+)?)", 1).cast("double")

# Clean/standardize
cleaned = parsed \
    .withColumn("temperature_num", num_extract(col("temperature"))) \
    .withColumn("temperature_unit", expr("lower(trim(substring(temperature, length(regexp_extract(temperature, '[-+]?\\d+(?:\\.\\d+)?', 0))+1)))")) \
    .withColumn("temperature_c",
        when(col("temperature_num").isNull(), None)
        .when(col("temperature").rlike("(?i)k$"), col("temperature_num") - 273.15)
        .when(col("temperature").rlike("(?i)f$"), (col("temperature_num") - 32.0) * 5.0/9.0)
        .otherwise(col("temperature_num"))
    ) \
    .withColumn("wind_num", num_extract(col("wind_speed"))) \
    .withColumn("wind_speed_kmh",
        when(col("wind_speed").rlike("(?i)km"), col("wind_num"))
        .when(col("wind_speed").rlike("(?i)mph"), col("wind_num") * 1.60934)
        .when(col("wind_speed").rlike("(?i)m/s"), col("wind_num") * 3.6)
        .when(col("wind_speed").rlike("(?i)m/h"), col("wind_num") * 0.001)
        .otherwise(col("wind_num"))
    ) \
    .withColumn("precip_num", num_extract(col("precipitation"))) \
    .withColumn("precipitation_mmh",
        when(col("precipitation").rlike("(?i)in"), col("precip_num") * 25.4)
        .otherwise(col("precip_num"))
    ) \
    .withColumn("humidity_pct", num_extract(col("humidity"))) \
    .withColumn("pressure_hpa", num_extract(col("pressure"))) \
    .withColumn("reading_ts", expr("to_timestamp(reading_timestamp)")) \
    .withColumn("processed_at", current_timestamp())

# Determine dlq condition: all three critical numeric fields null
with_flags = cleaned.withColumn("missing_all_crit",
                                (col("temperature_c").isNull()) &
                                (col("wind_speed_kmh").isNull()) &
                                (col("precipitation_mmh").isNull()))

# DLQ stream: send entire raw JSON + reason
dlq_df = with_flags.filter(col("missing_all_crit") == True) \
    .select(to_json(struct(col("*"))).alias("value"))

# Cleaned stream for downstream consumers (non-DLQ)
clean_non_dlq = with_flags.filter(col("missing_all_crit") == False)

# Generate alerts: storm priority, then others (we'll create one row per alert)
# 1) storm
storm_alerts = clean_non_dlq.filter((col("wind_speed_kmh").isNotNull()) & (col("precipitation_mmh").isNotNull()) &
                                    (col("wind_speed_kmh") > TH_STORM_WIND_KMH) &
                                    (col("precipitation_mmh") >= TH_STORM_PRECIP_MMH)) \
    .select(
        to_json(struct(
            expr("uuid() as alert_id"),
            col("station_id"),
            lit("Storm").alias("alert_type"),
            lit("critical").alias("severity"),
            struct(col("wind_speed_kmh"), col("precipitation_mmh")).alias("value"),
            col("processed_at").alias("timestamp"),
            struct(*[col(c) for c in parsed.columns]).alias("raw_reading")
        )).alias("value")
    )

# 2) high wind (exclude those already captured as storm)
high_wind_alerts = clean_non_dlq.filter((col("wind_speed_kmh").isNotNull()) & (col("wind_speed_kmh") > TH_HIGH_WIND_KMH) &
                                        ~((col("wind_speed_kmh") > TH_STORM_WIND_KMH) & (col("precipitation_mmh") >= TH_STORM_PRECIP_MMH))) \
    .select(to_json(struct(
        expr("uuid() as alert_id"),
        col("station_id"),
        lit("High Wind").alias("alert_type"),
        lit("warning").alias("severity"),
        struct(col("wind_speed_kmh")).alias("value"),
        col("processed_at").alias("timestamp"),
        struct(*[col(c) for c in parsed.columns]).alias("raw_reading")
    )).alias("value"))

# 3) flood
flood_alerts = clean_non_dlq.filter((col("precipitation_mmh").isNotNull()) & (col("precipitation_mmh") > TH_FLOOD_MMH) &
                                    ~((col("wind_speed_kmh") > TH_STORM_WIND_KMH) & (col("precipitation_mmh") >= TH_STORM_PRECIP_MMH))) \
    .select(to_json(struct(
        expr("uuid() as alert_id"),
        col("station_id"),
        lit("Flood").alias("alert_type"),
        lit("warning").alias("severity"),
        struct(col("precipitation_mmh")).alias("value"),
        col("processed_at").alias("timestamp"),
        struct(*[col(c) for c in parsed.columns]).alias("raw_reading")
    )).alias("value"))

# 4) extreme temperature
ext_temp_alerts = clean_non_dlq.filter((col("temperature_c").isNotNull()) & ((col("temperature_c") < TH_TEMP_LOW_C) | (col("temperature_c") > TH_TEMP_HIGH_C))) \
    .select(to_json(struct(
        expr("uuid() as alert_id"),
        col("station_id"),
        lit("Extreme Temperature").alias("alert_type"),
        lit("critical").alias("severity"),
        struct(col("temperature_c")).alias("value"),
        col("processed_at").alias("timestamp"),
        struct(*[col(c) for c in parsed.columns]).alias("raw_reading")
    )).alias("value"))

# Union alerts into single stream
alerts_union = storm_alerts.union(high_wind_alerts).union(flood_alerts).union(ext_temp_alerts)

# Write alerts to Kafka
alerts_query = alerts_union.writeStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("topic", ALERTS_TOPIC) \
    .option("checkpointLocation", CHECKPOINT_BASE + "/alerts_ckpt") \
    .start()

# Write DLQ entries to Kafka
dlq_query = dlq_df.writeStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("topic", DLQ_TOPIC) \
    .option("checkpointLocation", CHECKPOINT_BASE + "/dlq_ckpt") \
    .start()

# Optionally write cleaned records back to Kafka for downstream consumers
cleaned_out = clean_non_dlq.select(to_json(struct([col(c) for c in clean_non_dlq.columns])).alias("value"))
cleaned_query = cleaned_out.writeStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("topic", CLEANED_TOPIC) \
    .option("checkpointLocation", CHECKPOINT_BASE + "/cleaned_ckpt") \
    .start()

# Await termination
spark.streams.awaitAnyTermination()
