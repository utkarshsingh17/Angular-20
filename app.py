player_id = 1234
opponent_team_id = 55

spark.sql(f"""
SELECT
  COUNT(*) as matches_count,
  SUM(COALESCE(pms.runs_scored,0)) as total_runs,
  ROUND(AVG(CASE WHEN pms.balls_faced>0 THEN 100.0*pms.runs_scored/pms.balls_faced END),2) as avg_strike_rate,
  SUM(COALESCE(pms.wickets,0)) as total_wickets
FROM player_match_stats pms
JOIN matches_info_fact m ON pms.match_id = m.matchId
WHERE pms.player_id = {player_id}
  AND (m.team1Id = {opponent_team_id} OR m.team2Id = {opponent_team_id})
""").show(truncate=False)
