# As an Intern
from pyspark.sql import functions as F
from config import JDBC_URL, DB_PROPS
from write_jdbc import write_df_to_mysql

# -------- DIMENSIONS -------- #
dim_player = (player_info
              .select(
                  F.col("playerId").alias("player_id"),
                  F.col("playerName").alias("player_name"),
                  F.col("teamId").alias("team_id"),
                  F.col("born_date").alias("born_date"),
                  F.col("age_years").alias("age_years"),
                  F.col("birthPlace").alias("birth_place"),
                  F.col("role").alias("role"),
                  F.col("battingStyle").alias("batting_style"),
                  F.col("bowlingStyle").alias("bowling_style")
              )
              .dropDuplicates())

write_df_to_mysql(dim_player, "player_dim")

dim_team = (team_details
            .select(
                F.col("teamId").alias("team_id"),
                F.col("teamName").alias("team_name")
            )
            .dropDuplicates())

write_df_to_mysql(dim_team, "team_dim")

dim_venue = (venue_details
             .select(
                 F.col("venueId").alias("venue_id"),
                 F.col("venueName").alias("venue_name")
             )
             .dropDuplicates())

write_df_to_mysql(dim_venue, "venue_dim")

dim_format = spark.createDataFrame(
    [(1, "ODI"), (2, "T20"), (3, "Test")],
    ["format_id", "format_name"]
)
write_df_to_mysql(dim_format, "format_dim")

# -------- FACTS -------- #
fact_match = (matches_info
              .select(
                  F.col("matchId").alias("match_id"),
                  F.col("seriesId").alias("series_id"),
                  F.col("matchName").alias("match_name"),
                  F.col("venueId").alias("venue_id"),
                  F.col("startDate").alias("start_date"),
                  F.col("endDate").alias("end_date"),
                  F.col("team1runs").alias("team1_runs"),
                  F.col("team1wickets").alias("team1_wickets"),
                  F.col("team1over").alias("team1_over"),
                  F.col("team2runs").alias("team2_runs"),
                  F.col("team2wickets").alias("team2_wickets"),
                  F.col("team2over").alias("team2_over"),
                  F.col("match_format").alias("match_format"),
                  F.col("playerOfTheMatchId").alias("player_of_match_key")
              ))
write_df_to_mysql(fact_match, "match_fact")

odi_stats = odi_format_stats.withColumn("format_id", F.lit(1))
t20_stats = t20_format_stats.withColumn("format_id", F.lit(2))
test_stats = test_format_stats.withColumn("format_id", F.lit(3))

fact_player_stats = (odi_stats
    .unionByName(t20_stats, allowMissingColumns=True)
    .unionByName(test_stats, allowMissingColumns=True)
    .select(
        F.col("playerId").alias("player_id"),
        F.col("format_id"),
        F.col("matches"),
        F.col("innings"),
        F.col("runsScored").alias("runs_scored"),
        F.col("ballsFaced").alias("balls_faced"),
        F.col("highScore").alias("high_score"),
        F.col("average"),
        F.col("strikeRate").alias("strike_rate"),
        F.col("notOuts").alias("not_outs"),
        F.col("fours"),
        F.col("sixes"),
        F.col("fifties"),
        F.col("hundreds"),
        F.col("doubleHundreds").alias("double_hundreds"),
        F.col("bowlingInnings").alias("bowling_innings"),
        F.col("ballsBowled").alias("balls_bowled"),
        F.col("runsConceded").alias("runs_conceded"),
        F.col("wickets"),
        F.col("bowlingAverage").alias("bowling_average"),
        F.col("economy"),
        F.col("bowlingStrikeRate").alias("bowling_strike_rate"),
        F.col("bestBowlingInInnings").alias("best_bowling_innings"),
        F.col("bestBowlingInMatch").alias("best_bowling_match"),
        F.col("fiveWicketHauls").alias("five_wicket_hauls"),
        F.col("tenWicketHauls").alias("ten_wicket_hauls")
    ))
write_df_to_mysql(fact_player_stats, "player_stats_fact")

fact_player_venue = (player_stats_per_venue
                     .select(
                         F.col("playerId").alias("player_id"),
                         F.col("venueId").alias("venue_id"),
                         F.col("matches"),
                         F.col("runsScored").alias("runs_scored"),
                         F.col("wickets")
                     ))
write_df_to_mysql(fact_player_venue, "player_venue_fact")
