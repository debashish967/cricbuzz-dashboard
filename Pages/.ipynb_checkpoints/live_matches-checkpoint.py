# pages/live_matches.py
import streamlit as st
import sqlite3, os, re, time
import requests
from datetime import datetime

st.set_page_config(page_title="Live Matches (Free API)", layout="wide")

DB_PATH = os.path.abspath("cricbuzz.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Load API key
API_KEY = st.secrets.get("RAPIDAPI_KEY", None)
if not API_KEY:
    st.error("Missing RAPIDAPI_KEY in .streamlit/secrets.toml")
    st.stop()

LIVE_URL = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
HEADERS = {
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com",
    "x-rapidapi-key": API_KEY
}

def parse_status(status_text: str):
    """Parse winner, victory_type, victory_margin, is_complete from status string."""
    if not status_text:
        return "", "", None, 0
    s = status_text.strip()
    # winner + margin/type pattern: "India won by 4 wickets" / "Australia won by 23 runs"
    m = re.search(r"^(.*?)\s+won by\s+(\d+)\s+(wickets?|runs?)", s, flags=re.IGNORECASE)
    if m:
        winner = m.group(1).strip()
        margin = int(m.group(2))
        vtype = m.group(3).lower()
        return winner, ("wickets" if "wicket" in vtype else "runs"), margin, 1
    # other completed states
    for kw in ["tied", "tie", "draw", "drawn", "no result", "abandoned", "match over", "stumps"]:
        if kw in s.lower():
            return "", "", None, 1
    return "", "", None, 0

def to_int_or_none(x):
    try:
        return int(x)
    except:
        return None

def flatten_match(series_name: str, match_obj: dict):
    """Safely flatten one match record from the free live endpoint."""
    info = match_obj.get("matchInfo", {})
    teams1 = info.get("team1", {}) or {}
    teams2 = info.get("team2", {}) or {}
    venue = info.get("venueInfo", {}) or {}

    match_id = str(info.get("matchId", ""))
    team1 = teams1.get("teamName") or teams1.get("teamSName") or ""
    team2 = teams2.get("teamName") or teams2.get("teamSName") or ""
    status = info.get("status") or info.get("stateTitle") or info.get("statusText") or ""
    match_desc = info.get("matchDesc") or ""
    match_format = info.get("matchFormat") or info.get("matchType") or ""

    # Many feeds provide ms since epoch as string in 'startDate'; try a few keys
    start_ts = info.get("startDate") or info.get("startTime") or info.get("matchStartTimestamp")
    start_ts = to_int_or_none(start_ts)

    venue_name = venue.get("ground") or venue.get("name") or ""
    venue_city = venue.get("city") or ""
    venue_country = venue.get("country") or ""

    winner, victory_type, victory_margin, is_complete = parse_status(status)
    updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    return {
        "match_id": match_id,
        "series_name": series_name or "",
        "team1": team1,
        "team2": team2,
        "status": status,
        "match_desc": match_desc,
        "start_ts": start_ts,
        "venue_name": venue_name,
        "venue_city": venue_city,
        "venue_country": venue_country,
        "match_format": match_format,
        "winner": winner,
        "victory_type": victory_type,
        "victory_margin": victory_margin,
        "is_complete": is_complete,
        "updated_at": updated_at
    }

def fetch_live_matches():
    r = requests.get(LIVE_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

st.title("🏏 Live Matches (Free API)")

colA, colB = st.columns([1,1])
with colA:
    if st.button("🔄 Fetch Live Matches now"):
        try:
            data = fetch_live_matches()
            type_matches = data.get("typeMatches", [])
            rows = []
            for t in type_matches:
                # t example: {"matchType":"International", "seriesMatches":[...]}
                series_list = t.get("seriesMatches", [])
                for s in series_list:
                    adw = s.get("seriesAdWrapper", {}) or {}
                    series_name = adw.get("seriesName") or ""
                    matches = adw.get("matches", []) or []
                    for m in matches:
                        rows.append(flatten_match(series_name, m))

            # UPSERT into live_matches
            with get_conn() as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                sql = """
                INSERT INTO live_matches
                (match_id, series_name, team1, team2, status,
                 match_desc, start_ts, venue_name, venue_city, venue_country,
                 match_format, winner, victory_type, victory_margin, is_complete, updated_at)
                VALUES
                (:match_id, :series_name, :team1, :team2, :status,
                 :match_desc, :start_ts, :venue_name, :venue_city, :venue_country,
                 :match_format, :winner, :victory_type, :victory_margin, :is_complete, :updated_at)
                ON CONFLICT(match_id) DO UPDATE SET
                  series_name=excluded.series_name,
                  team1=excluded.team1,
                  team2=excluded.team2,
                  status=excluded.status,
                  match_desc=excluded.match_desc,
                  start_ts=excluded.start_ts,
                  venue_name=excluded.venue_name,
                  venue_city=excluded.venue_city,
                  venue_country=excluded.venue_country,
                  match_format=excluded.match_format,
                  winner=excluded.winner,
                  victory_type=excluded.victory_type,
                  victory_margin=excluded.victory_margin,
                  is_complete=excluded.is_complete,
                  updated_at=excluded.updated_at
                """
                conn.executemany(sql, rows)
                conn.commit()
            st.success(f"✅ Fetched & saved {len(rows)} matches.")
        except requests.HTTPError as e:
            st.error(f"HTTP error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

with colB:
    st.caption("Shows what’s currently stored in the DB")
    with get_conn() as conn:
        df = conn.execute("""
            SELECT match_id, series_name, team1, team2, status, match_format,
                   venue_city, updated_at
            FROM live_matches
            ORDER BY COALESCE(start_ts, 0) DESC, series_name
            LIMIT 50
        """).fetchall()
    if df:
        st.write("Latest 50:")
        st.table(df)
    else:
        st.info("No rows yet. Click the fetch button.")