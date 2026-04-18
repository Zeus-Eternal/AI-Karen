"""Organizational hierarchy router for knowledge queries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

from ai_karen_engine.services.knowledge.index_hub import Department, Team, KnowledgeQuery


class IntentType(str, Enum):
    GENERAL = "general"


@dataclass
class RouteDecision:
    department: Department
    team: Team | None
    intent_type: IntentType
    confidence: float
    reasoning: str


class OrganizationalHierarchy:
    def __init__(self) -> None:
        self.intent_patterns = {"general": ["*"]}
        self.routing_rules = ["default_engineering"]

    async def process_query_with_routing(self, query_text: str, index_hub) -> Tuple[RouteDecision, List]:
        route = RouteDecision(
            department=Department.ENGINEERING,
            team=Team.BACKEND,
            intent_type=IntentType.GENERAL,
            confidence=0.6,
            reasoning="default routing",
        )
        results = await index_hub.search(KnowledgeQuery(text=query_text))
        return route, results


__all__ = ["OrganizationalHierarchy", "RouteDecision", "IntentType"]
