from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List, Optional


class ReasoningGraph:
    """Lightweight in-memory graph for capsule reasoning."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[tuple[str, str], Dict[str, Any]] = {}
        self.adj: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, name: str, **attrs: Any) -> None:
        self.nodes[name] = attrs

    def add_edge(self, src: str, dst: str, **attrs: Any) -> None:
        self.adj[src].append(dst)
        self.edges[(src, dst)] = attrs

    def get_node(self, name: str) -> Dict[str, Any] | None:
        return self.nodes.get(name)

    def get_edge(self, src: str, dst: str) -> Dict[str, Any] | None:
        return self.edges.get((src, dst))

    def delete_node(self, name: str) -> None:
        self.nodes.pop(name, None)
        self.adj.pop(name, None)
        for neighbors in self.adj.values():
            if name in neighbors:
                neighbors.remove(name)
        for key in list(self.edges.keys()):
            if name in key:
                del self.edges[key]

    def delete_edge(self, src: str, dst: str) -> None:
        if dst in self.adj.get(src, []):
            self.adj[src].remove(dst)
        self.edges.pop((src, dst), None)

    def multi_hop(self, start: str, end: str, max_hops: int = 3) -> Optional[List[str]]:
        queue: deque[tuple[str, List[str]]] = deque([(start, [start])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            if len(path) - 1 > max_hops:
                continue
            if node == end:
                return path
            for nxt in self.adj.get(node, []):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [nxt]))
        return None

    def visualize_cli(self) -> str:
        lines = []
        for src, dsts in self.adj.items():
            for dst in dsts:
                lines.append(f"{src} -> {dst}")
        return "\n".join(sorted(lines))
