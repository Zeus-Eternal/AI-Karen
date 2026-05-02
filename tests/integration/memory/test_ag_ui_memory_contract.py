import inspect
from ai_karen_engine.services.ui.ag_ui_memory_manager import AGUIMemoryManager


def test_agui_methods_are_async():
    assert inspect.iscoroutinefunction(AGUIMemoryManager.get_memory_grid_data)
    assert inspect.iscoroutinefunction(AGUIMemoryManager.search_memories)
