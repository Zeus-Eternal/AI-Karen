"""Modular API route collection for Kari."""

from ai_karen_engine.utils.dependency_checks import import_fastapi

APIRouter = import_fastapi("APIRouter")

router = APIRouter()
