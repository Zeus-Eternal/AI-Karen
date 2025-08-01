"""Self-refactoring engine with simple RL loop."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Tuple

from ai_karen_engine.integrations.nanda_client import NANDAClient
 
from ai_karen_engine.integrations.llm_registry import get_registry



class PatchReport(dict):
    """Dictionary-based patch report with typed helpers."""

    @property
    def reward(self) -> float:
        return float(self.get("reward", 0))

    @property
    def patches(self) -> Dict[str, str]:
        return self.get("patches", {})


class SelfRefactorEngine:
    """Run static analysis and LLM-guided refactoring cycles."""

    def __init__(
        self,
        repo_root: pathlib.Path,
        llm=None,
        deepseek=None,
        nanda=None,
        test_cmd=None,
        auto_merge: bool | None = None,
        review_dir: pathlib.Path | None = None,
    ) -> None:
        self.repo_root = pathlib.Path(repo_root)

        llm_registry = get_registry()
        self.llm = llm or llm_registry.auto_select_provider()
        self.deepseek = deepseek or llm_registry.auto_select_provider()

        self.nanda = nanda or NANDAClient(agent_name="SelfRefactor")
        self.test_cmd = test_cmd or ["pytest", "-q"]

        env_merge = os.getenv("ENABLE_SELF_REFACTOR_AUTO_MERGE", "false").lower() == "true"
        self.auto_merge = env_merge if auto_merge is None else auto_merge
        self.review_dir = review_dir or (self.repo_root / "self_refactor" / "reviews")

    def _generate(self, prompt: str) -> str:
        if hasattr(self.llm, "generate_text"):
            return self.llm.generate_text(prompt)
        return prompt

    def static_analysis(self) -> List[Tuple[pathlib.Path, str]]:
        issues = []
        for file in self.repo_root.rglob("*.py"):
            try:
                tree = ast.parse(file.read_text())
            except Exception:
                continue
            if sum(1 for _ in ast.walk(tree)) > 200:
                issues.append((file, "High AST node count (complexity)"))
        return issues

    def propose_patches(self, issues) -> Dict[pathlib.Path, str]:
        prompts = [
            f"Refactor `{p}` → reduce complexity:\n{open(p).read()[:8000]}"
            for p, _ in issues
        ]
        remote_hints = self.nanda.discover("python refactor large module")
        context = "\n\n".join(h.get("snippet", "") for h in remote_hints[:3])
        return {
            p: self._generate(f"{context}\n### PATCH\n{pr}")
            for (p, _), pr in zip(issues, prompts)
        }

    def test_patches(self, patches: Dict[pathlib.Path, str]) -> PatchReport:
        """Apply patches in a sandbox and run the test suite."""
        report: PatchReport = PatchReport()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            dst = tmp_path / self.repo_root.name
            shutil.copytree(self.repo_root, dst)
            for file, code in patches.items():
                target = dst / file.relative_to(self.repo_root)
                target.write_text(code)
            start = time.time()
            env = dict(os.environ)
            env["PYTHONPATH"] = str(dst)
            proc = subprocess.run(
                self.test_cmd,
                cwd=dst,
                capture_output=True,
                text=True,
                env=env,
            )
            duration = time.time() - start
            reward = 1.0 if proc.returncode == 0 else 0.0
            report.update(
                {
                    "reward": reward,
                    "duration": duration,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "patches": {str(k): v for k, v in patches.items()},
                    "signatures": {
                        str(k): hashlib.sha256(v.encode()).hexdigest()
                        for k, v in patches.items()
                    },
                }
            )
        try:
            from ai_karen_engine.self_refactor import log_utils

            log_utils.record_report(report)
        except Exception:
            pass
        return report

    def reinforce(self, report: PatchReport) -> pathlib.Path | None:
        """Save results and optionally merge successful patches.

        Returns the path of the review directory if a patch was queued.
        """
        if report.reward <= 0:
            return None

        self.review_dir.mkdir(parents=True, exist_ok=True)
        ts = str(int(time.time()))
        review_path = self.review_dir / ts
        review_path.mkdir()
        for file_str, patch in report.patches.items():
            rel_path = pathlib.Path(file_str)
            dest = review_path / rel_path.name
            dest.write_text(patch)
        (review_path / "report.json").write_text(
            json.dumps(report, indent=2)
        )

        if not self.auto_merge:
            return review_path

        for file_str, patch in report.patches.items():
            target = self.repo_root / file_str
            target.write_text(patch)

        return review_path

    # Convenience -----------------------------------------------------------
    def self_heal(self) -> PatchReport | None:
        """Run one complete self-refactor cycle."""
        issues = self.static_analysis()
        if not issues:
            return None
        patches = self.propose_patches(issues)
        report = self.test_patches(patches)
        self.reinforce(report)
        return report

    def apply_review(self, review_id: str) -> None:
        """Apply patches from a saved review directory."""
        review_path = self.review_dir / review_id
        if not review_path.exists():
            raise FileNotFoundError(str(review_path))
        for file in review_path.iterdir():
            if file.name == "report.json":
                continue
            target = self.repo_root / file.name
            target.write_text(file.read_text())
        shutil.rmtree(review_path)
