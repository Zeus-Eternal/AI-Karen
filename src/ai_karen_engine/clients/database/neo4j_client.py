"""
KnowledgeGraphClient (Neo4j): Handles all knowledge graph ops for Kari AI.
- Entity/concept nodes, property bags, edges (typed relationships), and concept queries.
- Uses py2neo, local Docker Neo4j recommended.
"""
# pyright: reportMissingImports=false
# cspell:ignore py2neo

import logging
from typing import Any, Dict, Iterator, List, Optional, Protocol, cast


class _MatchResultProtocol(Protocol):
    def first(self) -> Any: ...
    def __iter__(self) -> Iterator[Any]: ...


class _GraphProtocol(Protocol):
    def push(self, entity: Any) -> None: ...
    def create(self, entity: Any) -> None: ...
    def delete(self, entity: Any) -> None: ...
    def separate(self, relationship: Any) -> None: ...
    def run(self, cypher: str, **params: Any) -> Iterator[Dict[str, Any]]: ...


class _NodeMatcherProtocol(Protocol):
    def match(self, label: str, **kwargs: Any) -> _MatchResultProtocol: ...


class _RelationshipMatcherProtocol(Protocol):
    def match(self, nodes: tuple[Any, Any], r_type: str) -> _MatchResultProtocol: ...

try:
    from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher  # type: ignore
    _PY2NEO_AVAILABLE = True
except ImportError:
    _PY2NEO_AVAILABLE = False

    class Graph:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("py2neo is not installed")

    class Node(dict):  # type: ignore[no-redef]
        pass

    class Relationship(dict):  # type: ignore[no-redef]
        pass

    class NodeMatcher:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("py2neo is not installed")

    class RelationshipMatcher:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("py2neo is not installed")

class KnowledgeGraphClient:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="changeme"):
        if not _PY2NEO_AVAILABLE:
            raise ImportError("py2neo is not installed")
        graph = Graph(uri, auth=(user, password))
        self.graph = cast(_GraphProtocol, graph)
        self.matcher = cast(_NodeMatcherProtocol, NodeMatcher(graph))
        self.rel_matcher = cast(_RelationshipMatcherProtocol, RelationshipMatcher(graph))

    # --- NODE CRUD ---
    def upsert_node(self, label, properties):
        node = self.matcher.match(label, **{k:v for k,v in properties.items() if k=='id'}).first()
        if node:
            for k, v in properties.items():
                node[k] = v
            self.graph.push(node)
        else:
            node = Node(label, **properties)
            self.graph.create(node)
        return node

    def get_node(self, label, **kwargs):
        return self.matcher.match(label, **kwargs).first()

    def find_nodes(self, label, **kwargs):
        return list(self.matcher.match(label, **kwargs))

    def delete_node(self, label, **kwargs):
        node = self.matcher.match(label, **kwargs).first()
        if node:
            self.graph.delete(node)

    # --- RELATIONSHIP CRUD ---
    def upsert_relationship(self, label1, props1, rel_type, label2, props2, rel_props=None):
        node1 = self.upsert_node(label1, props1)
        node2 = self.upsert_node(label2, props2)
        rel = self.rel_matcher.match((node1, node2), r_type=rel_type).first()
        if rel:
            if rel_props:
                for k, v in rel_props.items():
                    rel[k] = v
                self.graph.push(rel)
        else:
            rel = cast(Any, Relationship)(node1, rel_type, node2, **(rel_props or {}))
            self.graph.create(rel)
        return rel

    def get_relationship(self, label1, props1, rel_type, label2, props2):
        node1 = self.get_node(label1, **props1)
        node2 = self.get_node(label2, **props2)
        if node1 and node2:
            return self.rel_matcher.match((node1, node2), r_type=rel_type).first()
        return None

    def delete_relationship(self, label1, props1, rel_type, label2, props2):
        rel = self.get_relationship(label1, props1, rel_type, label2, props2)
        if rel:
            self.graph.separate(rel)

    # --- CONCEPT QUERIES ---
    def find_related_concepts(self, node_label, node_props, rel_type=None, depth=1):
        node = self.get_node(node_label, **node_props)
        if not node:
            return []
        cypher = (
            f"MATCH (n:{node_label} {{{', '.join([f'{k}: ${k}' for k in node_props.keys()])}}})"
            f"-[r{':'+rel_type if rel_type else ''}*1..{depth}]-(m) "
            f"RETURN m, r"
        )
        result = self.graph.run(cypher, **node_props)
        concepts = []
        for record in result:
            m = record['m']
            concepts.append(dict(m))
        return concepts

    def get_concept_graph(self, node_label, node_props, depth=2):
        node = self.get_node(node_label, **node_props)
        if not node:
            return []
        cypher = (
            f"MATCH p=(n:{node_label} {{{', '.join([f'{k}: ${k}' for k in node_props.keys()])}}})"
            f"-[*1..{depth}]-(m) RETURN p"
        )
        return [record['p'] for record in self.graph.run(cypher, **node_props)]

    # --- Health/Admin ---
    def health(self):
        try:
            self.graph.run("RETURN 1")
            return True
        except Exception as ex:
            logging.warning(f"Neo4j healthcheck failed: {ex}")
            return False

    def clear_all(self):
        self.graph.run("MATCH (n) DETACH DELETE n")
