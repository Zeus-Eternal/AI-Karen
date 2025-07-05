"""
Kari Home Page - Role-Aware, Self-Updating, Ultra-Responsive
- Features: RBAC quick-links, dynamic widgets, onboarding modal, fast telemetry
- Relies on: ui_logic.components, ui_logic.config, ui_logic.hooks
- All business logic lives in ui_logic. This file is glue only.
"""

import streamlit as st
from ui_logic.hooks.auth import get_user_context
from ui_logic.hooks.rbac import user_has_role
from ui_logic.config.branding import get_branding_config
from ui_logic.utils.api import fetch_announcements
from ui_logic.components.memory.profile_panel import render_profile_panel
from ui_logic.components.analytics.chart_builder import render_quick_charts
from ui_logic.components.admin.system_status import render_system_status

def render_welcome(user_ctx, branding):
    st.markdown(
        f"""
        <div style='padding:1.3em 0 0.7em 0'>
            <h1 style='color:{branding.get('accent', '#bb00ff')};margin-bottom:0'>
                {branding.get('title', 'Kari AI')}
            </h1>
            <span style='font-size:1.2em;color:{branding.get('accent', '#bb00ff')};'>
                {branding.get('subtitle', 'Unstoppable Autonomous Assistant')}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_announcements():
    ann = fetch_announcements(limit=3)
    if ann:
        st.info("**Latest Announcements**")
        for a in ann:
            st.markdown(f"- `{a['date']}`: {a['title']} &mdash; {a['summary']}")
    else:
        st.info("No current announcements.")

def render_onboarding(user_ctx):
    # Show onboarding only if flagged as needed in user_ctx/profile
    if user_ctx.get("needs_onboarding"):
        from ui_logic.components.memory.profile_panel import render_onboarding_wizard
        render_onboarding_wizard(user_ctx=user_ctx)

def render_shortcuts(user_ctx):
    st.markdown("### Quick Access")
    cols = st.columns(4)
    pages = [
        {"label": "Chat", "icon": "💬", "page": "chat", "roles": ["user", "admin", "dev"]},
        {"label": "Memory", "icon": "🧠", "page": "memory", "roles": ["user", "admin"]},
        {"label": "Analytics", "icon": "📊", "page": "analytics", "roles": ["admin", "dev"]},
        {"label": "Plugins", "icon": "🧩", "page": "plugins", "roles": ["dev", "admin"]},
        {"label": "IoT", "icon": "📡", "page": "iot", "roles": ["dev", "admin"]},
        {"label": "Task Manager", "icon": "✅", "page": "task_manager", "roles": ["admin", "dev"]},
        {"label": "Admin", "icon": "🛡️", "page": "admin", "roles": ["admin"]},
        {"label": "Settings", "icon": "⚙️", "page": "settings", "roles": ["user", "admin", "dev"]},
    ]
    idx = 0
    for p in pages:
        if any(user_has_role(user_ctx, role) for role in p["roles"]):
            with cols[idx % len(cols)]:
                st.button(f"{p['icon']} {p['label']}", key=f"nav_{p['page']}", on_click=lambda pg=p["page"]: st.experimental_set_query_params(page=pg))
            idx += 1

def render_profile(user_ctx):
    with st.expander("👤 Profile & Preferences", expanded=False):
        render_profile_panel(user_ctx=user_ctx)

def render_home_page():
    st.set_page_config(page_title="Kari Home", layout="wide")
    user_ctx = get_user_context()
    branding = get_branding_config()

    render_welcome(user_ctx, branding)
    render_onboarding(user_ctx)
    render_announcements()
    render_shortcuts(user_ctx)
    render_profile(user_ctx)

    # Show system status if admin
    if user_has_role(user_ctx, "admin"):
        st.markdown("---")
        render_system_status()

    # Quick analytics preview for power-users/devs
    if user_has_role(user_ctx, "dev"):
        st.markdown("---")
        st.markdown("#### Live Analytics Snapshot")
        render_quick_charts()

# Entry point for Streamlit
if __name__ == "__main__":
    render_home_page()
