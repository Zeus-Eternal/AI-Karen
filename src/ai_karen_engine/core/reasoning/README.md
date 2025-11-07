# Reasoning Module - AI Karen Engine

This module implements advanced reasoning capabilities for the AI Karen Engine, aligned with the research paper:

**"Soft Reasoning: Navigating Solution Spaces in Large Language Models through Controlled Embedding Exploration"**

📄 Paper: [OpenReview](https://openreview.net/forum?id=4gWE7CMOlH)

## Overview

The Soft Reasoning approach enables efficient navigation of solution spaces through controlled embedding exploration, achieving better accuracy with minimal computational overhead compared to traditional methods.

### Key Benefits

- ✅ **Improved Accuracy**: Better reasoning quality through guided embedding optimization
- ⚡ **Efficient**: Drastically reduced token consumption (~6% of baseline methods)
- 🎯 **Controlled Exploration**: Balanced exploration-exploitation via Bayesian optimization
- 🔍 **Verifier-Guided**: Quality-driven optimization using multi-criteria verification

## Architecture

```
reasoning/
├── soft_reasoning/          # Core Soft Reasoning implementation
│   ├── engine.py           # Main SR engine with dual-embedding & recency
│   ├── perturbation.py     # Controlled embedding perturbation
│   ├── optimization.py     # Bayesian optimization for refinement
│   └── verifier.py         # Verifier-guided quality objectives
├── graph/                   # Graph-based reasoning structures
│   ├── capsule.py          # CapsuleGraph for reasoning paths
│   └── reasoning.py        # ReasoningGraph facade
├── retrieval/               # Vector store & retrieval adapters
│   ├── adapters.py         # SR retriever protocols
│   └── vector_stores.py    # VectorStore implementations
├── synthesis/               # ICE integration & synthesis
│   ├── ice_wrapper.py      # Premium ICE wrapper
│   └── subengines.py       # Synthesis sub-engines
└── causal/                  # Causal reasoning (Pearl's hierarchy)
    └── engine.py           # Causal inference & counterfactuals
```

## Core Components

### 1. Soft Reasoning Engine (`soft_reasoning/engine.py`)

Main retrieval and reasoning engine with:
- **Dual-embedding approach**: Fast prefiltering + precise reranking
- **Recency-aware scoring**: Time-weighted relevance
- **Novelty gate**: Entropy-based filtering for ingestion
- **TTL management**: Automatic expiration of stale memories

```python
from ai_karen_engine.core.reasoning import SoftReasoningEngine

engine = SoftReasoningEngine()
results = engine.query("What is the status of Project X?", top_k=5)
engine.ingest("Project X completed successfully", {"timestamp": 1234567890})
```

### 2. Embedding Perturbation (`soft_reasoning/perturbation.py`)

Implements controlled perturbation strategies for exploring the embedding space:

- **Gaussian**: Random noise with configurable variance
- **Directional**: Guided perturbation toward target regions
- **Adaptive**: Variance adapts based on confidence (low confidence → more exploration)
- **Diverse**: Maximize diversity from explored embeddings
- **Hybrid**: Combine multiple strategies

```python
from ai_karen_engine.core.reasoning import EmbeddingPerturber, PerturbationStrategy

perturber = EmbeddingPerturber(strategy=PerturbationStrategy.ADAPTIVE)
perturbed = perturber.perturb(embedding, confidence=0.7)

# Generate multiple candidates for parallel exploration
candidates = perturber.perturb_batch(embedding, num_perturbations=10)
```

### 3. Bayesian Optimization (`soft_reasoning/optimization.py`)

Refines embeddings using Bayesian optimization with verifier feedback:

- **Gaussian Process surrogate model**: Efficient search through high-dimensional space
- **Acquisition functions**: UCB, EI, PI, Thompson Sampling
- **Exploration-exploitation balance**: Configurable via exploration weight
- **Convergence detection**: Stops when improvement threshold reached

```python
from ai_karen_engine.core.reasoning import BayesianOptimizer, AcquisitionFunction

optimizer = BayesianOptimizer()

def score_fn(embedding):
    # Score based on reasoning quality
    return verifier.verify(query, generate_response(embedding)).overall_score

result = optimizer.optimize(initial_embedding, score_fn)
best_embedding = result.best_embedding
```

### 4. Reasoning Verifier (`soft_reasoning/verifier.py`)

Provides verifier-guided objectives for quality assessment:

**Criteria**:
- **Correctness**: Factual accuracy
- **Coherence**: Logical consistency
- **Completeness**: Coverage of key points
- **Relevance**: Alignment with query
- **Confidence**: Model certainty

```python
from ai_karen_engine.core.reasoning import ReasoningVerifier

verifier = ReasoningVerifier()
result = verifier.verify(query="What causes rain?", response="...", context=[...])

print(f"Score: {result.overall_score:.2f}")
print(f"Passed: {result.passed}")
print(f"Feedback: {result.feedback}")
```

### 5. Graph-Based Reasoning (`graph/`)

**CapsuleGraph**: Lightweight directed graph for reasoning paths
- Node/edge operations with attributes
- BFS multi-hop path search
- Dijkstra shortest path by weight
- DOT visualization support

**ReasoningGraph**: High-level facade with ICE integration
- Combines SR engine + graph mirroring
- Explainability through graph visualization

```python
from ai_karen_engine.core.reasoning import ReasoningGraph

graph = ReasoningGraph()
trace = graph.run("Analyze the root cause of the system failure")

# Visualize reasoning graph
print(graph.visualize_capsule_cli())
```

### 6. Synthesis & ICE (`synthesis/`)

Premium Integrated Cognitive Engine wrapper:

**Features**:
- Multiple recall strategies (Semantic, Temporal, Hybrid, Cascade)
- Synthesis modes (Concise, Analytical, Action-Oriented, Multi-Perspective)
- Adaptive entropy thresholds
- Circuit breaker for resilience
- Token budget management
- Prometheus telemetry

```python
from ai_karen_engine.core.reasoning import (
    KariICEWrapper,
    ICEWritebackPolicy,
    RecallStrategy,
    SynthesisMode
)

policy = ICEWritebackPolicy(
    enable=True,
    adaptive_entropy=True,
    summary_style=SynthesisMode.ANALYTICAL
)

ice = KariICEWrapper(policy=policy, recall_strategy=RecallStrategy.CASCADE)
trace = ice.process("Explain the benefits of soft reasoning")

print(f"Synthesis: {trace.synthesis}")
print(f"Confidence: {trace.confidence_estimate:.2%}")
```

### 7. Causal Reasoning (`causal/`)

Implements Pearl's causal hierarchy:

**Level 1 - Association**: Observing correlations
**Level 2 - Intervention**: do-calculus (what if we do X?)
**Level 3 - Counterfactuals**: Imagining alternatives (what if we had done X?)

```python
from ai_karen_engine.core.reasoning import get_causal_engine

engine = get_causal_engine()
engine.learn_from_observations(observations)

# Estimate causal effect
effect = engine.estimate_causal_effect("training_hours", "model_accuracy")

# Model intervention
outcomes = engine.do_intervention("training_hours", value=100)

# Counterfactual reasoning
scenario = engine.generate_counterfactual(
    "What if we had doubled training data?",
    [("training_data", 2 * current_data)]
)
```

## Research Paper Alignment

### Paper Concepts → Implementation Mapping

| Paper Concept | Implementation | Module |
|--------------|----------------|---------|
| Embedding perturbation | `EmbeddingPerturber` | `soft_reasoning/perturbation.py` |
| Bayesian optimization | `BayesianOptimizer` | `soft_reasoning/optimization.py` |
| Verifier-guided objective | `ReasoningVerifier` | `soft_reasoning/verifier.py` |
| Controlled exploration | Perturbation strategies | `soft_reasoning/perturbation.py` |
| Exploitation balance | Acquisition functions | `soft_reasoning/optimization.py` |
| First-token optimization | Embedding optimization | `soft_reasoning/optimization.py` |

### Performance Characteristics (from paper)

- **Input token consumption**: ~6.19% of baseline methods
- **Output token usage**: ~63.28% of baseline methods
- **Inference time**: ~14.3% of baseline methods
- **Accuracy improvement**: Superior correctness across tasks

## Usage Examples

### End-to-End Soft Reasoning Pipeline

```python
from ai_karen_engine.core.reasoning import (
    SoftReasoningEngine,
    EmbeddingPerturber,
    BayesianOptimizer,
    ReasoningVerifier,
    PerturbationStrategy,
)

# Initialize components
engine = SoftReasoningEngine()
perturber = EmbeddingPerturber(strategy=PerturbationStrategy.ADAPTIVE)
optimizer = BayesianOptimizer()
verifier = ReasoningVerifier()

# Query with optimization
query = "What are the key factors affecting system performance?"

# Get initial embedding
initial_embedding = engine.embeddings.embed(query)

# Create verifier-guided score function
score_fn = verifier.create_score_function(query)

# Optimize embedding with Bayesian optimization
result = optimizer.optimize(
    initial_embedding,
    score_fn,
    perturb_fn=lambda e: perturber.perturb(e, confidence=0.5)
)

# Use optimized embedding for retrieval
results = engine.query(query, top_k=5)

# Synthesize response
synthesis = f"Based on {len(results)} relevant memories: ..."

# Verify quality
verification = verifier.verify(query, synthesis, context=[r['payload']['text'] for r in results])

print(f"Optimized in {result.num_iterations} iterations")
print(f"Best score: {result.best_score:.3f}")
print(f"Verification: {verification.overall_score:.2f} ({verification.feedback})")
```

### Integration with Existing Code

The reorganization maintains **full backward compatibility**. Existing code continues to work:

```python
# Old imports still work
from ai_karen_engine.core.reasoning import (
    SoftReasoningEngine,
    ReasoningGraph,
    CausalReasoningEngine,
    KariICEWrapper
)

# New paper-aligned modules are also available
from ai_karen_engine.core.reasoning import (
    EmbeddingPerturber,
    BayesianOptimizer,
    ReasoningVerifier
)
```

## Configuration

### Perturbation Configuration

```python
from ai_karen_engine.core.reasoning import PerturbationConfig, PerturbationStrategy

config = PerturbationConfig(
    strategy=PerturbationStrategy.HYBRID,
    base_variance=0.01,
    adaptive_factor=2.0,
    diversity_weight=0.3
)
```

### Optimization Configuration

```python
from ai_karen_engine.core.reasoning import OptimizationConfig, AcquisitionFunction

config = OptimizationConfig(
    acquisition_fn=AcquisitionFunction.UCB,
    exploration_weight=2.0,
    max_iterations=20,
    convergence_threshold=0.01
)
```

### Verifier Configuration

```python
from ai_karen_engine.core.reasoning import VerifierConfig, VerificationCriterion

config = VerifierConfig(
    criteria_weights={
        VerificationCriterion.CORRECTNESS: 0.4,
        VerificationCriterion.COHERENCE: 0.25,
        VerificationCriterion.COMPLETENESS: 0.15,
        VerificationCriterion.RELEVANCE: 0.15,
        VerificationCriterion.CONFIDENCE: 0.05,
    },
    min_acceptance_score=0.6,
    enable_adaptive_threshold=True
)
```

## Metrics & Telemetry

When Prometheus is available, the module exports metrics:

- `kari_sr_query_latency_ms`: SR query latency
- `kari_sr_ingest_total`: SR ingestion counts
- `kari_ice_latency_ms`: ICE processing latency
- `kari_ice_recall_strategy_total`: Recall strategy usage
- `kari_ice_writebacks_total`: Writeback operations
- `kari_ice_token_usage_total`: Approximate token usage

## Testing

```bash
# Run tests for reasoning module
pytest tests/core/reasoning/

# Specific component tests
pytest tests/core/reasoning/test_perturbation.py
pytest tests/core/reasoning/test_optimization.py
pytest tests/core/reasoning/test_verifier.py
```

## References

1. **Soft Reasoning Paper**: [OpenReview](https://openreview.net/forum?id=4gWE7CMOlH)
   - "Soft Reasoning: Navigating Solution Spaces in Large Language Models through Controlled Embedding Exploration"

2. **Bayesian Optimization**: Shahriari et al., "Taking the Human Out of the Loop: A Review of Bayesian Optimization"

3. **Causal Inference**: Pearl, "Causality: Models, Reasoning, and Inference"

## License

Part of AI Karen Engine - see root LICENSE file.
