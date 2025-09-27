"""Automation scheduler dashboard."""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import streamlit as st

from ai_karen_engine.automation_manager import get_automation_manager
from ai_karen_engine.automation_manager.encryption_utils import decrypt_data
from ui_logic.pages._shared import coerce_datetime, require_page_access

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_workflows"


def _decode_result(raw_result) -> Dict | str | None:
    if not raw_result:
        return None
    try:
        decrypted = decrypt_data(raw_result)
    except Exception:  # pragma: no cover - cryptography edge cases
        return str(raw_result)

    if not decrypted:
        return None

    try:
        return json.loads(decrypted)
    except json.JSONDecodeError:
        return decrypted


def _snapshot_jobs(manager) -> List[Tuple[str, Dict]]:
    jobs: List[Tuple[str, Dict]] = []
    schedule = getattr(manager, "_schedule", {})
    lock = getattr(manager, "_lock", None)
    items: Iterable[Tuple[str, Dict]]
    if lock is not None:
        with lock:  # type: ignore[assignment]
            items = list(schedule.items())
    else:  # pragma: no cover - defensive branch
        items = schedule.items()

    for job_id, payload in items:
        job = dict(payload)
        job["result"] = _decode_result(job.get("result"))
        job["last_run_dt"] = coerce_datetime(job.get("last_run"))
        job["created_at_dt"] = coerce_datetime(job.get("created_at"))
        jobs.append((job_id, job))
    return jobs


def _bootstrap_demo_job(manager) -> None:
    if getattr(manager, "_schedule", {}):
        return

    def _demo_job() -> str:
        time.sleep(0.2)
        return json.dumps({"status": "ok", "checked_at": datetime.utcnow().isoformat()})

    manager.register_job("Telemetry heartbeat", _demo_job, "*/15 * * * *")


def render_page(user_ctx: Dict | None = None) -> None:
    """Render the automation dashboard."""

    require_page_access(
        user_ctx,
        required_roles=REQUIRED_ROLES,
        feature_flag=FEATURE_FLAG,
        feature_name="Workflow automation",
    )

    manager = get_automation_manager()
    _bootstrap_demo_job(manager)

    st.title("⚙️ Automation Control Tower")
    st.caption("Monitor and manually trigger secure background jobs.")

    jobs = _snapshot_jobs(manager)
    if not jobs:
        st.info("No automation jobs have been registered yet.")
        return

    summary = pd.DataFrame(
        [
            {
                "Job": meta["name"],
                "Schedule": meta.get("schedule", "—"),
                "Status": meta.get("status", "pending"),
                "Last Run": meta.get("last_run_dt"),
                "Result": meta.get("result"),
            }
            for _, meta in jobs
        ]
    )

    completed = sum(1 for _, meta in jobs if str(meta.get("status")).lower() == "success")
    failures = sum(1 for _, meta in jobs if str(meta.get("status")).lower() == "failed")

    col_jobs, col_ok, col_fail = st.columns(3)
    col_jobs.metric("Registered Jobs", len(jobs))
    col_ok.metric("Successful Runs", completed)
    col_fail.metric("Failures", failures)

    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Job actions")

    for job_id, meta in jobs:
        with st.expander(f"{meta['name']} — {meta.get('status', 'pending')}"):
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if st.button("Run now", key=f"trigger_{job_id}"):
                    if manager.trigger_job(job_id):
                        st.success("Execution requested")
                    else:
                        st.error("Job could not be queued (check signature)" )
            with col_b:
                st.markdown(
                    f"**Schedule:** `{meta.get('schedule', 'n/a')}`  \
**Created:** {meta.get('created_at_dt')}  \
**Last Run:** {meta.get('last_run_dt')}"
                )

            if meta.get("result") is not None:
                st.write("Last Result")
                st.json(meta["result"], expanded=False)

