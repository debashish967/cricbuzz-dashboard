# pages/home.py
import streamlit as st
import sqlite3, os
from datetime import datetime

st.set_page_config(page_title="Home - Cricbuzz Live Stats", layout="wide")

DB_PATH = os.path.abspath("cricbuzz.db")
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

st.title("🏏 Cricbuzz Live Stats — Home")
st.write("Welcome — this dashboard shows live matches from the free Cricbuzz feed. Use the sidebar to navigate.")

# Summary metrics
with get_conn() as conn:
    try:
        count = conn.execute("SELECT COUNT(*) FROM live_matches").fetchone()[0]
        last_update = conn.execute("SELECT MAX(updated_at) FROM live_matches").fetchone()[0]
    except Exception:
        count = 0
        last_update = None

col1, col2 = st.columns(2)
col1.metric("Matches stored", count)
col2.write("Last update (UTC)")
col2.write(last_update or "N/A")

st.markdown("---")
st.subheader("Quick tips")
st.write("""
- Go to **Live Matches** and click **Fetch Live Matches now** to populate new data.  
- Use **Scorecard** to view detailed info for each match (limited to free-plan fields).  
- Use **CRUD Operations** to add or edit rows for demo/testing.
""")