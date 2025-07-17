import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from ui_logic.pages.presence import page as presence_logic
from helpers.session import get_user_context
from ai_karen_engine.event_bus import get_event_bus


def render(user_ctx=None):
    """Render Presence Monitor with live event feed."""
    user_ctx = user_ctx or get_user_context()
    st.title("👥 Presence Monitor")
    st_autorefresh(interval=3000, key="presence_refresh")

    if st.button("Generate Test Event"):
        get_event_bus().publish(
            capsule="demo",
            event_type="heartbeat",
            payload={"ts": time.time()},
        )

    events = presence_logic(user_ctx=user_ctx)
    if not events:
        st.info("No recent presence events.")
    else:
        for ev in events:
            with st.expander(f"{ev['capsule']} | {ev['type']}"):
                st.json(ev)


if __name__ == "__main__":
    render()
