import json
import os
from pathlib import Path

import pytest

from ai_karen_engine.config.user_profiles import (
    get_user_profiles_manager,
    UserProfile,
    ModelAssignment,
)
from ai_karen_engine.routing.profile_resolver import ProfileResolver


def test_profiles_manager_crud_and_resolver(tmp_path: Path, monkeypatch):
    # Point config to a temp file
    cfg_path = tmp_path / "config.json"
    os.environ["KARI_CONFIG_FILE"] = str(cfg_path)

    # Seed minimal config
    cfg_path.write_text(json.dumps({}))

    upm = get_user_profiles_manager()
    # Ensure default exists
    default = upm.ensure_default_profile()
    assert default.is_active

    # Create a new profile with explicit chat assignment to deepseek
    prof = UserProfile(
        id="dev_profile",
        name="Dev Profile",
        assignments={
            "chat": ModelAssignment("chat", "deepseek", "deepseek-chat"),
        },
        is_active=False,
    )
    upm.create_profile(prof)
    upm.set_active_profile("dev_profile")

    # Resolver should now reflect new active profile
    pr = ProfileResolver()
    uprof = pr.get_user_profile(user_id="u1")
    assert uprof is not None
    ma = pr.get_model_assignment(uprof, task_type="chat")
    assert ma is not None
    assert ma.provider == "deepseek"
    assert ma.model == "deepseek-chat"

