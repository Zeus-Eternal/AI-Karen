import pytest

from ai_karen_engine.clients.nlp import spacy_client as sc

class DummyNLP:
    pass

@pytest.fixture

def fake_spacy(monkeypatch):
    class FakeSpaCy:
        def __init__(self):
            self.calls = []
        def load(self, name):
            self.calls.append(name)
            if name == sc.TRF_MODEL:
                raise OSError("missing")
            return DummyNLP()
    fake = FakeSpaCy()
    monkeypatch.setattr(sc, "spacy", fake)
    return fake


def test_trf_fallback(fake_spacy):
    client = sc.SpaCyClient()
    assert isinstance(client.nlp, DummyNLP)
    assert client.model_name == sc.SM_MODEL
    assert fake_spacy.calls == [sc.TRF_MODEL, sc.SM_MODEL]


def test_explicit_small(monkeypatch):
    class FakeSpaCy:
        def __init__(self):
            self.calls = []
        def load(self, name):
            self.calls.append(name)
            return DummyNLP()
    fake = FakeSpaCy()
    monkeypatch.setattr(sc, "spacy", fake)
    client = sc.SpaCyClient(model_name=sc.SM_MODEL)
    assert isinstance(client.nlp, DummyNLP)
    assert client.model_name == sc.SM_MODEL
    assert fake.calls == [sc.SM_MODEL]

