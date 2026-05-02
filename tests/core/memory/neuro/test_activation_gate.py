from ai_karen_engine.core.memory.neuro.activation_gate import decide_activation_mode


def test_activation_profile_for_preference():
    d = decide_activation_mode(query="What's my favorite food?")
    assert d.mode.value == "profile"
