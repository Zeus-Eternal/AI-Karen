from .contracts import ResponseTask

def build_response_task(task_id: str, messages: list[dict]):
    return ResponseTask(task_id=task_id, messages=messages)
