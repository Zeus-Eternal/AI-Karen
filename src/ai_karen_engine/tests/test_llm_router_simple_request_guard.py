from pathlib import Path


def test_simple_request_helper_defined_in_router():
    file = Path(__file__).resolve().parents[1] / "services" / "models" / "routing" / "llm_router_service.py"
    text = file.read_text(encoding="utf-8", errors="ignore")
    assert "def _is_simple_chat_request" in text
    assert "self._is_simple_request" not in text
