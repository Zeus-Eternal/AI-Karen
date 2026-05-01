from ai_karen_engine.core.memory.graph.config import LeanGraphConfig


def test_leangraph_config_defaults_valid():
    cfg = LeanGraphConfig.from_env()
    assert cfg.graph_backend in {"kuzu", "memgraph"}
    assert cfg.graph_max_entities_per_event > 0
