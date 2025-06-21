import pathlib

from src.self_refactor import SelfRefactorEngine


class DummyLLM:
    def __init__(self):
        self.prompts = []

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        self.prompts.append(prompt)
        return "patched-code"


class DummyNANDA:
    def discover(self, query: str):
        return [{"snippet": "# expert hint"}]


def make_large_file(path: pathlib.Path):
    lines = ["def func():\n"]
    for i in range(210):
        lines.append(f"    x{i} = {i}\n")
    path.write_text("".join(lines))


def test_propose_patches(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    f1 = repo / "a.py"
    f2 = repo / "b.py"
    make_large_file(f1)
    make_large_file(f2)

    engine = SelfRefactorEngine(repo_root=repo,
                                llm=DummyLLM(),
                                nanda=DummyNANDA())

    issues = engine.static_analysis()
    assert len(issues) == 2

    patches = engine.propose_patches(issues)
    assert set(patches.keys()) == {f1, f2}
    assert all(p == "patched-code" for p in patches.values())
