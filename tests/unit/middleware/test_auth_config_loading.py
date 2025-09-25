from pathlib import Path

import pytest
import yaml

from ai_karen_engine.auth.config import AuthConfig


def write_config(path: Path, data):
    path.write_text(yaml.safe_dump(data))
    return path


def test_from_file_selects_environment(tmp_path):
    data = {
        "development": {
            "database": {"database_url": "sqlite:///./dev.db"},
            "jwt": {"secret_key": "dev-secret"},
        },
        "production": {
            "database": {"database_url": "postgresql://user:pass@db/prod"},
            "jwt": {"secret_key": "prod-secret"},
        },
    }
    cfg_path = write_config(tmp_path / "auth.yaml", data)
    cfg = AuthConfig.from_file(cfg_path, "development")
    assert cfg.environment == "development"
    assert cfg.database.database_url.startswith("sqlite")
    assert cfg.jwt.secret_key == "dev-secret"


def test_from_environment_discovers_file(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "auth_config.yaml").write_text(
        yaml.safe_dump(
            {
                "development": {
                    "database": {"database_url": "sqlite:///./dev.db"},
                    "jwt": {"secret_key": "dev-secret"},
                }
            }
        )
    )
    cfg = AuthConfig.from_environment("development", config_dir=config_dir)
    assert cfg.database.database_url.endswith("dev.db")


def test_production_requires_secret(tmp_path):
    data = {
        "production": {
            "database": {"database_url": "postgresql://user:pass@db/prod"}
        }
    }
    cfg_path = write_config(tmp_path / "auth.yaml", data)
    with pytest.raises(ValueError):
        AuthConfig.from_file(cfg_path, "production")
