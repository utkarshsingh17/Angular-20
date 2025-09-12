player_id = 1234
N = 10

spark.sql(f"""
SELECT
  pms.match_id,
  m.startDate AS match_date,
  pms.runs_scored,
  pms.wickets,
  ROUND( CASE WHEN pms.balls_faced>0 THEN 100.0 * pms.runs_scored / pms.balls_faced END,2) as strike_rate
FROM player_match_stats pms
JOIN matches_info_fact m ON pms.match_id = m.matchId
WHERE pms.player_id = {player_id}
ORDER BY m.startDate DESC
LIMIT {N}
""").show(truncate=False)
