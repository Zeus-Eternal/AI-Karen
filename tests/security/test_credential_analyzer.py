from types import SimpleNamespace

import pytest

from ai_karen_engine.security.credential_analyzer import CredentialAnalyzer
from ai_karen_engine.security.models import IntelligentAuthConfig


class DummySpacyService:
    def __init__(self, fail: bool = False):
        self.fail = fail

    async def parse_message(self, text: str):
        if self.fail:
            raise RuntimeError("boom")
        return SimpleNamespace(used_fallback=False)


@pytest.mark.asyncio
async def test_initialize_handles_spacy_failure():
    analyzer = CredentialAnalyzer(
        IntelligentAuthConfig(), spacy_service=DummySpacyService(fail=True)
    )
    success = await analyzer.initialize()
    assert success is False


@pytest.mark.asyncio
async def test_fallback_language_detection():
    analyzer = CredentialAnalyzer(IntelligentAuthConfig(), spacy_service=DummySpacyService())
    assert analyzer._fallback_language_detection("hello") == "en"
    assert analyzer._fallback_language_detection("你好") == "multi"
    assert analyzer._fallback_language_detection("") == "unknown"
