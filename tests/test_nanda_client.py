from integrations.nanda_client import NANDAClient


def test_discover_returns_snippet():
    client = NANDAClient(agent_name="karen")
    hints = client.discover("optimize")
    assert hints and "snippet" in hints[0]

