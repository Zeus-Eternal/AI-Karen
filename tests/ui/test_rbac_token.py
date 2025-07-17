import types
import sys

sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

from ui_launchers.common.components import rbac
from ui_launchers.streamlit_ui.helpers import session


def test_page_denied_with_invalid_token(monkeypatch):
    st = types.SimpleNamespace(
        session_state={},
        error=lambda msg: st.session_state.setdefault("err", msg),
        experimental_get_query_params=lambda: {},
        experimental_set_query_params=lambda **_: None,
    )
    monkeypatch.setattr(rbac, "st", st)
    monkeypatch.setattr(session, "st", st)
    monkeypatch.setattr(session, "_verify_token", lambda t: None)

    st.session_state["token"] = "bad"
    ctx = session.get_user_context()
    assert ctx["roles"] == []
    assert st.session_state["roles"] == []

    @rbac.require_role("admin")
    def _page():
        return "ok"

    assert _page() is None
    assert st.session_state["err"] == "Access denied"
