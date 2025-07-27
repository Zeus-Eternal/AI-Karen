import streamlit as st
from pages.user_management import (
    get_current_user_from_context,
    render_login_interface,
)
from services.user_service import rbac_service, User


def render_profile_page(user_ctx=None):
    """Display and edit the current user's profile."""

    current_user = get_current_user_from_context(user_ctx)
    if not current_user:
        render_login_interface()
        return

    st.markdown("# 👤 Profile")
    st.markdown("### View and edit your personal details")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Username:** {current_user.username}")
        st.write(f"**Email:** {current_user.email}")
        st.write(f"**Full Name:** {current_user.full_name}")
        st.write(f"**Role:** {current_user.role.value.title()}")
        last_login = (
            current_user.last_login.strftime("%Y-%m-%d %H:%M")
            if current_user.last_login
            else "Never"
        )
        st.write(f"**Last Login:** {last_login}")

    with col2:
        stats = rbac_service.get_user_activity(current_user)
        st.metric("Active Sessions", stats["sessions"])
        st.metric("Memory Events", stats["memory_events"])
        st.metric("Plugin Calls", stats["plugin_invocations"])

    st.markdown("---")
    st.markdown("### ✏️ Edit Profile")
    with st.form("edit_profile_form"):
        new_username = st.text_input("New Username", value=current_user.username)
        new_email = st.text_input("Email", value=current_user.email)
        new_full_name = st.text_input("Full Name", value=current_user.full_name)
        new_password = st.text_input(
            "New Password", type="password", placeholder="Leave blank to keep current"
        )

        if st.form_submit_button("Save Changes", type="primary"):
            try:
                rbac_service.update_user_credentials(
                    current_user,
                    username=(
                        new_username if new_username != current_user.username else None
                    ),
                    password=new_password or None,
                    email=(new_email if new_email != current_user.email else None),
                    full_name=(
                        new_full_name
                        if new_full_name != current_user.full_name
                        else None
                    ),
                )
                st.success(
                    "Profile updated! Please log in again if username or password changed."
                )
                st.session_state.current_user = current_user
            except Exception as e:
                st.error(f"Failed to update profile: {e}")
