# As an Intern
from pyspark.sql import functions as F

# matches_info: your cleaned matches DataFrame
# venue_map: df with columns (venue_id, venue_key)
# player_map: df with columns (player_id, player_key)

# 1. normalize column names if needed
matches = matches_info \
    .withColumnRenamed("matchId", "match_id") \
    .withColumnRenamed("seriesId", "series_id") \
    .withColumnRenamed("matchName", "match_name") \
    .withColumnRenamed("venueId", "venue_id") \
    .withColumnRenamed("startDate", "start_date") \
    .withColumnRenamed("endDate", "end_date") \
    .withColumnRenamed("playerOfTheMatchId", "player_of_match_id")

# 2. join to mapping tables to get surrogate keys
fact_matches = (matches
    .join(venue_map.select(F.col("venue_id").alias("v_venue_id"), "venue_key"),
          matches.venue_id == F.col("v_venue_id"), how="left")
    .join(player_map.select(F.col("player_id").alias("p_player_id"), "player_key"),
          matches.player_of_match_id == F.col("p_player_id"), how="left")
    # 3. coalesce missing surrogate keys to -1 (Unknown)
    .withColumn("venue_key", F.coalesce(F.col("venue_key"), F.lit(-1)).cast("int"))
    .withColumn("player_of_match_key", F.coalesce(F.col("player_key"), F.lit(-1)).cast("int"))
    # 4. select final set of columns that match your MySQL fact schema
    .select(
        F.col("match_id").alias("match_id"),
        F.col("series_id").alias("series_id"),
        F.col("match_name").alias("match_name"),
        F.col("venue_key"),
        F.to_date("start_date").alias("start_date"),
        F.to_date("end_date").alias("end_date"),
        F.col("team1runs").alias("team1_runs"),
        F.col("team1wickets").alias("team1_wickets"),
        F.col("team1over").alias("team1_over"),
        F.col("team2runs").alias("team2_runs"),
        F.col("team2wickets").alias("team2_wickets"),
        F.col("team2over").alias("team2_over"),
        F.col("match_format").alias("match_format"),
        F.col("player_of_match_key").alias("player_of_match_key")
    )
)
