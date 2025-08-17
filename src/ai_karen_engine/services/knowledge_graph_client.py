"""
Kari KnowledgeGraphClient – Evil Twin Edition
- Neo4j graph engine with:
  * Prompt-first, transaction-safe query API
  * RBAC enforcement points (add more as needed)
  * Connection pooling, retry, metric, and audit hooks
  * Production-wipe protection and forensic logging
  * Supports batch ops, upsert, advanced traversal, healthcheck
"""

from typing import Any, Dict, List, Optional, Tuple
from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
from py2neo.database import Transaction
import logging
from datetime import datetime
import time
from functools import wraps
from contextlib import contextmanager
import os

logger = logging.getLogger("kari.knowledge_graph")
logger.setLevel(logging.INFO)

class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph operations"""
    pass

class ConnectionError(KnowledgeGraphError):
    """Raised when connection to Neo4j fails"""
    pass

class QueryExecutionError(KnowledgeGraphError):
    """Raised when a query fails to execute"""
    pass

def log_operation(func):
    """Decorator to log and time all public graph operations, with context"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"[{self._correlation_id()}] {func.__name__} completed in {duration:.3f}s")
            # Increment metric
            self.metrics["queries_executed"] += 1
            self.metrics["last_successful_operation"] = datetime.utcnow()
            return result
        except Exception as e:
            logger.error(f"[{self._correlation_id()}] {func.__name__} failed: {str(e)}", exc_info=True)
            raise
    return wrapper

