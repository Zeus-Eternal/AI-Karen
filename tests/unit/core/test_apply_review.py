from ai_karen_engine.self_refactor import SelfRefactorEngine


class DummyEngine(SelfRefactorEngine):
    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.review_dir = repo_root / "self_refactor" / "reviews"


def test_apply_review(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    code = repo / "a.py"
    code.write_text("x = 1\n")
    review = repo / "self_refactor" / "reviews" / "123"
    review.mkdir(parents=True)
    (review / "a.py").write_text("x = 2\n")
    engine = DummyEngine(repo_root=repo)
    engine.apply_review("123")
    assert code.read_text() == "x = 2\n"
    assert not review.exists()

