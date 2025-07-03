import sys
from types import ModuleType

import cli


def ensure_optional_dependency(name: str):
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)


def test_self_test_output(capsys):
    for dep in ["pyautogui", "urwid"]:
        ensure_optional_dependency(dep)
    cli.self_test()
    out = capsys.readouterr().out
    assert "Self test summary:" in out
    assert "plugins:" in out
