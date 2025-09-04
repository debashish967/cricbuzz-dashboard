# pages/top_stats.py
import streamlit as st
import pandas as pd
from utils.db_connection import get_engine

st.title("📊 Top Stats")

engine = get_engine()

st.write("Fetching sample data from DB...")

# Try to read data
try:
    df = pd.read_sql("SELECT * FROM matches", engine)
    st.dataframe(df)
except Exception:
    st.info("No matches table yet. Add data to DB first.")