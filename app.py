import streamlit as st

from auth import google_login

st.set_page_config(
    page_title="GSC Cannibalization Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title(
    "📊 GSC Cannibalization Analyzer"
)

result = google_login()

if result:

    st.success(
        "Google Login Successful"
    )

    st.json(result)