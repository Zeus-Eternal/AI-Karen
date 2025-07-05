import asyncio

from ..src.ai_karen_engine.core.reasoning.ice_integration import KariICEWrapper


def test_multi_hop_flow():
    wrapper = KariICEWrapper()
    wrapper.process("The Earth revolves around the Sun.")
    result = wrapper.process("What does the Earth revolve around?")
    assert result["memory_matches"]
    assert "Earth" in result["analysis"]


def test_async_multi_hop():
    wrapper = KariICEWrapper()
    wrapper.process("Water freezes at 0 degrees Celsius.")
    out = asyncio.run(wrapper.aprocess("When does water freeze?"))
    assert out["memory_matches"]
