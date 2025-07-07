"""
Streamlit IoT Device/Config Page
- Visualizes, manages, and configures IoT nodes, sensors, and device automations.
- RBAC: Only 'admin' or 'iot_manager' can edit devices/config.
- Auto-discovers device schemas via core API.
"""

import streamlit as st
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import fetch_org_settings, update_org_settings, fetch_announcements

def render_iot_dashboard(user_ctx):
    st.title("IoT Device Management")
    org_id = user_ctx.get("org_id", "default")
    can_edit = require_roles(user_ctx, ["admin", "iot_manager"])

    st.info(f"Active Org: `{org_id}`. {'Edit enabled' if can_edit else 'View only'}")

    # Fetch IoT config/settings (replace with actual IoT API call if available)
    settings = fetch_org_settings(org_id)
    iot_config = settings.get("iot_config", {})

    # Display current config
    st.subheader("Current IoT Config")
    st.json(iot_config if iot_config else {"message": "No IoT config found for this org."})

    # Edit mode (admins/managers)
    if can_edit:
        st.subheader("Update IoT Config")
        new_config = st.text_area(
            "Paste new IoT config (JSON)", 
            value=st.session_state.get("iot_config_json", ""),
            height=300
        )
        if st.button("Save IoT Config"):
            try:
                import json
                parsed = json.loads(new_config)
                update_org_settings(org_id, {**settings, "iot_config": parsed})
                st.success("IoT config updated successfully.")
                st.session_state["iot_config_json"] = new_config
            except Exception as ex:
                st.error(f"Failed to update: {ex}")

    # Show announcements (IoT-related)
    st.subheader("IoT Announcements & Logs")
    announcements = fetch_announcements(limit=10)
    for a in announcements:
        if "iot" in str(a).lower():
            st.markdown(f"**[{a.get('timestamp', 'N/A')}]** {a.get('message', '')}")

def render(user_ctx=None):
    if user_ctx is None:
        st.warning("No user context. Please login.")
        return
    render_iot_dashboard(user_ctx)

# Streamlit expects a callable for page loading
if __name__ == "__main__":
    import json
    # Evil fallback: Dev stub user context for direct run/testing
    user_ctx = {
        "user_id": "evil_admin",
        "org_id": "default",
        "roles": ["admin", "iot_manager"]
    }
    render(user_ctx)
