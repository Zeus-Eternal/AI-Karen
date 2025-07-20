"""Helper functions for rendering chat UI components."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text()


def render_message(message: dict) -> None:
    """Render a single chat ``message`` using the HTML templates."""
    timestamp = message.get("timestamp", datetime.now()).strftime("%H:%M")
    template = "message_user.html" if message.get("role") == "user" else "message_assistant.html"
    st.markdown(
        _load_template(template).format(content=message["content"], timestamp=timestamp),
        unsafe_allow_html=True,
    )
    if message.get("attachments"):
        for attachment in message["attachments"]:
            st.markdown(f"📎 {attachment['name']} ({attachment['size']})")


def render_typing_indicator(show: bool) -> None:
    """Render the typing indicator when ``show`` is ``True``."""
    if show:
        st.markdown(_load_template("typing_indicator.html"), unsafe_allow_html=True)


def render_export_modal() -> None:
    """Render the export modal and handle export actions."""
    with st.expander("📤 Export Conversation", expanded=True):
        st.markdown(_load_template("export_modal.md"))
        col1, col2, col3 = st.columns(3)

        if col1.button("📄 Export as Text"):
            export_text = "AI Karen Conversation Export\n" + "=" * 40 + "\n\n"
            for msg in st.session_state.chat_messages:
                role = "You" if msg["role"] == "user" else "AI Karen"
                ts = msg.get("timestamp", datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                export_text += f"[{ts}] {role}: {msg['content']}\n\n"
            col1.download_button(
                label="💾 Download Text File",
                data=export_text,
                file_name=f"ai_karen_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
            )

        if col2.button("📊 Export as JSON"):
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "conversation_length": len(st.session_state.chat_messages),
                "messages": [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "timestamp": m.get("timestamp", datetime.now()).isoformat(),
                        "attachments": m.get("attachments", []),
                    }
                    for m in st.session_state.chat_messages
                ],
            }
            col2.download_button(
                label="💾 Download JSON File",
                data=json.dumps(export_data, indent=2),
                file_name=f"ai_karen_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

        if col3.button("📋 Copy to Clipboard"):
            st.info(
                "📋 Copy functionality would be implemented with JavaScript in a full deployment"
            )

        if st.button("❌ Close Export"):
            st.session_state.show_export_modal = False
            st.rerun()
