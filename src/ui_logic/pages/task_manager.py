"""Secure job management UI."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List

import pandas as pd
import streamlit as st

from ai_karen_engine.services.job_manager import Job, JobManager
from ui_logic.pages._shared import require_page_access

REQUIRED_ROLES = ["user", "dev"]
FEATURE_FLAG = "enable_workflows"


def _get_manager() -> JobManager:
    manager: JobManager = st.session_state.setdefault("kari_job_manager", JobManager())
    if not st.session_state.get("kari_job_handler_registered"):
        _register_diagnostic_handler(manager)
        st.session_state["kari_job_handler_registered"] = True
    return manager


def _register_diagnostic_handler(manager: JobManager) -> None:
    def _handler(job: Job) -> None:
        total_steps = int(job.parameters.get("steps", 10))
        for step in range(total_steps):
            if job._cancel_event and job._cancel_event.is_set():
                manager.set_error(job.id, "Cancelled by operator")
                return
            if job._pause_event and job._pause_event.is_set():
                while job._pause_event.is_set():
                    time.sleep(0.2)

            progress = (step + 1) / total_steps
            manager.update_progress(job.id, progress)
            manager.append_log(job.id, f"Completed step {step + 1} of {total_steps}")
            time.sleep(job.parameters.get("delay", 0.2))

        manager.complete_job(
            job.id,
            {
                "completed_at": datetime.utcnow().isoformat(),
                "steps": total_steps,
                "note": job.parameters.get("note", "Synthetic diagnostics"),
            },
        )

    manager.register_handler("diagnostic", _handler)


def _render_stats(manager: JobManager) -> None:
    stats = manager.get_stats()
    col_total, col_running, col_failed = st.columns(3)
    col_total.metric("Jobs", stats.total_jobs)
    col_running.metric("Running", stats.running_jobs)
    col_failed.metric("Failures", stats.failed_jobs)


def _render_job_table(jobs: List[Job]) -> None:
    if not jobs:
        st.info("No jobs queued yet. Submit a diagnostic run below.")
        return

    frame = pd.DataFrame(
        [
            {
                "ID": job.id,
                "Title": job.title or job.kind.title(),
                "Status": job.status,
                "Progress": f"{job.progress * 100:.0f}%",
                "Created": datetime.fromtimestamp(job.created_at).isoformat(),
                "Updated": datetime.fromtimestamp(job.updated_at).isoformat(),
            }
            for job in jobs
        ]
    )
    st.dataframe(frame, hide_index=True, use_container_width=True)


def _render_job_controls(manager: JobManager, job: Job) -> None:
    with st.expander(f"{job.title or job.id} — {job.status}"):
        st.progress(job.progress)
        st.code("\n".join(job.logs[-10:]) or "No logs yet.")
        st.json(job.result or {}, expanded=False)

        col1, col2, col3 = st.columns(3)
        if col1.button("Pause", key=f"pause_{job.id}", disabled=not job.can_pause()):
            manager.pause_job(job.id)
        if col2.button("Resume", key=f"resume_{job.id}", disabled=not job.can_resume()):
            manager.resume_job(job.id)
        if col3.button("Cancel", key=f"cancel_{job.id}", disabled=not job.can_cancel()):
            manager.cancel_job(job.id)


def render_page(user_ctx: Dict | None = None) -> None:
    """Render the task manager page."""

    require_page_access(
        user_ctx,
        required_roles=REQUIRED_ROLES,
        feature_flag=FEATURE_FLAG,
        feature_name="Workflow engine",
    )

    manager = _get_manager()

    st.title("🧮 Task Manager")
    st.caption("Queue, inspect and control long running jobs.")

    _render_stats(manager)

    st.markdown("### Active jobs")
    jobs = manager.list_jobs(limit=50)
    _render_job_table(jobs)

    st.markdown("---")
    st.subheader("Submit diagnostic job")
    with st.form("diagnostic_job"):
        title = st.text_input("Title", value="Diagnostics sweep")
        steps = st.slider("Steps", min_value=3, max_value=20, value=10)
        delay = st.slider("Delay per step (seconds)", min_value=0.1, max_value=1.0, value=0.2)
        if st.form_submit_button("Queue job"):
            job = manager.create_job(
                kind="diagnostic",
                title=title,
                description="Synthetic diagnostic workload",
                parameters={"steps": steps, "delay": delay},
            )
            manager.start_job(job.id)
            st.success(f"Queued job {job.id}")

    for job in jobs:
        _render_job_controls(manager, job)

