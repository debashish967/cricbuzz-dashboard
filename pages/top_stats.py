import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Top Cricket Stats", layout="wide")

st.title("📊 Top Cricket Stats Dashboard")

# --- Sample Data ---
# Mock "Top Batsmen"
batsmen_data = pd.DataFrame({
    "Player": ["Virat Kohli", "Babar Azam", "Rohit Sharma", "Steve Smith", "Kane Williamson"],
    "Runs": [12876, 9802, 10754, 9513, 9401],
    "Average": [57.3, 54.6, 48.5, 50.1, 47.8],
    "Centuries": [46, 25, 31, 28, 27]
})

# Mock "Top Bowlers"
bowlers_data = pd.DataFrame({
    "Player": ["Jasprit Bumrah", "Mitchell Starc", "Shaheen Afridi", "Rashid Khan", "Trent Boult"],
    "Wickets": [217, 210, 178, 180, 195],
    "Average": [24.6, 26.1, 27.4, 21.5, 25.7],
    "Economy": [4.5, 4.9, 5.2, 4.1, 4.8]
})

# --- Layout with columns ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏏 Top 5 Batsmen (ODI)")
    st.dataframe(batsmen_data, use_container_width=True)

    # Bar Chart for Runs
    fig, ax = plt.subplots()
    batsmen_data.plot(x="Player", y="Runs", kind="bar", ax=ax, legend=False, color="orange")
    ax.set_ylabel("Runs")
    ax.set_title("Runs by Top Batsmen")
    st.pyplot(fig)

with col2:
    st.subheader("🔥 Top 5 Bowlers (ODI)")
    st.dataframe(bowlers_data, use_container_width=True)

    # Bar Chart for Wickets
    fig, ax = plt.subplots()
    bowlers_data.plot(x="Player", y="Wickets", kind="bar", ax=ax, legend=False, color="purple")
    ax.set_ylabel("Wickets")
    ax.set_title("Wickets by Top Bowlers")
    st.pyplot(fig)

# --- Extra Stats ---
st.subheader("📈 Additional Insights")
st.write("✔️ Virat Kohli leads in runs with 12,876 ODI runs.")
st.write("✔️ Jasprit Bumrah has the best bowling economy among the top bowlers.")