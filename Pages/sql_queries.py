# pages/sql_queries.py
import streamlit as st
import sqlite3
import os
DB_PATH = os.path.abspath("cricbuzz.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

st.title("SQL Queries (25 Templates)")

# Add a dropdown with labels Q1..Q25
queries = {
    "Q1 - Players who represent India": """
-- Q1
SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
""",
    "Q2 - Matches in last 30 days": """
-- Q2
SELECT m.match_id, s.series_name || ' - ' || m.format as description,
       t1.team_name as team1, t2.team_name as team2,
       v.name as venue, m.match_date
FROM matches m
LEFT JOIN teams t1 ON m.team1_id = t1.team_id
LEFT JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
LEFT JOIN series s ON m.series_id = s.series_id
WHERE date(m.match_date) >= date('now','-30 days')
ORDER BY m.match_date DESC
""",
    "Q3 - Top 10 ODI run scorers": """
-- Q3 (requires player_career_stats)
SELECT p.full_name, pcs.total_runs, pcs.batting_average, pcs.centuries
FROM player_career_stats pcs
JOIN players p ON pcs.player_id = p.player_id
WHERE pcs.format = 'ODI'
ORDER BY pcs.total_runs DESC
LIMIT 10
""",
    "Q4 - Venues capacity > 50,000": """
-- Q4
SELECT name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC
""",
    "Q5 - Matches won per team": """
-- Q5
SELECT t.team_name, COUNT(*) as wins
FROM matches m
JOIN teams t ON m.winner_team_id = t.team_id
GROUP BY t.team_name
ORDER BY wins DESC
""",
    "Q6 - Count players by role": """
-- Q6
SELECT playing_role, COUNT(*) as player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC
""",
    "Q7 - Highest individual score by format": """
-- Q7 (from player_innings)
SELECT pi.format, MAX(pi.runs) as highest_score
FROM player_innings pi
GROUP BY pi.format
""",
    "Q8 - Series started in 2024": """
-- Q8
SELECT series_name, host_country, match_type, start_date, planned_matches
FROM series
WHERE strftime('%Y', start_date) = '2024'
""",
    # --- Intermediate (9-16) ---
    "Q9 - All-rounders >1000 runs AND >50 wickets": """
-- Q9 (assumes player_career_stats per format or overall)
SELECT p.full_name, pcs.total_runs, pcs.total_wickets, pcs.format
FROM player_career_stats pcs
JOIN players p ON p.player_id = pcs.player_id
WHERE pcs.total_runs > 1000 AND pcs.total_wickets > 50
""",
    "Q10 - Last 20 completed matches": """
-- Q10
SELECT m.match_id, s.series_name, t1.team_name, t2.team_name, 
       twin.team_name AS winner, m.result_margin, m.result_type, v.name as venue, m.match_date
FROM matches m
LEFT JOIN teams t1 ON m.team1_id = t1.team_id
LEFT JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN teams twin ON m.winner_team_id = twin.team_id
LEFT JOIN venues v ON m.venue_id = v.venue_id
LEFT JOIN series s ON m.series_id = s.series_id
WHERE m.match_status = 'Complete'
ORDER BY m.match_date DESC
LIMIT 20
""",
    "Q11 - Player performance across formats": """
-- Q11
SELECT p.player_id, p.full_name,
SUM(CASE WHEN pcs.format='Test' THEN pcs.total_runs ELSE 0 END) AS runs_test,
SUM(CASE WHEN pcs.format='ODI' THEN pcs.total_runs ELSE 0 END) AS runs_odi,
SUM(CASE WHEN pcs.format='T20I' THEN pcs.total_runs ELSE 0 END) AS runs_t20i,
ROUND(AVG(pcs.batting_average),2) AS overall_batting_avg
FROM player_career_stats pcs
JOIN players p ON pcs.player_id = p.player_id
GROUP BY p.player_id
HAVING COUNT(DISTINCT pcs.format) >= 2
""",
    "Q12 - Home vs Away performance (wins)": """
-- Q12 (requires venue.country and teams.country)
SELECT t.team_name,
SUM(CASE WHEN v.country = t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS home_wins,
SUM(CASE WHEN v.country != t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS away_wins
FROM matches m
JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
LEFT JOIN venues v ON m.venue_id = v.venue_id
GROUP BY t.team_name
""",
    "Q13 - Partnerships >=100": """
-- Q13 (requires partnerships table)
SELECT p1.full_name AS batter_a, p2.full_name AS batter_b, pr.runs, pr.innings_no, pr.match_id
FROM partnerships pr
JOIN players p1 ON pr.player_a_id = p1.player_id
JOIN players p2 ON pr.player_b_id = p2.player_id
WHERE pr.runs >= 100
""",
    "Q14 - Bowling performance per venue": """
-- Q14
SELECT b.player_id, pl.full_name, b.venue_id, v.name,
       ROUND(AVG(b.runs_conceded*1.0 / b.overs),2) AS avg_econ,
       SUM(b.wickets) AS total_wickets, COUNT(DISTINCT b.match_id) AS matches_played
FROM bowling_figures b
JOIN players pl ON pl.player_id = b.player_id
JOIN venues v ON v.venue_id = b.venue_id
GROUP BY b.player_id, b.venue_id
HAVING COUNT(DISTINCT b.match_id) >= 3
""",
    "Q15 - Players in close matches": """
-- Q15 (close match defined at match level)
WITH close_matches AS (
  SELECT match_id FROM matches
  WHERE (result_type = 'runs' AND result_margin < 50) OR (result_type LIKE '%wicket' AND result_margin < 5)
)
SELECT p.player_id, p.full_name,
 ROUND(AVG(pi.runs),2) AS avg_runs_in_close,
 COUNT(DISTINCT pi.match_id) AS close_matches_played,
 SUM(CASE WHEN m.winner_team_id = pi.team_id THEN 1 ELSE 0 END) AS close_matches_won_when_they_batted
FROM player_innings pi
JOIN players p ON p.player_id = pi.player_id
JOIN matches m ON m.match_id = pi.match_id
WHERE pi.match_id IN (SELECT match_id FROM close_matches)
GROUP BY p.player_id
""",
    "Q16 - Yearly batting performance since 2020": """
-- Q16
SELECT p.player_id, p.full_name, strftime('%Y', m.match_date) AS year,
       ROUND(AVG(pi.runs),2) AS avg_runs_per_match, ROUND(AVG((pi.runs*100.0)/pi.balls),2) AS avg_sr,
       COUNT(DISTINCT m.match_id) AS matches_played
FROM player_innings pi
JOIN matches m ON pi.match_id = m.match_id
JOIN players p ON p.player_id = pi.player_id
WHERE CAST(strftime('%Y', m.match_date) AS INTEGER) >= 2020
GROUP BY p.player_id, year
HAVING COUNT(DISTINCT m.match_id) >= 5
""",
    # --- Advanced (17-25) ---
    "Q17 - Toss advantage analysis": """
-- Q17
SELECT m.toss_decision,
 ROUND(100.0 * SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) / COUNT(*),2) AS pct_wins_when_won_toss,
 COUNT(*) as total_matches
FROM matches m
GROUP BY m.toss_decision
""",
    "Q18 - Most economical bowlers (ODI & T20)": """
-- Q18
SELECT p.player_id, p.full_name,
 ROUND(SUM(b.runs_conceded)*1.0/SUM(b.overs),2) AS economy,
 SUM(b.wickets) AS total_wickets,
 COUNT(DISTINCT b.match_id) AS matches
FROM bowling_figures b
JOIN players p ON p.player_id = b.player_id
JOIN matches m ON m.match_id = b.match_id
WHERE m.format IN ('ODI','T20I')
GROUP BY p.player_id
HAVING COUNT(DISTINCT b.match_id) >= 10 AND SUM(b.overs)/COUNT(DISTINCT b.match_id) >= 2
ORDER BY economy ASC
""",
    "Q19 - Consistency (avg & stddev) since 2022": """
-- Q19 (SQLite has no STDDEV built-in; approximate using variance window if available)
SELECT p.player_id, p.full_name,
 ROUND(AVG(pi.runs),2) AS avg_runs,
 ROUND((AVG(pi.runs*pi.runs) - AVG(pi.runs)*AVG(pi.runs)),2) AS variance_approx,
 COUNT(*) AS innings_played
FROM player_innings pi
JOIN matches m ON pi.match_id = m.match_id
JOIN players p ON p.player_id = pi.player_id
WHERE CAST(strftime('%Y', m.match_date) AS INTEGER) >= 2022
GROUP BY p.player_id
HAVING SUM(pi.balls) >= 10
""",
    "Q20 - Matches & batting avg per format": """
-- Q20
SELECT p.player_id, p.full_name,
 SUM(CASE WHEN m.format='Test' THEN 1 ELSE 0 END) AS test_matches,
 SUM(CASE WHEN m.format='ODI' THEN 1 ELSE 0 END) AS odi_matches,
 SUM(CASE WHEN m.format='T20I' THEN 1 ELSE 0 END) AS t20_matches,
 ROUND(AVG(CASE WHEN m.format='Test' THEN pi.runs END),2) AS avg_test,
 ROUND(AVG(CASE WHEN m.format='ODI' THEN pi.runs END),2) AS avg_odi,
 ROUND(AVG(CASE WHEN m.format='T20I' THEN pi.runs END),2) AS avg_t20
FROM player_innings pi
JOIN matches m ON pi.match_id = m.match_id
JOIN players p ON p.player_id = pi.player_id
GROUP BY p.player_id
HAVING (test_matches + odi_matches + t20_matches) >= 20
""",
    "Q21 - Performance ranking system": """
-- Q21 (example weighted score using player_career_stats)
SELECT p.player_id, p.full_name,
 ( (pcs.total_runs * 0.01) + (pcs.batting_average * 0.5) + (pcs.strike_rate * 0.3)
   + (pcs.total_wickets * 2 + (50 - pcs.bowling_average) * 0.5 + (6 - pcs.economy) * 2)
   + (COALESCE(pf.catches,0) * 3 + COALESCE(pf.stumpings,0) * 5)
 ) AS performance_score
FROM player_career_stats pcs
JOIN players p ON p.player_id = pcs.player_id
LEFT JOIN (SELECT player_id, SUM(catches) as catches, SUM(stumpings) as stumpings FROM player_fielding GROUP BY player_id) pf
  ON pf.player_id = p.player_id
ORDER BY performance_score DESC
LIMIT 50
""",
    "Q22 - Head-to-head analysis": """
-- Q22 (example for a single pair; generalization needs grouping by team pairs)
SELECT
 t1.team_name || ' vs ' || t2.team_name AS pair,
 COUNT(*) AS matches_played,
 SUM(CASE WHEN m.winner_team_id = m.team1_id THEN 1 ELSE 0 END) AS wins_team1,
 SUM(CASE WHEN m.winner_team_id = m.team2_id THEN 1 ELSE 0 END) AS wins_team2,
 AVG(CASE WHEN m.winner_team_id = m.team1_id THEN m.result_margin ELSE NULL END) AS avg_margin_team1_wins,
 AVG(CASE WHEN m.winner_team_id = m.team2_id THEN m.result_margin ELSE NULL END) AS avg_margin_team2_wins
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
WHERE date(m.match_date) >= date('now','-3 years')
GROUP BY m.team1_id, m.team2_id
HAVING COUNT(*) >= 5
""",
    "Q23 - Recent player form / last 10 performances": """
-- Q23 (requires ranking of last 10 innings per player)
WITH last_innings AS (
  SELECT pi.*,
         ROW_NUMBER() OVER (PARTITION BY pi.player_id ORDER BY m.match_date DESC) as rn
  FROM player_innings pi
  JOIN matches m ON pi.match_id = m.match_id
)
SELECT p.player_id, p.full_name,
 ROUND(AVG(CASE WHEN rn <= 5 THEN runs END),2) AS avg_last5,
 ROUND(AVG(CASE WHEN rn <= 10 THEN runs END),2) AS avg_last10,
 SUM(CASE WHEN rn <= 10 AND runs >= 50 THEN 1 ELSE 0 END) AS count_50s_last10
FROM last_innings li
JOIN players p ON p.player_id = li.player_id
WHERE rn <= 10
GROUP BY p.player_id
""",
    "Q24 - Best batting partnerships": """
-- Q24
SELECT p1.full_name AS batter_a, p2.full_name AS batter_b,
       COUNT(*) AS partnerships_count,
       ROUND(AVG(pr.runs),2) AS avg_partnership,
       SUM(CASE WHEN pr.runs > 50 THEN 1 ELSE 0 END) AS partnerships_above_50,
       MAX(pr.runs) AS highest_partnership
FROM partnerships pr
JOIN players p1 ON p1.player_id = pr.player_a_id
JOIN players p2 ON p2.player_id = pr.player_b_id
GROUP BY pr.player_a_id, pr.player_b_id
HAVING COUNT(*) >= 5
ORDER BY avg_partnership DESC
""",
    "Q25 - Time-series quarterly performance": """
-- Q25 (quarterly averages)
SELECT p.player_id, p.full_name,
 strftime('%Y', m.match_date) || '-Q' || (((strftime('%m',m.match_date)-1)/3)+1) AS quarter,
 ROUND(AVG(pi.runs),2) AS avg_runs, ROUND(AVG((pi.runs*100.0)/pi.balls),2) AS avg_sr,
 COUNT(DISTINCT m.match_id) AS matches_in_quarter
FROM player_innings pi
JOIN matches m ON pi.match_id = m.match_id
JOIN players p ON p.player_id = pi.player_id
GROUP BY p.player_id, quarter
HAVING matches_in_quarter >= 3
"""
}

choice = st.selectbox("Choose a query template", list(queries.keys()))
sql = st.text_area("SQL (editable)", value=queries[choice], height=220)
if st.button("Run SQL"):
    with get_conn() as conn:
        try:
            df = conn.execute(sql).fetchall()
            cols = [d[0] for d in conn.execute("PRAGMA table_info(players)").fetchall()] if df else []
            st.write("Rows:", len(df))
            # show as a simple table
            st.table(df)
        except Exception as e:
            st.error(f"SQL error: {e}")