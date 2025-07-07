import asyncio

from ui_launchers.backend.chat_hub import ChatHub, SlashCommand, NeuroVault

class DummyRouter:
    def __init__(self):
        self.messages = []

    def generate_reply(self, text: str) -> str:
        self.messages.append(text)
        return f"echo:{text}"


async def collect(gen):
    return "".join([chunk async for chunk in gen]).strip()


def test_nl_routing():
    hub = ChatHub(router=DummyRouter())
    reply = asyncio.run(collect(hub.stream_reply("hello", roles=["user"])))
    assert reply == "echo:hello"
    assert hub.memory.recall()[0] == "echo:hello"


def test_command_help():
    hub = ChatHub(router=DummyRouter())
    out = asyncio.run(collect(hub.stream_reply("/help", roles=["user"])))
    assert "help" in out


def test_memory_purge():
    hub = ChatHub(router=DummyRouter())
    asyncio.run(collect(hub.stream_reply("hi")))
    assert hub.memory.recall()
    asyncio.run(collect(hub.stream_reply("/purge", roles=["dev"])))
    assert not hub.memory.recall()
