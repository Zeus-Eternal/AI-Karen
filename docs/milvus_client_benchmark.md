# MilvusClient ANN Benchmark

The benchmark measures search latency for the in-memory `MilvusClient` using
linear (flat) search versus the new HNSW index backed by `hnswlib`.

## Setup
- 1000 random 128-dimensional vectors
- 100 random search queries (top-5)
- p95 latency reported in milliseconds

## Results
| Index Type | p95 Latency (ms) |
|------------|-----------------|
| flat       | 7.82            |
| hnsw       | 0.09            |
