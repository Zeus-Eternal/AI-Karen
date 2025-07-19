from datetime import datetime

import pytest

# Skip tests if ``streamlit.testing`` is unavailable
pytest.importorskip("streamlit.testing.v1", reason="streamlit not installed")
from streamlit.testing.v1 import AppTest
import streamlit as st

from ui_launchers.streamlit_ui.helpers import (
    render_message,
    render_typing_indicator,
    render_export_modal,
)


def test_render_message_runs():
    def app():
        render_message({"role": "assistant", "content": "hi", "timestamp": datetime.now(), "attachments": []})

    at = AppTest.from_function(app)
    at.run()
    assert at.exception is None


def test_render_typing_indicator_runs():
    def app():
        render_typing_indicator(True)

    at = AppTest.from_function(app)
    at.run()
    assert at.exception is None


def test_render_export_modal_runs():
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "hi", "timestamp": datetime.now(), "attachments": []}
    ]
    st.session_state.show_export_modal = True

    def app():
        render_export_modal()

    at = AppTest.from_function(app)
    at.run()
    assert at.exception is None
