import streamlit as st
import sqlite3
import os

st.title("📺 Live Display (from DB)")

DB_PATH = os.path.abspath("cricbuzz.db")

# ✅ Ensure table exists
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS live_matches (
        match_id TEXT PRIMARY KEY,
        series_name TEXT,
        team1 TEXT,
        team2 TEXT,
        status TEXT
    )
    """)
    conn.commit()

def get_conn():
    return sqlite3.connect(DB_PATH)

with get_conn() as conn:
    rows = conn.execute("""
        SELECT series_name, team1, team2, status 
        FROM live_matches 
        ORDER BY series_name, team1
    """).fetchall()

if not rows:
    st.warning("No data yet — go to 'Live Matches' and click 'Fetch Live Matches'.")
else:
    st.success(f"Found {len(rows)} matches in DB.")
    st.dataframe(rows)