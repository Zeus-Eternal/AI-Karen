from integrations.nanda_client import NANDAClient


 
def test_snippet_submission_and_discovery(tmp_path):
    store = tmp_path / "snippets.json"
    client = NANDAClient(agent_name="karen", store_path=store)
    client.submit_snippet("print('hi')", {"tag": "py"})
    hints = client.discover("hi")
    assert hints and hints[0]["snippet"].startswith("print")

def test_discover_returns_snippet():
    client = NANDAClient(agent_name="karen")
    hints = client.discover("optimize")
    assert hints and "snippet" in hints[0]

 
