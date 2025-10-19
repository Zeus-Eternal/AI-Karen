"""Unit tests covering the CORTEX routing integrations."""

from __future__ import annotations

import pytest

from ai_karen_engine.core.cortex.routing_intents import resolve_routing_intent
from ai_karen_engine.core.cortex.dispatch import dispatch
from ai_karen_engine.core.predictors import predictor_registry
from ai_karen_engine.extensions.workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    StepType,
    WorkflowStatus,
)


@pytest.fixture
def user_ctx() -> dict[str, str]:
    return {"user_id": "user-123", "tenant_id": "tenant-x", "roles": ["routing"]}


def test_resolve_routing_intent_detects_select(user_ctx):
    """Routing resolver should surface routing intents before fallback logic."""
    intent, meta = resolve_routing_intent("Please route to OpenAI for this", user_ctx)

    assert intent == "routing.select"
    assert meta["match"] == "routing"
    assert meta["pattern"] == "route to"


@pytest.mark.asyncio
async def test_dispatch_invokes_routing_predictor(monkeypatch, user_ctx):
    """Dispatch should execute registered routing predictors asynchronously."""

    async def fake_routing_handler(user_ctx, query, context=None):
        assert "route to" in query.lower()
        return {"provider": "openai", "model": "gpt-4o"}

    monkeypatch.setitem(predictor_registry, "routing.select", fake_routing_handler)

    result = await dispatch(
        user_ctx,
        "Can you route to OpenAI for this reasoning task?",
        memory_enabled=False,
        plugin_enabled=False,
    )

    assert result["intent"] == "routing.select"
    assert result["result"]["provider"] == "openai"
    assert result["result"]["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_workflow_engine_routing_step(monkeypatch, user_ctx):
    """Routing workflow steps should leverage the predictor registry."""

    recorded = {}

    async def fake_select(user_ctx, query, context=None):
        recorded["query"] = query
        recorded["context"] = context
        return {"provider": "deepseek", "model": "deepseek-chat"}

    monkeypatch.setitem(predictor_registry, "routing.select", fake_select)

    engine = WorkflowEngine(plugin_orchestrator=object())

    routing_step = WorkflowStep(
        id="routing",
        type=StepType.ROUTING,
        config={
            "action": "routing.select",
            "query": "${input_query}",
            "context": {"requirements": "${requirements}"},
            "output_key": "routing_result",
        },
    )

    workflow = WorkflowDefinition(
        id="wf-routing",
        name="Routing Workflow",
        steps={"routing": routing_step},
        start_step="routing",
    )

    execution = WorkflowExecution(
        workflow_id=workflow.id,
        execution_id="exec-routing",
        variables={
            "input_query": "Route to DeepSeek please",
            "requirements": {"max_cost_per_call": 0.01},
        },
    )

    await engine._execute_workflow_async(workflow, execution, user_ctx)

    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.variables["routing_result"]["provider"] == "deepseek"
    assert recorded["query"] == "Route to DeepSeek please"
    assert recorded["context"] == {"requirements": {"max_cost_per_call": 0.01}}

