# pages/sql_free_api.py
import streamlit as st
import sqlite3, os
import pandas as pd

st.set_page_config(page_title="SQL (Free API Queries)", layout="wide")
DB_PATH = os.path.abspath("cricbuzz.db")
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

st.title("SQL — Free API supported queries")
# Q2 (Matches in last 30 days) ⚡ Modified:
# We don’t have start_ts, so we’ll just show matches with status containing “won” or “opt to”.
QUERIES = {
    "Q2: Matches in last 30 days (requires start_ts,We don’t have start_ts, so we’ll just show matches with status containing “won” or “opt to”.)": """
SELECT series_name, team1, team2, status
FROM live_matches
WHERE status LIKE '%won%' OR status LIKE '%opt%'
ORDER BY match_id DESC;
""",
# Q5 (Wins per team) ⚡ Modified:
# Parse status text for winners.    
    "Q5: Wins per team (from parsed winner, Parse status text for winners.)": """
SELECT team, COUNT(*) as wins
FROM (
    SELECT
        CASE
            WHEN status LIKE team1 || ' won%' THEN team1
            WHEN status LIKE team2 || ' won%' THEN team2
        END as team
    FROM live_matches
) WHERE team IS NOT NULL
GROUP BY team
ORDER BY wins DESC;
""",

# Q10 (Last 20 completed matches) ⚡ Modified:
# We’ll call any match with “won” in status = completed.
    "Q10: Last 20 completed matches,We’ll call any match with “won” in status = completed.": """
SELECT match_id, series_name, team1, team2, status
FROM live_matches
WHERE status LIKE '%won%'
ORDER BY match_id DESC
LIMIT 20;
""",
# Q22 (Head-to-Head partial) ⚡ Modified:
# Pair counts + wins (parses winner from status)
# Counts matches and counts wins for each side when status contains pattern like "TeamName won ...".

    "Q22: Head-to-head (partial, last 3 years, We can only group by teams.)": """
-- Head-to-head with parsed wins (uses pattern "X won ...")
SELECT
  tA || ' vs ' || tB AS pair,
  COUNT(*) AS matches_played,
  SUM(CASE WHEN winner = tA THEN 1 ELSE 0 END) AS wins_tA,
  SUM(CASE WHEN winner = tB THEN 1 ELSE 0 END) AS wins_tB
FROM (
  SELECT
    CASE WHEN team1 < team2 THEN team1 ELSE team2 END AS tA,
    CASE WHEN team1 < team2 THEN team2 ELSE team1 END AS tB,
    CASE
      WHEN status LIKE team1 || ' won%' THEN team1
      WHEN status LIKE team2 || ' won%' THEN team2
      ELSE NULL
    END AS winner
  FROM live_matches
)
GROUP BY tA, tB
HAVING COUNT(*) >= 1
ORDER BY matches_played DESC;
""",
    "Utility: Show latest rows": """
SELECT match_id, series_name, team1, team2, status,
       winner, victory_type, victory_margin, datetime(start_ts/1000, 'unixepoch') AS start_utc, venue_city
FROM live_matches
ORDER BY COALESCE(start_ts,0) DESC
LIMIT 200
"""
}

choice = st.selectbox("Choose a query", list(QUERIES.keys()))
sql = QUERIES[choice]
st.code(sql, language="sql")

if st.button("Run query"):
    with get_conn() as conn:
        try:
            df = pd.read_sql_query(sql, conn)
            st.write(f"Rows: {len(df)}")
            if df.empty:
                st.warning("Query returned no rows. This often means required fields (like start_ts or winner) are missing for current live data.")
            else:
                st.dataframe(df)
        except Exception as e:
            st.error(f"SQL error: {e}")