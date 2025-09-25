import pytest
from ai_karen_engine.extensions.workflow_engine import WorkflowEngine
from unittest.mock import Mock


@pytest.fixture
def workflow_engine():
    return WorkflowEngine(Mock())


def test_complex_valid_conditions(workflow_engine):
    variables = {"count": 5, "status": "active"}
    assert workflow_engine._evaluate_condition("${count} + 2 == 7", variables)
    assert workflow_engine._evaluate_condition(
        "${count} > 3 and ${status} == 'active'", variables
    )
    assert not workflow_engine._evaluate_condition(
        "${count} < 3 or ${status} == 'inactive'", variables
    )
    assert workflow_engine._evaluate_condition("not (${status} != 'active')", variables)


def test_invalid_conditions_return_false(workflow_engine):
    variables = {"count": 5}
    assert not workflow_engine._evaluate_condition("${count} >>> 1", variables)
    assert not workflow_engine._evaluate_condition(
        "__import__('os').system('echo hi')", variables
    )
