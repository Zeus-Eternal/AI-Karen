import asyncio

from ai_karen_engine.core.reasoning.ice_integration import KariICEWrapper


def test_process_returns_keys():
    wrapper = KariICEWrapper()
    result = wrapper.process("Why do we dream?")
    assert "entropy" in result
    assert "memory_matches" in result
    assert "analysis" in result and result["analysis"]


def test_aprocess():
    wrapper = KariICEWrapper()
    result = asyncio.run(wrapper.aprocess("What is consciousness?"))
    assert "analysis" in result
