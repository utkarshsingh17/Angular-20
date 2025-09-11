# As an Intern
# load_mysql_raw_to_spark.py
# Read raw tables from MySQL into Spark DataFrames, validate, and write Bronze parquet.
# Using Python logger for structured logging.

import logging
import os
import sys
from pyspark.sql import SparkSession, functions as F

# ---------- LOGGER ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RawDataLoader")

# ---------- CONFIG ----------
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "cricket_src"
MYSQL_USER = "root"
MYSQL_PASS = "your_mysql_password"   # change
TABLES = ["players_raw", "matches_raw"]

BRONZE_DIR = "/tmp/cricket_bronze"   # local bronze layer

WRITE_BACK_TO_DW = False
DW_JDBC_URL = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/cricket_dw?useSSL=false&serverTimezone=UTC"
DW_USER = "dw_user"
DW_PASS = "dw_pass"

jdbc_url = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?useSSL=false&serverTimezone=UTC"

# ---------- Spark ----------
spark = SparkSession.builder \
    .appName("load-mysql-raw-to-spark") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

os.makedirs(BRONZE_DIR, exist_ok=True)

def read_table(table_name):
    logger.info(f"Reading table: {table_name}")
    df = spark.read.format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", table_name) \
        .option("user", MYSQL_USER) \
        .option("password", MYSQL_PASS) \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()
    return df

def write_bronze(df, table_name):
    path = f"{BRONZE_DIR}/{table_name}"
    logger.info(f"Writing Bronze parquet for {table_name} -> {path}")
    df.write.mode("overwrite").parquet(path)
    logger.info(f"Done writing {table_name}")

def write_back_to_dw(df, table_name):
    target_table = f"stg_{table_name}"
    logger.info(f"Writing to DW table {target_table}")
    df.write.format("jdbc") \
        .option("url", DW_JDBC_URL) \
        .option("dbtable", target_table) \
        .option("user", DW_USER) \
        .option("password", DW_PASS) \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .mode("overwrite") \
        .save()
    logger.info(f"Done writing to DW {target_table}")

def validate(df, table_name, sample_n=5):
    cnt = df.count()
    logger.info(f"Validation: {table_name} row count = {cnt}")
    df.show(sample_n, truncate=False)

def main():
    for t in TABLES:
        try:
            df = read_table(t)
        except Exception as e:
            logger.error(f"Failed to read {t}: {e}")
            continue

        # tiny cleaning example
        if "name" in df.columns:
            df = df.withColumn("name", F.trim(F.col("name")))

        validate(df, t)
        write_bronze(df, t)

        if WRITE_BACK_TO_DW:
            write_back_to_dw(df, t)

    logger.info("All tables processed.")
    spark.stop()

if __name__ == "__main__":
    main()
