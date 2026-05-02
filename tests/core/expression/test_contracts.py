from ai_karen_engine.core.expression.contracts import ExpressionTask

def test_expression_task_contract():
    t = ExpressionTask(task_id='1', kind='chat', messages=[], response_mode='text', required_capabilities=[], forbidden_capabilities=[])
    assert t.timeout_ms == 30000
