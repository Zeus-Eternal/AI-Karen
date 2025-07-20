import importlib.util
import sys
import types
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "src/ui_logic/components/memory/knowledge_graph.py"

class DummyStreamlit:
    def __init__(self):
        self.info_messages = []
        self.subheader = self._noop
        self.markdown = self._noop
        self.text_input = lambda *a, **k: ""
        self.slider = lambda *a, **k: 1
        self.button = lambda *a, **k: False
        self.dataframe = self._noop
        self.write = self._noop
        self.error = self._noop
        self.checkbox = lambda *a, **k: False
        self.session_state = {}

    def info(self, msg):
        self.info_messages.append(msg)

    @staticmethod
    def _noop(*a, **k):
        pass

def setup_env(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    fake_rbac = types.ModuleType("ui_logic.hooks.rbac")
    def require_roles(user_ctx, roles):
        if not any(r in user_ctx.get("roles", []) for r in roles):
            raise PermissionError("denied")
        return True
    fake_rbac.require_roles = require_roles
    monkeypatch.setitem(sys.modules, "ui_logic.hooks.rbac", fake_rbac)

    fake_api = types.ModuleType("ui_logic.utils.api")
    fake_api.fetch_audit_logs = lambda **_: []
    monkeypatch.setitem(sys.modules, "ui_logic.utils.api", fake_api)

    fake_pd = types.ModuleType("pandas")
    fake_pd.DataFrame = lambda *a, **k: object()
    monkeypatch.setitem(sys.modules, "pandas", fake_pd)

    fake_client_mod = types.ModuleType("ai_karen_engine.services.knowledge_graph_client")
    class DummyClient:
        def find_related_concepts(self, *a, **k):
            return []
        def get_concept_graph(self, *a, **k):
            return []
        def health(self):
            return True
    fake_client_mod.KnowledgeGraphClient = DummyClient
    monkeypatch.setitem(sys.modules, "ai_karen_engine.services.knowledge_graph_client", fake_client_mod)

    spec = importlib.util.spec_from_file_location("kg", MODULE_PATH)
    kg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kg)
    return kg, st


def test_audit_permission_denied(monkeypatch):
    kg, st = setup_env(monkeypatch)
    ctx = {"user_id": "u1", "roles": ["user"]}
    kg.render_knowledge_graph_panel(ctx)
    assert any("permission" in msg.lower() for msg in st.info_messages)
