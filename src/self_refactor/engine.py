import ast
import pathlib
from typing import Dict, List, Tuple


class PatchReport(dict):
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
            p: self.deepseek.generate(f"{context}\n### PATCH\n{pr}")
            for (p, _), pr in zip(issues, prompts)
        }
