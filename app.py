player_id = 1234
match_id = 9876

spark.sql(f"""
SELECT
  p.playerId                              AS player_id,
  p.playerName                            AS player_name,
  m.matchId                               AS match_id,
  m.matchName                             AS match_name,
  m.playerOfTheMatchId                    AS player_of_match_id,
  -- fallback: use any available format stat row for the player (ODI/T20/Test)
  COALESCE(o.runsScored, t.runsScored, te.runsScored) AS runs_scored,
  COALESCE(o.wickets, t.wickets, te.wickets)         AS wickets,
  COALESCE(o.strikeRate, t.strikeRate, te.strikeRate) AS strike_rate,
  COALESCE(o.economy, t.economy, te.economy)         AS economy
FROM playerinfo_dim p
LEFT JOIN matches_info_fact m ON m.matchId = {match_id}
LEFT JOIN odiformatstats_fact o ON o.playerId = p.playerId
LEFT JOIN t20formatstats_fact t ON t.playerId = p.playerId
LEFT JOIN testformatstats_fact te ON te.playerId = p.playerId
WHERE p.playerId = {player_id}
LIMIT 1
""").show(truncate=False)
