"""
Kari Profile Panel (Production)
- Real-time persona/profile management & analytics
- Local-first: Milvus, DuckDB, Redis, MemoryManager stack
- RBAC: user (edit self), admin (all), analyst (read-only)
- Full audit, meta, memory stats, danger zone
"""

import streamlit as st
import pandas as pd
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps

from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_user_profile,
    save_user_profile,
    fetch_audit_logs
)

# Optional: For local-first ops—try/catch if logic.* not present
try:
    from ui_logic.components.memory.memory_manager import (
        get_active_profile,
        update_profile_field,
        get_profile_history,
        get_embedding_score,
        recalc_persona_metrics,
        reset_profile,
        flush_short_term,
        flush_long_term
    )
    from config.config_manager import load_config
    HAS_LOCAL = True
except ImportError:
    HAS_LOCAL = False

logger = logging.getLogger("kari.ui.profile_panel")
logger.setLevel(logging.INFO)

class ProfilePanelError(Exception): pass

def log_profile_op(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            logger.info(f"{func.__name__} executed", extra={"user_ctx": kwargs.get("user_ctx", {})})
            return res
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}", exc_info=True)
            raise
    return wrapper

def parse_preferences(pref_val: Any) -> dict:
    import json
    if isinstance(pref_val, dict):
        return pref_val
    try:
        return json.loads(pref_val)
    except Exception:
        return {}

