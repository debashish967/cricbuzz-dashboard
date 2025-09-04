# pages/crud_operations.py
import streamlit as st
import sqlite3, os

st.set_page_config(page_title="CRUD Operations", layout="wide")
DB_PATH = os.path.abspath("cricbuzz.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

st.title("🛠 CRUD — Manage live_matches (safe demo)")

# Show current rows
with get_conn() as conn:
    rows = conn.execute("SELECT match_id, series_name, team1, team2, status FROM live_matches ORDER BY COALESCE(start_ts,0) DESC").fetchall()

st.subheader("Current rows")
if rows:
    st.dataframe(rows)
else:
    st.info("No matches in DB yet.")

st.markdown("---")
st.subheader("Add a new match (demo)")

with st.form("add_match"):
    new_id = st.text_input("Match ID (unique)")
    series = st.text_input("Series name")
    t1 = st.text_input("Team 1")
    t2 = st.text_input("Team 2")
    status = st.text_input("Status")
    submitted = st.form_submit_button("Add match")
    if submitted:
        if not new_id:
            st.error("Match ID is required.")
        else:
            with get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO live_matches
                    (match_id, series_name, team1, team2, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (new_id, series, t1, t2, status))
                conn.commit()
            st.success("Added/Updated match.")

st.markdown("---")
st.subheader("Edit / Delete an existing match")
with get_conn() as conn:
    choices = [r[0] for r in conn.execute("SELECT match_id FROM live_matches").fetchall()]

if choices:
    sel = st.selectbox("Select match_id to edit", choices)
    if sel:
        with get_conn() as conn:
            r = conn.execute("SELECT match_id, series_name, team1, team2, status FROM live_matches WHERE match_id=?", (sel,)).fetchone()
        if r:
            with st.form("edit_match"):
                series = st.text_input("Series name", value=r[1])
                t1 = st.text_input("Team 1", value=r[2])
                t2 = st.text_input("Team 2", value=r[3])
                status = st.text_input("Status", value=r[4])
                update_btn = st.form_submit_button("Update")
                delete_btn = st.form_submit_button("Delete")
                if update_btn:
                    with get_conn() as conn:
                        conn.execute("""
                            UPDATE live_matches
                            SET series_name=?, team1=?, team2=?, status=?, updated_at=datetime('now')
                            WHERE match_id=?
                        """, (series, t1, t2, status, sel))
                        conn.commit()
                    st.success("Updated.")
                if delete_btn:
                    with get_conn() as conn:
                        conn.execute("DELETE FROM live_matches WHERE match_id=?", (sel,))
                        conn.commit()
                    st.success("Deleted.")
else:
    st.info("No rows to edit/delete yet.")