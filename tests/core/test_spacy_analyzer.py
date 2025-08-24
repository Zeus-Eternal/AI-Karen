from core.response.spacy_analyzer import SpaCyAnalyzer


def test_spacy_analyzer_outputs() -> None:
    analyzer = SpaCyAnalyzer()
    result = analyzer.analyze("Hello there")
    assert result["intent"] == "greeting"
    assert "persona" in result
    assert "sentiment" in result
    assert "entities" in result
