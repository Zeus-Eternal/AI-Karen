from pathlib import Path
from ai_karen_engine.self_refactor import SelfRefactorEngine

class DummyLLM:
    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        return prompt.split("### PATCH\n", 1)[-1]


class DummyNANDA:
    def discover(self, query: str):
        return []


def make_large_file(path: Path) -> None:
    lines = ["def func():\n"]
    for i in range(210):
        lines.append(f"    x{i} = {i}\n")
    path.write_text("".join(lines))


def test_self_heal_cycle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tests").mkdir()
    code = repo / "maths.py"
    make_large_file(code)
    code.write_text(code.read_text() + "    return 0\n")
    (repo / "tests" / "test_maths.py").write_text(
        "from maths import func\n\n\ndef test_func():\n    assert func() == 1\n"
    )

    engine = SelfRefactorEngine(repo_root=repo, llm=DummyLLM(), nanda=DummyNANDA())
    engine.propose_patches = lambda issues: {code: code.read_text().replace("return 0", "return 1")}
    report = engine.self_heal()
    assert report and report.reward == 1
