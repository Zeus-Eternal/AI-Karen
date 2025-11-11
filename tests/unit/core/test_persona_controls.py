from ui_launchers.common.components.rbac import require_role, st


def test_require_role_allows_authorized_user(monkeypatch):
    st.session_state.clear()
    st.session_state["roles"] = {"admin", "user"}

    called = {}

    @require_role("admin")
    def protected():
        called["ran"] = True
        return "ok"

    result = protected()
    assert result == "ok"
    assert called["ran"] is True


def test_require_role_blocks_unauthorized_user(monkeypatch):
    st.session_state.clear()
    st.session_state["roles"] = {"user"}

    errors = {}

    def fake_error(message):
        errors["message"] = message

    monkeypatch.setattr(st, "error", fake_error)

    @require_role("admin")
    def protected():
        return "ok"

    assert protected() is None
    assert errors["message"] == "Access denied"
