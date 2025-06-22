
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
 

 

 

import ast
import pathlib
 
 
 
from typing import Dict, List, Tuple


class PatchReport(dict):

    """Dictionary-based patch report with typed helpers."""

    @property
    def reward(self) -> float:
        return float(self.get("reward", 0))

    @property
    def patches(self) -> Dict[str, str]:
        return self.get("patches", {})



from integrations.nanda_client import NANDAClient
from src.integrations.llm_utils import LLMUtils


 
class _OpenAILLM:
    """Very small wrapper around the OpenAI SDK"""

    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        try:  # pragma: no cover - optional dependency
            import openai  # type: ignore

            self._openai = openai
            self.model = model
        except Exception as exc:  # pragma: no cover
            self._openai = None
            self._error = exc
            self.model = model

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        if not self._openai:
            return f"{prompt} (openai unavailable)"
        resp = self._openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message["content"]



 
class SelfRefactorEngine:
    """Run static analysis and LLM-guided refactoring cycles."""

    def __init__(
        self,
        repo_root: pathlib.Path,
 
        llm: object | None = None,

        deepseek: LLMUtils | None = None,
 
        nanda: NANDAClient | None = None,
        test_cmd=None,
    ) -> None:
        self.repo_root = pathlib.Path(repo_root)
 
        self.llm = llm or self._default_llm()
        self.nanda = nanda or NANDAClient(agent_name="SelfRefactor")
        self.test_cmd = test_cmd or ["pytest", "-q"]

    def _default_llm(self) -> object:
        backend = os.getenv("SRE_LLM", "hf").lower()
        if backend == "openai":
            return _OpenAILLM()
        # "deepseek" backend is optional and treated the same as hf if missing
        if backend == "deepseek":  # pragma: no cover - optional dependency
            try:
                from deepseek_engineer import DeepSeek

                class _DSWrapper:
                    def __init__(self) -> None:
                        self._ds = DeepSeek(model_path="models/deepseek-v2.ggml")

                    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
                        return self._ds.generate(prompt, max_tokens)

                return _DSWrapper()
            except Exception:
                pass
        return LLMUtils()

    def _generate(self, prompt: str) -> str:
        if hasattr(self.llm, "generate_text"):
            return self.llm.generate_text(prompt)
        if hasattr(self.llm, "generate"):
            return self.llm.generate(prompt)
        raise AttributeError("LLM backend missing generate method")


        self.deepseek = deepseek or LLMUtils()
        self.nanda = nanda or NANDAClient(agent_name="SelfRefactor")
        self.test_cmd = test_cmd or ["pytest", "-q"]

 


class SelfRefactorEngine:
    """Run static analysis and LLM-guided refactoring cycles."""

    def __init__(self, repo_root: pathlib.Path, deepseek, nanda, test_cmd=None) -> None:
        self.repo_root = pathlib.Path(repo_root)
        self.deepseek = deepseek
        self.nanda = nanda
        self.test_cmd = test_cmd or ["pytest", "-q"]

 

    """Simple dict-based patch report"""
    pass


class SelfRefactorEngine:
    def __init__(self, repo_root: pathlib.Path, deepseek, nanda):
        self.repo_root = pathlib.Path(repo_root)
        self.deepseek = deepseek
        self.nanda = nanda

 
 
    def static_analysis(self) -> List[Tuple[pathlib.Path, str]]:
        issues = []
        for file in self.repo_root.rglob("*.py"):
            try:
                tree = ast.parse(file.read_text())
            except Exception:
                continue
            node_count = sum(1 for _ in ast.walk(tree))
            if node_count > 200:
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


            p: self.deepseek.generate(f"{context}\n### PATCH\n{pr}")
            for (p, _), pr in zip(issues, prompts)
 
        }


 
        }


 
        }

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
            env = dict(**{k: v for k, v in list(os.environ.items())})
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
        return report

    def reinforce(self, report: PatchReport) -> None:
        """Promote successful patches to the main repository."""
        print(json.dumps({"self_refactor": report.reward}))
        if report.reward <= 0:
            return
        for file_str, patch in report.patches.items():
            target = self.repo_root / file_str
            target.write_text(patch)
