from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class Node:
    name: str
    attrs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    weight: float = 1.0
    attrs: Dict[str, Any] = field(default_factory=dict)


class CapsuleGraph:
    """Lightweight in-memory directed graph for capsule reasoning.

    Features:
    - Idempotent upserts for nodes/edges
    - Optional edge weights
    - BFS multi-hop path search with hop cap
    - Dijkstra shortest path by weight
    - CLI and DOT visualizations
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[Tuple[str, str], Edge] = {}
        self._adj: Dict[str, List[str]] = defaultdict(list)

    # -------------------------
    # Node operations
    # -------------------------
    def add_node(self, name: str, **attrs: Any) -> None:
        if name in self._nodes:
            self._nodes[name].attrs.update(attrs)
        else:
            self._nodes[name] = Node(name=name, attrs=dict(attrs))

    def upsert_node(self, name: str, **attrs: Any) -> None:
        self.add_node(name, **attrs)

    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        n = self._nodes.get(name)
        return dict(n.attrs) if n else None

    def has_node(self, name: str) -> bool:
        return name in self._nodes

    def delete_node(self, name: str) -> None:
        if name not in self._nodes:
            return
        # remove outgoing adjacency
        self._adj.pop(name, None)
        # remove incoming adjacency
        for neighbors in self._adj.values():
            while name in neighbors:
                neighbors.remove(name)
        # remove edges touching the node
        for key in list(self._edges.keys()):
            if name in key:
                del self._edges[key]
        # finally remove node
        del self._nodes[name]

    # -------------------------
    # Edge operations
    # -------------------------
    def add_edge(self, src: str, dst: str, *, weight: float = 1.0, **attrs: Any) -> None:
        self.add_node(src)
        self.add_node(dst)
        if dst not in self._adj[src]:
            self._adj[src].append(dst)
        self._edges[(src, dst)] = Edge(src=src, dst=dst, weight=float(weight), attrs=dict(attrs))

    def upsert_edge(self, src: str, dst: str, *, weight: float = 1.0, **attrs: Any) -> None:
        self.add_edge(src, dst, weight=weight, **attrs)

    def delete_edge(self, src: str, dst: str) -> None:
        if dst in self._adj.get(src, []):
            self._adj[src].remove(dst)
        self._edges.pop((src, dst), None)

    def get_edge(self, src: str, dst: str) -> Optional[Dict[str, Any]]:
        e = self._edges.get((src, dst))
        if not e:
            return None
        out = dict(e.attrs)
        out["weight"] = e.weight
        return out

    def has_edge(self, src: str, dst: str) -> bool:
        return (src, dst) in self._edges

    # -------------------------
    # Queries
    # -------------------------
    def neighbors(self, name: str) -> List[str]:
        return list(self._adj.get(name, []))

    def degree(self, name: str) -> int:
        return len(self._adj.get(name, []))

    def nodes(self) -> List[str]:
        return list(self._nodes.keys())

    def edges(self) -> List[Tuple[str, str]]:
        return list(self._edges.keys())

    # -------------------------
    # Path finding
    # -------------------------
    def multi_hop(self, start: str, end: str, max_hops: int = 3) -> Optional[List[str]]:
        """BFS path up to max_hops edges (minimizes hops)."""
        if start not in self._nodes or end not in self._nodes:
            return None
        queue: deque[Tuple[str, List[str]]] = deque([(start, [start])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            if len(path) - 1 > max_hops:
                continue
            if node == end:
                return path
            for nxt in self._adj.get(node, []):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [nxt]))
        return None

    def shortest_path(self, start: str, end: str) -> Optional[Tuple[float, List[str]]]:
        """Dijkstra on edge weights; returns (total_weight, path)."""
        if start not in self._nodes or end not in self._nodes:
            return None
        import heapq
        dist: Dict[str, float] = {start: 0.0}
        prev: Dict[str, Optional[str]] = {start: None}
        pq: List[Tuple[float, str]] = [(0.0, start)]
        visited: set[str] = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            if u == end:
                # reconstruct
                path: List[str] = []
                cur: Optional[str] = end
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                path.reverse()
                return (d, path)

            for v in self._adj.get(u, []):
                w = self._edges[(u, v)].weight
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return None

    # -------------------------
    # Visualization
    # -------------------------
    def visualize_cli(self) -> str:
        lines = []
        for src, dsts in self._adj.items():
            for dst in dsts:
                w = self._edges[(src, dst)].weight
                lines.append(f"{src} -[{w}]-> {dst}")
        return "\n".join(sorted(lines))

    def to_dot(self, *, rankdir: str = "LR") -> str:
        """Graphviz DOT for nicer previews."""
        parts = [f'digraph CapsuleGraph {{ rankdir="{rankdir}";']
        for n in self._nodes.values():
            label = n.name.replace('"', '\\"')
            parts.append(f'  "{n.name}" [label="{label}"];')
        for (src, dst), e in self._edges.items():
            parts.append(f'  "{src}" -> "{dst}" [label="{e.weight}"];')
        parts.append("}")
        return "\n".join(parts)

    # -------------------------
    # Bulk helpers
    # -------------------------
    def add_path(self, nodes: Iterable[str], *, weight: float = 1.0, **edge_attrs: Any) -> None:
        seq = list(nodes)
        for i in range(len(seq) - 1):
            self.add_edge(seq[i], seq[i + 1], weight=weight, **edge_attrs)
