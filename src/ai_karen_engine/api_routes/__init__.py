"""Modular API route collection for Kari."""

from typing import Any, cast

from ai_karen_engine.utils.dependency_checks import import_fastapi

APIRouter = cast(Any, import_fastapi("APIRouter"))

router = APIRouter()
