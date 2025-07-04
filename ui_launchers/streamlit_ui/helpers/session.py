import streamlit as st

def get_user_context():
    # This would actually call src/ui/hooks/auth.py for prod
    # Here, mimic demo user for framework wiring
    if "user_ctx" not in st.session_state:
        st.session_state["user_ctx"] = {
            "user_id": "zeus",
            "name": "God Zeus",
            "roles": ["admin", "user", "devops", "analyst"],
            "session_token": "demo-token"
        }
    return st.session_state["user_ctx"]
