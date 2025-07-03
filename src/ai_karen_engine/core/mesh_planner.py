from __future__ import annotations

from typing import Any, List, Optional

try:
    from neo4j import GraphDatabase  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    GraphDatabase = None

from .reasoning import ReasoningGraph


class MeshPlanner:
    """Reasoning mesh planner with optional Neo4j sync."""

    def __init__(
        self,
        neo4j_url: str | None = None,
        *,
        neo4j_user: str = "",
        neo4j_password: str = "",
    ) -> None:
        self.graph = ReasoningGraph()
        self.driver = None
        if neo4j_url and GraphDatabase is not None:
            try:
                self.driver = GraphDatabase.driver(
                    neo4j_url, auth=(neo4j_user, neo4j_password)
                )
            except Exception:
                self.driver = None

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def create_node(self, name: str, **attrs: Any) -> None:
        self.graph.add_node(name, **attrs)
        if self.driver:
            with self.driver.session() as session:  # pragma: no cover - optional
                session.run(
                    "MERGE (n:Concept {name: $name}) SET n += $attrs",
                    name=name,
                    attrs=attrs,
                )

    def create_edge(self, src: str, dst: str, **attrs: Any) -> None:
        self.graph.add_edge(src, dst, **attrs)
        if self.driver:
            with self.driver.session() as session:  # pragma: no cover - optional
                session.run(
                    "MATCH (a:Concept {name: $src}), (b:Concept {name: $dst}) "
                    "MERGE (a)-[r:RELATED]->(b) SET r += $attrs",
                    src=src,
                    dst=dst,
                    attrs=attrs,
                )

    def multi_hop_query(
        self, start: str, end: str, max_hops: int = 3
    ) -> Optional[List[str]]:
        return self.graph.multi_hop(start, end, max_hops)

    def visualize(self) -> str:
        return self.graph.visualize_cli()
