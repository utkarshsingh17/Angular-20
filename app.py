USE cricket_dw;

-- dims
CREATE TABLE IF NOT EXISTS dim_venue (
  venue_id BIGINT PRIMARY KEY,
  venue_name VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS dim_team (
  team_id BIGINT PRIMARY KEY,
  team_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS dim_player (
  player_id BIGINT PRIMARY KEY,
  team_id BIGINT,
  player_name VARCHAR(512),
  born_date DATE,
  age_years INT,
  birth_place VARCHAR(512),
  role VARCHAR(128),
  batting_style VARCHAR(128),
  bowling_style VARCHAR(128),
  test_player_id BIGINT,
  odi_player_id BIGINT,
  t20_player_id BIGINT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- facts
CREATE TABLE IF NOT EXISTS fact_match (
  match_id BIGINT PRIMARY KEY,
  series_id BIGINT,
  match_name VARCHAR(512),
  venue_id BIGINT,
  start_date DATE,
  end_date DATE,
  team1_score VARCHAR(128), -- keep text as it might include wickets
  team2_score VARCHAR(128),
  player_of_match_id BIGINT
);

-- player format stats (separate tables, same columns)
CREATE TABLE IF NOT EXISTS fact_player_test_stats (
  player_id BIGINT,
  test_player_id BIGINT,
  matches INT, innings INT, runs_scored BIGINT, balls_faced BIGINT,
  high_score VARCHAR(64), average DOUBLE, strike_rate DOUBLE, not_outs INT,
  fours INT, sixes INT, fifties INT, hundreds INT,
  double_hundreds INT, bowling_innings INT, balls_bowled BIGINT,
  runs_conceded BIGINT, wickets INT, bowling_average DOUBLE, economy DOUBLE,
  bowling_strike_rate DOUBLE, best_bowling_in_innings VARCHAR(64),
  best_bowling_in_match VARCHAR(64), five_wicket_hauls INT, ten_wicket_hauls INT
);

CREATE TABLE IF NOT EXISTS fact_player_odi_stats LIKE fact_player_test_stats;
CREATE TABLE IF NOT EXISTS fact_player_t20_stats LIKE fact_player_test_stats;

-- Unknown placeholders
INSERT IGNORE INTO dim_player (player_id, player_name) VALUES (-1, 'UNKNOWN');
INSERT IGNORE INTO dim_team (team_id, team_name) VALUES (-1, 'UNKNOWN');
INSERT IGNORE INTO dim_venue (venue_id, venue_name) VALUES (-1, 'UNKNOWN');
