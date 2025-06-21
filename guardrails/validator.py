"""Validate tool parameters based on simple YAML rules."""

from __future__ import annotations

import re
from typing import Any, Dict


class ValidationError(Exception):
    pass


def validate(rules: Dict[str, Any], params: Dict[str, Any]) -> None:
    for name, cfg in rules.items():
        value = params.get(name)
        if value is None:
            raise ValidationError(f"missing {name}")
        if "regex" in cfg and not re.match(cfg["regex"], str(value)):
            raise ValidationError(f"{name} invalid")
        if "enum" in cfg and value not in cfg["enum"]:
            raise ValidationError(f"{name} not allowed")
