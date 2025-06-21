class NANDAClient:
    """Stub client for the NANDA agent federation."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def discover(self, query: str):
        """Return remote code snippets for a given query."""
        return [{"snippet": f"# {self.agent_name} hint for {query}"}]

    def submit_snippet(self, snippet: str, metadata=None) -> None:
        """Submit a code snippet for others to reuse (no-op)."""
        _ = (snippet, metadata)
        return None

