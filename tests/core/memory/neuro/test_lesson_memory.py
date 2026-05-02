from ai_karen_engine.core.memory.neuro.lesson_memory import LessonMemoryStore
from ai_karen_engine.core.memory.neuro.contracts import LessonArtifact


def test_lesson_store_roundtrip():
    s = LessonMemoryStore()
    s.put('t', LessonArtifact(id='1', lesson_type='correction', failure_signature='local_gguf', correction='do not use', applies_to=['routing']))
    assert len(s.recall('t', 'local_gguf')) == 1
