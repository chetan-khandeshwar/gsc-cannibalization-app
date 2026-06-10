import streamlit as st

st.set_page_config(
    page_title="GSC Cannibalization Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 GSC Cannibalization Analyzer")

st.success("Streamlit Cloud deployment working")

try:

    client_id = st.secrets["GOOGLE_CLIENT_ID"]

    st.success("Google Client ID found in Streamlit Secrets")

    st.code(
        client_id[:25] + "..."
    )

except Exception as e:

    st.error(
        f"Secrets Error: {str(e)}"
    )