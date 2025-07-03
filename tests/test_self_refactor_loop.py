from ai_karen_engine.self_refactor import SelfRefactorEngine


class DummyLLM:
    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        return prompt.split("### PATCH\n", 1)[-1]


class DummyNANDA:
    def discover(self, query: str):
        return []


def test_test_patches_and_reinforce(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tests").mkdir()
    code = repo / "maths.py"
    code.write_text("def add(a, b):\n    return a - b\n")
    (repo / "tests" / "test_maths.py").write_text(
        "from maths import add\n\n\ndef test_add():\n    assert add(1, 1) == 2\n"
    )

    engine = SelfRefactorEngine(repo_root=repo, llm=DummyLLM(), nanda=DummyNANDA())
    patches = {code: "def add(a, b):\n    return a + b\n"}
    report = engine.test_patches(patches)
    assert report.reward == 1

    engine.reinforce(report)
    assert code.read_text() == patches[code]
