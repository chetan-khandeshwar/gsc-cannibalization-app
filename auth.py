import streamlit as st

from streamlit_oauth import OAuth2Component

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly"
]


def google_login():

    oauth2 = OAuth2Component(
        st.secrets["GOOGLE_CLIENT_ID"],
        st.secrets["GOOGLE_CLIENT_SECRET"],
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token"
    )

    result = oauth2.authorize_button(
        "Login with Google",
        redirect_uri=st.query_params.get(
            "redirect_uri",
            ""
        ),
        scope=" ".join(SCOPES)
    )

    return result