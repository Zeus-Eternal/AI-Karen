"""
Kari Model Benchmark Panel Logic
- Compares LLM/model performance (latency, accuracy, cost)
- RBAC: admin, analyst, user (with limits)
- Audit-logged; config-driven
"""

from typing import Dict, Any, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_model_benchmarks, 
    run_model_benchmark, 
    fetch_audit_logs
)

def get_model_benchmarks(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst", "user"]):
        raise PermissionError("Insufficient privileges for model benchmarking.")
    return fetch_model_benchmarks(user_ctx.get("user_id"))

def benchmark_model(user_ctx: Dict, model_id: str, params: Dict[str, Any]) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges to run model benchmark.")
    return run_model_benchmark(model_id, params, user_ctx.get("user_id"))

def get_benchmark_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges for benchmark audit.")
    return fetch_audit_logs(category="model_benchmark", user_id=user_ctx["user_id"])[-limit:][::-1]
