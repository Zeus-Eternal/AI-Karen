import time

import numpy as np  # type: ignore

from ai_karen_engine.core.milvus_client import MilvusClient  # type: ignore


def benchmark(index_type: str) -> float:
    dim = 128
    client = MilvusClient(dim=dim, index_type=index_type)
    rng = np.random.default_rng(0)
    for vec in rng.random((1000, dim), dtype=np.float32):
        client.upsert(vec.tolist(), {})
    latencies = []
    for q in rng.random((100, dim), dtype=np.float32):
        start = time.time()
        client.search_sync(q.tolist(), top_k=5)
        latencies.append(time.time() - start)
    return float(np.percentile(latencies, 95) * 1000)


if __name__ == "__main__":
    flat = benchmark("flat")
    hnsw = benchmark("hnsw")
    print(f"flat p95: {flat:.2f} ms")
    print(f"hnsw p95: {hnsw:.2f} ms")
