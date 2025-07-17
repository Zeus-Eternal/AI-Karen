import time
import importlib.util
from ai_karen_engine.event_bus import get_event_bus

spec = importlib.util.spec_from_file_location(
    "presence", "src/ui_logic/pages/presence.py"
)
presence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(presence)
page = presence.page


def test_presence_page_consumes_events():
    bus = get_event_bus()
    bus.publish("caps", "ping", {"ts": time.time()}, risk=0.1, roles=["admin"], tenant_id="t1")
    result = page({"roles": ["admin", "user"], "tenant_id": "t1"})
    assert isinstance(result, list)
    assert result and result[0]["capsule"] == "caps"