@log_profile_op
def load_profile(user_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Loads the current profile for given user context (local-first, then API).
    """
    user_id = user_ctx.get("user_id")
    # Prefer local logic if available (power-user mode)
    if HAS_LOCAL:
        profile = get_active_profile(user_id)
        if profile:
            return profile
    # Fallback to API
    data = fetch_user_profile(user_id)
    if not data or "error" in data:
        raise ProfilePanelError(data.get("error", "Profile not found."))
    return data.get("result", data)

@log_profile_op
def save_profile(user_ctx: Dict[str, Any], update: Dict[str, Any]) -> bool:
    """
    Save profile (local-first if available).
    """
    user_id = user_ctx.get("user_id")
    if HAS_LOCAL:
        for k, v in update.items():
            update_profile_field(user_id, k, v)
        recalc_persona_metrics(user_id)
        return True
    # Fallback: API save
    out = save_user_profile(user_id, update)
    if not out.get("success", True):
        raise ProfilePanelError(out.get("error", "Failed to save profile."))
    return True

def render_profile_history(user_id: str):
    """Render profile change history table if available"""
    if HAS_LOCAL:
        history = get_profile_history(user_id)
        if history:
            df = pd.DataFrame(history)
            st.markdown("#### 🕒 Profile Change History")
            st.dataframe(df.style.format({"timestamp": "{:%Y-%m-%d %H:%M:%S}"}), hide_index=True, use_container_width=True)
        else:
            st.info("No profile change history yet.")

def render_persona_metrics(user_id: str):
    """Render persona embedding & metrics (local-first)"""
    if HAS_LOCAL:
        embed_score = get_embedding_score(user_id)
        metrics = recalc_persona_metrics(user_id, as_dict=True)
        st.markdown(f"**Embedding Similarity Score:** `{embed_score:.3f}`")
        st.markdown("#### 📊 Persona Metrics")
        st.json(metrics, expanded=False)

def render_danger_zone(user_id: str):
    """Danger zone controls (reset/flush), local-only, admin/user"""
    if not HAS_LOCAL:
        return
    st.markdown("---")
    with st.expander("💥 Danger Zone: Persona & Memory Ops", expanded=False):
        if st.button("Reset Profile (Irreversible)"):
            reset_profile(user_id)
            st.warning("Profile reset. Please refresh panel.")
        if st.button("Flush Short-Term Memory"):
            flush_short_term(user_id)
            st.info("Short-term memory flushed.")
        if st.button("Flush Long-Term Memory"):
            flush_long_term(user_id)
            st.info("Long-term memory flushed.")

def render_profile_panel(user_ctx: Dict[str, Any]):
    """
    Universal Profile Panel for Kari.
    Args:
        user_ctx: Dict with user_id, roles, org, etc.
    """
    try:
        user_id = user_ctx.get("user_id")
        roles = user_ctx.get("roles", [])
        org = user_ctx.get("org_id", None)

        # --- RBAC check: user (self), admin (all), analyst (read-only) ---
        try:
            require_roles(user_ctx, ["user", "admin", "analyst"])
        except Exception as e:
            st.error("🔒 You don't have permission to view/edit profiles.")
            logger.warning(f"Profile access denied for {user_id}: {e}")
            return

        st.title("👤 Kari Persona Profile")
        st.markdown("""
            <div style='color: #666; margin-bottom: 1.2em;'>
                View and edit your active profile. Metrics, memory, audit, and danger zone below.
            </div>
        """, unsafe_allow_html=True)

        # --- Profile Fetch ---
        with st.spinner("Loading profile..."):
            try:
                profile = load_profile(user_ctx)
            except Exception as e:
                st.error(f"Could not load profile: {e}")
                return

        readonly = ("analyst" in roles and "admin" not in roles and "user" not in roles)
        can_edit = ("admin" in roles or user_id == profile.get("user_id") or user_id == profile.get("id"))
        st.subheader("Profile Information")
        with st.form("profile_edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Display Name", profile.get("name", ""), disabled=readonly)
                style = st.selectbox(
                    "Preferred Style", 
                    ["Neutral", "Empathetic", "Witty", "Serious", "Humorous"],
                    index=["Neutral", "Empathetic", "Witty", "Serious", "Humorous"].index(profile.get("style", "Neutral")),
                    disabled=readonly
                )
                importance = st.slider("Importance", 1, 10, int(profile.get("importance", 5)), disabled=readonly)
            with col2:
                bio = st.text_area("Bio/Description", profile.get("bio", ""), height=80, disabled=readonly)
                tags_val = profile.get("tags", [])
                tags = st.text_input("Tags (comma-separated)", ", ".join(tags_val) if isinstance(tags_val, list) else str(tags_val), disabled=readonly)
            preferences = st.text_area("Preferences (JSON)", value=str(profile.get("preferences", "{}")), height=50, disabled=readonly)
            submit = st.form_submit_button("Save Profile", disabled=readonly or not can_edit)

        # --- Save Handler ---
        if submit and not readonly and can_edit:
            import json
            try:
                prefs_dict = parse_preferences(preferences)
            except Exception:
                prefs_dict = {}
            updated_profile = {
                "name": name,
                "bio": bio,
                "style": style,
                "importance": importance,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "preferences": prefs_dict,
            }
            with st.spinner("Saving..."):
                try:
                    save_profile(user_ctx, updated_profile)
                    st.success("Profile saved!")
                    st.experimental_rerun()
                except Exception as e:
                    logger.error(f"Profile save failed: {e}")
                    st.error("Profile save failed.")

        # --- Persona Embedding & Metrics ---
        if HAS_LOCAL:
            render_persona_metrics(user_id)

        # --- Profile Change History ---
        if HAS_LOCAL:
            render_profile_history(user_id)

        # --- Audit Trail (Admin only, API) ---
        if "admin" in roles:
            with st.expander("📝 Profile Audit Logs"):
                try:
                    audit_logs = fetch_audit_logs(category="user_profile", user_id=user_id, limit=25)
                    if audit_logs:
                        df = pd.DataFrame(audit_logs)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No recent audit logs.")
                except Exception as ex:
                    st.warning(f"Audit log fetch error: {ex}")

        # --- Danger Zone ---
        if can_edit and HAS_LOCAL:
            render_danger_zone(user_id)

        st.caption("Profile Panel v2.0 – All changes are tracked. Kari never forgets.")

    except Exception as e:
        st.error("Critical error in profile panel.")
        logger.critical(f"Profile panel failed: {e}\n{traceback.format_exc()}")
        if st.session_state.get("show_debug_info", False):
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())

# Import alias for Streamlit/Kari UI
render_profile_panel_page = render_profile_panel
