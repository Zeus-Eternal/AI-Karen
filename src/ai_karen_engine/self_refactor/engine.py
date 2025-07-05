"""Self-refactoring engine with simple RL loop."""

from __future__ import annotations

import ast
import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Tuple

from integrations.nanda_client import NANDAClient
 
from integrations.llm_registry import registry as llm_registry

from integrations.llm_utils import LLMUtils


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
    ) -> None:
        self.repo_root = pathlib.Path(repo_root)
 
        self.llm = llm or llm_registry.get_active()
        self.deepseek = deepseek or llm_registry.get_active()
 
        self.nanda = nanda or NANDAClient(agent_name="SelfRefactor")
        self.test_cmd = test_cmd or ["pytest", "-q"]

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

    def reinforce(self, report: PatchReport) -> None:
        """Promote successful patches to the main repository."""
        if report.reward <= 0:
            return
        for file_str, patch in report.patches.items():
            target = self.repo_root / file_str
            target.write_text(patch)

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
