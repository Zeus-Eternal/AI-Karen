from ai_karen_engine.core.mesh_planner import MeshPlanner


def test_graph_crud():
    planner = MeshPlanner()
    planner.create_node("A", role="entity")
    planner.create_node("B")
    planner.create_edge("A", "B", weight=1)
    assert planner.graph.get_node("A")["role"] == "entity"
    assert planner.graph.get_edge("A", "B")["weight"] == 1
    planner.graph.nodes["A"]["role"] = "updated"
    assert planner.graph.get_node("A")["role"] == "updated"
    planner.graph.delete_edge("A", "B")
    assert planner.graph.multi_hop("A", "B") is None
    planner.graph.delete_node("A")
    assert planner.graph.get_node("A") is None


def test_multi_hop_query():
    planner = MeshPlanner()
    for n in ["A", "B", "C"]:
        planner.create_node(n)
    planner.create_edge("A", "B")
    planner.create_edge("B", "C")
    path = planner.multi_hop_query("A", "C", max_hops=2)
    assert path == ["A", "B", "C"]


def test_plugin_chain():
    planner = MeshPlanner()
    planner.create_node("one")
    planner.create_node("two")
    planner.create_edge("one", "two")

    handlers = {
        "one": lambda d: d.append("1"),
        "two": lambda d: d.append("2"),
    }

    path = planner.multi_hop_query("one", "two")
    data: list[str] = []
    for step in path or []:
        handlers[step](data)
    assert data == ["1", "2"]
