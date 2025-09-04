# pages/scorecard.py
import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Scorecard", layout="wide")

DB_PATH = os.path.abspath("cricbuzz.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fmt_time(ts):
    """Format timestamp (milliseconds or seconds) to human readable string."""
    if not ts:
        return "N/A"
    try:
        t = int(ts)
        # if it looks like milliseconds (>= 10^12), treat as ms
        if t > 1_000_000_000_000:
            return datetime.utcfromtimestamp(t / 1000).strftime("%d %b %Y, %H:%M UTC")
        else:
            return datetime.utcfromtimestamp(t).strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return str(ts)

# CSS: page gradient + white cards + dark readable fonts + badges
st.markdown("""
<style>
/* page background: purple → yellow gradient */
.page-bg {
  background: linear-gradient(135deg, #6a1b9a 0%, #fdd835 100%);
  padding: 18px;
  border-radius: 10px;
}

/* scorecard card */
.scorecard-box {
  background: rgba(255,255,255,0.96);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: 2px 6px 20px rgba(0,0,0,0.15);
  border: 2px solid transparent;
  background-clip: padding-box, border-box;
  background-origin: border-box;
  background-image: linear-gradient(white, white), linear-gradient(135deg, #6a1b9a, #fdd835);
}

/* match meta info */
.match-meta {
  font-size: 16px;
  color: #e65100;       /* dark orange */
  font-weight: 700;
  margin-bottom: 6px;
}

/* team blocks */
.team-block {
  background: linear-gradient(90deg, rgba(255,255,255,0.95), rgba(250,250,250,0.95));
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 2px solid transparent;
  background-clip: padding-box, border-box;
  background-origin: border-box;
  background-image: linear-gradient(white, white), linear-gradient(135deg, #6a1b9a, #fdd835);
}
.team-name {
  font-size: 20px;
  font-weight: 800;
  color: #e65100;       /* orange */
}
.team-score {
  font-size: 20px;
  font-weight: 800;
  color: #1a237e;       /* dark navy for numbers */
}

/* badges */
.badge {
  display:inline-block;
  padding:6px 12px;
  border-radius:12px;
  font-weight:700;
  color:#fff;
}
.status-badge { background:#ef6c00; }  /* orange */
.winner-badge { background:#2e7d32; } /* green */

/* match status */
.match-status {
  font-size: 16px;
  font-weight: 700;
  color: #b71c1c;       /* deep red */
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid transparent;
  background-clip: padding-box, border-box;
  background-origin: border-box;
  background-image: linear-gradient(white, white), linear-gradient(135deg, #6a1b9a, #fdd835);
}
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="page-bg">', unsafe_allow_html=True)

st.title("🏏 Live Scorecard — (Free API / DB view)")

# Fetch matches (try to order by start_ts if present; fallback to simple select)
with get_conn() as conn:
    try:
        cur = conn.execute("SELECT * FROM live_matches ORDER BY COALESCE(start_ts, 0) DESC LIMIT 200")
    except Exception:
        cur = conn.execute("SELECT * FROM live_matches LIMIT 200")
    cols = [d[0] for d in cur.description]
    matches = [dict(zip(cols, r)) for r in cur.fetchall()]

if not matches:
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("No matches found in the DB. Go to Live Matches and click 'Fetch Live Matches now' or add demo rows in CRUD.")
    st.stop()

# Build options list (label -> row dict)
options = []
for m in matches:
    series = m.get("series_name") or "Series N/A"
    t1 = m.get("team1") or "Team1"
    t2 = m.get("team2") or "Team2"
    status = m.get("status") or ""
    label = f"{series} — {t1} vs {t2} ({status or 'Status N/A'})"
    options.append((label, m))

labels = [o[0] for o in options]
choice_label = st.selectbox("Select a match", labels)
# find chosen row
chosen = next((r for lbl, r in options if lbl == choice_label), None)
if not chosen:
    st.warning("Selected match not found.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Extract commonly used fields with safe fallbacks
match_id = chosen.get("match_id") or chosen.get("matchId") or ""
series_name = chosen.get("series_name") or chosen.get("seriesName") or ""
team1 = chosen.get("team1") or ""
team2 = chosen.get("team2") or ""
status = chosen.get("status") or ""
match_desc = chosen.get("match_desc") or chosen.get("matchDesc") or ""
start_ts = chosen.get("start_ts") or chosen.get("startDate") or chosen.get("startTime")
venue_name = chosen.get("venue_name") or chosen.get("venue") or ""
venue_city = chosen.get("venue_city") or ""
match_format = chosen.get("match_format") or chosen.get("matchFormat") or ""
winner = chosen.get("winner") or ""
victory_type = chosen.get("victory_type") or ""
victory_margin = chosen.get("victory_margin") or None

# Header card (white card on top of gradient)
st.markdown('<div class="scorecard-box">', unsafe_allow_html=True)

# Top row: series + meta on left, quick metrics on right
left_col, right_col = st.columns([3,1])

with left_col:
    st.markdown(f'<div class="match-meta"><b>Series:</b> {series_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="match-meta"><b>Format:</b> {match_format or "N/A"}  |  <b>Match:</b> {match_desc or "N/A"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="match-meta"><b>Venue:</b> {venue_name or "Unknown"} {("(" + venue_city + ")") if venue_city else ""}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="match-meta"><b>Start:</b> {fmt_time(start_ts)}</div>', unsafe_allow_html=True)

with right_col:
    # Status badge
    if status:
        st.markdown(f'<div class="badge status-badge">{status}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="match-status">Status: N/A</div>', unsafe_allow_html=True)
    st.write("")  # spacing
    if winner:
        wt = f"{winner}"
        if victory_type and victory_margin is not None:
            wt += f" • {victory_type.capitalize()} {victory_margin}"
        st.markdown(f'<div style="margin-top:8px"><span class="badge winner-badge">Winner: {wt}</span></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close header card

# Main area: team blocks + optional team totals (from match_score)
st.markdown('<div class="scorecard-box">', unsafe_allow_html=True)

# Fetch team-level totals from match_score table if available
with get_conn() as conn:
    try:
        rows = conn.execute("SELECT team_name, runs, wickets, overs FROM match_score WHERE match_id = ?", (match_id,)).fetchall()
    except Exception:
        rows = []

# Prepare values for two teams (display N/A if missing)
team1_score = "N/A"
team2_score = "N/A"
if rows:
    # rows might not be ordered; map by team_name
    score_map = {r[0]: {"runs": r[1], "wickets": r[2], "overs": r[3]} for r in rows}
    t1_stats = score_map.get(team1)
    t2_stats = score_map.get(team2)
    if t1_stats:
        team1_score = f"{t1_stats.get('runs','0')}/{t1_stats.get('wickets','0')} in {t1_stats.get('overs','0')}"
    if t2_stats:
        team2_score = f"{t2_stats.get('runs','0')}/{t2_stats.get('wickets','0')} in {t2_stats.get('overs','0')}"
else:
    # no match_score rows
    pass

# Two columns: left for teams, right for quick info or placeholder (like charts in future)
col_a, col_b = st.columns([3,2])

with col_a:
    # Team 1 block
    st.markdown(f"""
    <div class="team-block">
       <div>
         <div class="team-name">{team1}</div>
         <div style="font-size:13px;color:#444;">Team 1</div>
       </div>
       <div style="text-align:right;">
         <div class="team-score">{team1_score}</div>
       </div>
    </div>
    """, unsafe_allow_html=True)

    # Team 2 block
    st.markdown(f"""
    <div class="team-block">
       <div>
         <div class="team-name">{team2}</div>
         <div style="font-size:13px;color:#444;">Team 2</div>
       </div>
       <div style="text-align:right;">
         <div class="team-score">{team2_score}</div>
       </div>
    </div>
    """, unsafe_allow_html=True)

    # If there were detailed batting/bowling (player_stats), we can show a small message or a table.
    with get_conn() as conn:
        try:
            bat_rows = conn.execute("SELECT player_name, runs, balls FROM player_stats WHERE match_id = ? AND role = 'Batsman' LIMIT 10", (match_id,)).fetchall()
        except Exception:
            bat_rows = []
    if bat_rows:
        st.markdown("**Top batting snippets (sample):**")
        df_bat = pd.DataFrame(bat_rows, columns=["Player", "R", "B"])
        st.dataframe(df_bat)
    else:
        st.info("Player-level stats are not available for this match (free API). For demo, add rows via CRUD or use paid API.")

with col_b:
    # Quick stats card
    st.markdown('<div style="padding:10px;border-radius:10px;background:#fff;">', unsafe_allow_html=True)
    st.markdown(f"<div style='font-weight:700;color:#111;'>Match ID</div><div style='margin-bottom:8px'>{match_id or 'N/A'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-weight:700;color:#111;'>Series</div><div style='margin-bottom:8px'>{series_name or 'N/A'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-weight:700;color:#111;'>Status</div><div style='margin-bottom:8px'>{status or 'N/A'}</div>", unsafe_allow_html=True)
    if winner:
        st.markdown(f"<div style='font-weight:700;color:#111;'>Winner</div><div style='margin-bottom:8px'>{winner}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close main area card
st.markdown('</div>', unsafe_allow_html=True)  # close page-bg container