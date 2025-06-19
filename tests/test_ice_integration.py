from core.reasoning.ice_integration import KariICEWrapper


def test_process_returns_keys():
    wrapper = KariICEWrapper()
    result = wrapper.process("Why do we dream?")
    assert "entropy" in result
    assert "memory_matches" in result
