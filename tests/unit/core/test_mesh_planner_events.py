from ai_karen_engine.core.mesh_planner import MeshPlanner
from ai_karen_engine.event_bus import get_event_bus


def test_mesh_planner_publishes_events():
    bus = get_event_bus()
    bus.consume()  # clear any existing events
    planner = MeshPlanner()
    planner.create_node("A")
    planner.create_edge("A", "B")
    planner.multi_hop_query("A", "B")
    events = bus.consume(["admin"])
    types = [e.event_type for e in events]
    assert "node_created" in types
    assert "edge_created" in types
    assert "multi_hop_query" in types
