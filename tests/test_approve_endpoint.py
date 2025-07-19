import pathlib
from types import SimpleNamespace

from ai_karen_engine.api_routes.self_refactor import approve_review, ApproveRequest
from ai_karen_engine.self_refactor import SelfRefactorEngine


def test_approve_endpoint(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    review = repo / "self_refactor" / "reviews" / "1"
    review.mkdir(parents=True)
    (review / "a.py").write_text("print('x')\n")
    monkeypatch.setattr("ai_karen_engine.api_routes.self_refactor.ENGINE_ROOT", repo)
    class DummyEngine(SelfRefactorEngine):
        def __init__(self, repo_root):
            self.repo_root = repo_root
            self.review_dir = repo_root / "self_refactor" / "reviews"

        def apply_review(self, review_id: str) -> None:
            super().apply_review(review_id)

    monkeypatch.setattr(
        "ai_karen_engine.api_routes.self_refactor.SelfRefactorEngine", DummyEngine
    )
    request = SimpleNamespace(state=SimpleNamespace(roles=["admin"]))
    resp = approve_review(ApproveRequest(review_id="1"), request)
    assert resp["status"] == "applied"
    assert (repo / "a.py").read_text() == "print('x')\n"
    assert not review.exists()