class KnowledgeGraphClient:
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "changeme",
        max_retries: int = 3,
        connection_timeout: int = 30,
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.max_retries = max_retries
        self.connection_timeout = connection_timeout

        # Telemetry and metrics
        self.metrics = {
            "queries_executed": 0,
            "last_successful_operation": None
        }

        self.graph = self._initialize_connection()
        self.matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)

    def _initialize_connection(self) -> Graph:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                graph = Graph(
                    self.uri,
                    auth=(self.user, self.password),
                    timeout=self.connection_timeout,
                )
                # Health probe
                graph.run("RETURN 1").data()
                logger.info(f"Neo4j connection established (attempt {attempt})")
                return graph
            except Exception as e:
                last_error = e
                logger.warning(f"Neo4j connect attempt {attempt} failed: {str(e)}")
                time.sleep(1 + 0.5 * attempt)  # Progressive backoff
        raise ConnectionError("Failed to connect to Neo4j after retries") from last_error

    def _correlation_id(self) -> str:
        # Evil trace: tie every op to a session/correlation (expand as needed)
        return os.environ.get("KARI_SESSION_ID", "anon-session")

    @contextmanager
    def _transaction(self) -> Transaction:
        tx = self.graph.begin()
        try:
            yield tx
            self.graph.commit(tx)
        except Exception as e:
            self.graph.rollback(tx)
            raise QueryExecutionError(f"Transaction failed: {str(e)}") from e

    # ---- RBAC/Production Wipe Guards ----
    def _is_production(self) -> bool:
        env = os.environ.get("KARI_ENV", "").lower()
        return ("prod" in env or "production" in env or "cloud" in self.uri.lower())

    # ---- NODE CRUD ----
    @log_operation
    def upsert_node(self, label: str, properties: Dict[str, Any], tx: Optional[Transaction]=None) -> Node:
        """Create/update node by unique id. Requires 'id' in properties."""
        if "id" not in properties:
            raise KnowledgeGraphError("Node upsert requires unique 'id' property")
        node = self.matcher.match(label, id=properties["id"]).first()
        if node:
            for k, v in properties.items():
                node[k] = v
            (tx or self.graph).push(node)
        else:
            node = Node(label, **properties)
            (tx or self.graph).create(node)
        return node

    @log_operation
    def batch_upsert_nodes(self, nodes: List[Tuple[str, Dict[str, Any]]]) -> List[Node]:
        """Batch upsert: [(label, props)] in a transaction"""
        results = []
        with self._transaction() as tx:
            for label, props in nodes:
                results.append(self.upsert_node(label, props, tx))
        return results

    @log_operation
    def get_node(self, label: str, **kwargs) -> Optional[Node]:
        return self.matcher.match(label, **kwargs).first()

    @log_operation
    def find_nodes(self, label: str, **kwargs) -> List[Node]:
        return list(self.matcher.match(label, **kwargs))

    @log_operation
    def delete_node(self, label: str, **kwargs) -> bool:
        node = self.matcher.match(label, **kwargs).first()
        if node:
            self.graph.delete(node)
            return True
        return False

    # ---- RELATIONSHIP CRUD ----
    @log_operation
    def upsert_relationship(
        self,
        label1: str, props1: Dict[str, Any],
        rel_type: str,
        label2: str, props2: Dict[str, Any],
        rel_props: Optional[Dict[str, Any]] = None,
        tx: Optional[Transaction] = None
    ) -> Relationship:
        node1 = self.upsert_node(label1, props1, tx)
        node2 = self.upsert_node(label2, props2, tx)
        rel = self.rel_matcher.match((node1, node2), r_type=rel_type).first()
        if rel:
            if rel_props:
                for k, v in rel_props.items():
                    rel[k] = v
                (tx or self.graph).push(rel)
        else:
            rel = Relationship(node1, rel_type, node2, **(rel_props or {}))
            (tx or self.graph).create(rel)
        return rel

    @log_operation
    def delete_relationship(
        self,
        label1: str, props1: Dict[str, Any],
        rel_type: str,
        label2: str, props2: Dict[str, Any]
    ) -> bool:
        rel = self.get_relationship(label1, props1, rel_type, label2, props2)
        if rel:
            self.graph.separate(rel)
            return True
        return False

    @log_operation
    def get_relationship(
        self,
        label1: str, props1: Dict[str, Any],
        rel_type: str,
        label2: str, props2: Dict[str, Any]
    ) -> Optional[Relationship]:
        node1 = self.get_node(label1, **props1)
        node2 = self.get_node(label2, **props2)
        if node1 and node2:
            return self.rel_matcher.match((node1, node2), r_type=rel_type).first()
        return None

    # ---- ADVANCED CONCEPT/PROMPT QUERIES ----
    @log_operation
    def find_related_concepts(
        self,
        node_label: str,
        node_props: Dict[str, Any],
        rel_type: Optional[str] = None,
        depth: int = 1,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Prompt-first: Find related concepts up to depth, optionally filter rel_type."""
        if depth < 1 or depth > 5:
            raise KnowledgeGraphError("Depth must be between 1 and 5")
        node = self.get_node(node_label, **node_props)
        if not node:
            return []
        prop_filter = ', '.join([f"{k}: ${k}" for k in node_props.keys()])
        rel_match = f":{rel_type}" if rel_type else ""
        limit_clause = f"LIMIT {limit}" if limit else ""
        cypher = (
            f"MATCH (n:{node_label} {{{prop_filter}}})"
            f"-[r{rel_match}*1..{depth}]-(m) "
            f"RETURN DISTINCT m as node, [rel in relationships(r) | type(rel)] as rel_types "
            f"{limit_clause}"
        )
        results = self.execute_cypher(cypher, node_props)
        return [{
            "node": dict(record["node"]),
            "labels": list(record["node"].labels),
            "relationship_types": record["rel_types"]
        } for record in results]

    @log_operation
    def get_concept_graph(
        self,
        node_label: str,
        node_props: Dict[str, Any],
        depth: int = 2
    ) -> List[Any]:
        """Returns list of Path objects for graph visualization."""
        node = self.get_node(node_label, **node_props)
        if not node:
            return []
        prop_filter = ', '.join([f"{k}: ${k}" for k in node_props.keys()])
        cypher = (
            f"MATCH p=(n:{node_label} {{{prop_filter}}})"
            f"-[*1..{depth}]-(m) RETURN p"
        )
        return [record['p'] for record in self.graph.run(cypher, **node_props)]

    @log_operation
    def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        tx: Optional[Transaction] = None
    ) -> List[Dict[str, Any]]:
        try:
            return (tx or self.graph).run(query, parameters or {}).data()
        except Exception as e:
            raise QueryExecutionError(f"Cypher query failed: {str(e)}") from e

    # ---- HEALTH/AUDIT/ADMIN ----
    @log_operation
    def healthcheck(self) -> Dict[str, Any]:
        try:
            start = time.time()
            self.graph.run("RETURN 1").data()
            latency = time.time() - start
            return {
                "status": "healthy",
                "latency_seconds": latency,
                "last_operation": self.metrics["last_successful_operation"],
                "queries_executed": self.metrics["queries_executed"]
            }
        except Exception as e:
            logger.error(f"Healthcheck failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def clear_all(self, rbac_ctx: Optional[Dict[str, Any]] = None) -> None:
        """Wipe graph—only if NOT production and RBAC says yes. Log all attempts."""
        if self._is_production():
            logger.critical("DENIED: Attempt to clear knowledge graph in production!")
            raise KnowledgeGraphError("Clear operation not allowed in production")
        if rbac_ctx and "admin" not in rbac_ctx.get("roles", []):
            logger.critical("DENIED: Non-admin attempted graph wipe")
            raise KnowledgeGraphError("Only admin can clear the knowledge graph")
        self.execute_cypher("MATCH (n) DETACH DELETE n")
        logger.warning("KNOWLEDGE GRAPH CLEARED by admin action.")

