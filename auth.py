
Notice the triple backticks (` ``` `).

Those backticks are NOT Python code and will cause exactly the error shown in your logs. :contentReference[oaicite:1]{index=1}

Your entire `auth.py` should be EXACTLY this and nothing else:

```python
import streamlit as st

from streamlit_oauth import OAuth2Component

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly"
]

REDIRECT_URI = (
    "https://gsc-cannibalization-app-7mi43bptxgtjaajeeanxhp.streamlit.app"
)


def google_login():

    oauth2 = OAuth2Component(
        st.secrets["GOOGLE_CLIENT_ID"],
        st.secrets["GOOGLE_CLIENT_SECRET"],
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token"
    )

    result = oauth2.authorize_button(
        "Login with Google",
        redirect_uri=REDIRECT_URI,
        scope=" ".join(SCOPES)
    )

    return result