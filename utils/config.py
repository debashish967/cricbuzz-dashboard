import streamlit as st

def get_api_key():
    return st.secrets.get("RAPIDAPI_KEY", "")