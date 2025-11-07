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

## Human-Like Cognition

The reasoning module now includes advanced human-like cognitive capabilities inspired by cognitive psychology and the Self-Refine paper (arXiv:2303.17651).

### 8. Self-Refinement (`synthesis/self_refine.py`)

Implements iterative refinement with self-feedback, mimicking how humans revise their work:

**Key Features**:
- **Iterative improvement**: Generate → Feedback → Refine → Repeat
- **Self-critique**: Model evaluates its own output
- **Multi-criteria evaluation**: Assess correctness, coherence, completeness, relevance
- **Convergence detection**: Stop when quality threshold met or diminishing returns
- **No additional training**: Works with existing LLMs

```python
from ai_karen_engine.core.reasoning import create_self_refiner

refiner = create_self_refiner(max_iterations=5, min_quality_score=0.8)

# Refine an output iteratively
result = refiner.refine(
    query="Explain quantum entanglement",
    initial_output="Quantum entanglement is...",
    criteria=["accuracy", "completeness", "clarity"]
)

print(f"Refined in {result.total_iterations} iterations")
print(f"Quality improved from {result.initial_quality:.2f} to {result.final_quality:.2f}")
print(f"Final output: {result.final_output}")
```

**Refinement Process**:
1. Generate initial output (or use provided)
2. Self-critique: Identify issues and generate feedback
3. Apply refinement: Improve based on feedback
4. Verify quality: Check if improvements meet threshold
5. Repeat until convergence or max iterations

### 9. Metacognition (`synthesis/metacognition.py`)

Implements metacognitive monitoring for self-awareness of reasoning processes:

**Cognitive States**:
- **Confident**: High certainty in reasoning
- **Uncertain**: Low certainty, need more information
- **Confused**: Contradictory or unclear situation
- **Exploring**: Actively seeking information
- **Consolidating**: Integrating information
- **Stuck**: Unable to progress

**Reasoning Strategies**:
- Analytical (step-by-step logic)
- Intuitive (pattern-based)
- Exploratory (broad search)
- Focused (deep dive)
- Comparative (compare alternatives)
- Causal (causal chains)

```python
from ai_karen_engine.core.reasoning import MetacognitiveMonitor

monitor = MetacognitiveMonitor()

# Monitor reasoning process
state = monitor.monitor_reasoning_process(
    query="What causes inflation?",
    current_output="Inflation is caused by...",
    context=["Economic data from 2020-2024"]
)

print(f"Cognitive state: {state.cognitive_state}")
print(f"Confidence: {state.confidence:.2f}")
print(f"Certainty: {state.certainty:.2f}")
print(f"Knowledge gaps: {state.knowledge_gaps}")

# Select appropriate strategy
strategy = monitor.select_strategy(query, current_state=state)
print(f"Recommended strategy: {strategy.value}")

# Check if more information needed
should_seek, what = monitor.should_seek_more_information()
if should_seek:
    print(f"Should seek: {what}")

# Check if self-correction needed
should_correct, reason = monitor.should_self_correct(current_output, quality_score=0.65)
if should_correct:
    print(f"Should self-correct: {reason}")

# Get performance reflection
reflection = monitor.get_reflection()
print(f"Success rate: {reflection['success_rate']:.2%}")
print(f"Best strategy: {reflection['best_strategy']}")
```

**Capabilities**:
- Self-monitoring of confidence and certainty
- Knowledge gap identification
- Strategy selection based on task and state
- Performance tracking and adaptation
- Self-correction triggers

### 10. Cognitive Orchestrator (`synthesis/cognitive_orchestrator.py`)

High-level orchestrator that integrates all cognitive subsystems into a human-like reasoning flow:

**Cognitive Modes**:
- **Fast**: Quick, intuitive processing
- **Deliberate**: Slow, analytical processing
- **Adaptive**: Switch between fast and deliberate
- **Reflective**: Include self-reflection
- **Exploratory**: Broad information gathering

**Cognitive Flow**:
1. **Task Understanding**: Analyze query and select strategy
2. **Information Gathering**: Retrieve relevant context
3. **Initial Generation**: Generate first response
4. **Metacognitive Monitoring**: Assess cognitive state
5. **Self-Refinement**: Iteratively improve if needed
6. **Quality Verification**: Verify final output quality
7. **Learning**: Update performance metrics

```python
from ai_karen_engine.core.reasoning import (
    create_cognitive_orchestrator,
    CognitiveTask,
    CognitiveMode
)

# Create orchestrator (auto-initializes all subsystems)
orchestrator = create_cognitive_orchestrator(
    enable_self_refine=True,
    enable_metacognition=True,
    enable_soft_reasoning=True,
    max_refinement_iterations=3,
    quality_threshold=0.75
)

# Process a complex task
task = CognitiveTask(
    query="Analyze the long-term economic impacts of AI automation",
    task_type="analytical",
    requires_certainty=True,
    requires_explanation=True,
    priority=8
)

response = orchestrator.process(task, mode=CognitiveMode.REFLECTIVE)

print(f"Output: {response.output}")
print(f"Confidence: {response.confidence:.2%}")
print(f"Quality: {response.quality_score:.2f}")
print(f"Strategy: {response.strategy_used}")
print(f"Refinement iterations: {response.refinement_iterations}")
print(f"Reasoning trace: {response.reasoning_trace}")
print(f"Knowledge gaps: {response.knowledge_gaps}")

# Simplified interface
answer = orchestrator.process_simple(
    "What is the capital of France?",
    requires_certainty=True
)

# Get reflection on performance
reflection = orchestrator.reflect()
print(f"Recent performance: {reflection}")
```

**Integration Example - Full Human-Like Reasoning Pipeline**:

```python
from ai_karen_engine.core.reasoning import (
    create_cognitive_orchestrator,
    CognitiveTask,
    CognitiveMode,
)

# Initialize with all capabilities
orchestrator = create_cognitive_orchestrator(
    enable_self_refine=True,
    enable_metacognition=True,
    enable_soft_reasoning=True,
    enable_causal_reasoning=True,
    enable_learning=True,
)

# Process complex reasoning task
task = CognitiveTask(
    query="Why did the software deployment fail, and how can we prevent it?",
    context=[
        "Deployment at 2 AM on Friday",
        "Load balancer config changed",
        "Database migration included",
    ],
    requires_certainty=True,
    requires_explanation=True,
)

# Adaptive mode: automatically chooses fast or deliberate processing
response = orchestrator.process(task, mode=CognitiveMode.ADAPTIVE)

# The orchestrator:
# 1. Selected "causal" strategy (detected "why" question)
# 2. Gathered relevant information from soft reasoning engine
# 3. Generated initial causal analysis
# 4. Monitored confidence → low confidence detected
# 5. Triggered self-refinement (3 iterations)
# 6. Verified quality → passed threshold
# 7. Updated performance metrics for learning

print("=" * 60)
print("COGNITIVE RESPONSE")
print("=" * 60)
print(f"\nAnswer:\n{response.output}\n")
print(f"Confidence: {response.confidence:.2%}")
print(f"Certainty: {response.certainty:.2%}")
print(f"Quality Score: {response.quality_score:.2f}")
print(f"Processing Time: {response.processing_time:.2f}s")
print(f"\nMetacognitive State: {response.metacognitive_state}")
print(f"Strategy Used: {response.strategy_used}")
print(f"Refinement Iterations: {response.refinement_iterations}")
print(f"\nReasoning Trace:")
for step in response.reasoning_trace:
    print(f"  • {step}")

if response.knowledge_gaps:
    print(f"\nIdentified Knowledge Gaps:")
    for gap in response.knowledge_gaps:
        print(f"  - {gap}")
```

### Human-Like Cognition Research Alignment

| Human Cognitive Process | Implementation | Module |
|------------------------|----------------|---------|
| **Iterative Revision** | Self-Refine iterative loop | `synthesis/self_refine.py` |
| **Self-Awareness** | Metacognitive monitoring | `synthesis/metacognition.py` |
| **Strategy Selection** | Adaptive strategy choice | `synthesis/metacognition.py` |
| **Self-Critique** | Feedback generation | `synthesis/self_refine.py` |
| **Uncertainty Recognition** | Confidence/certainty assessment | `synthesis/metacognition.py` |
| **Learning from Experience** | Performance tracking & adaptation | `synthesis/metacognition.py` |
| **Executive Function** | Cognitive orchestration | `synthesis/cognitive_orchestrator.py` |
| **Dual Process (System 1/2)** | Fast vs Deliberate modes | `synthesis/cognitive_orchestrator.py` |

### Benefits of Human-Like Cognition

1. **Improved Quality**: Iterative refinement produces higher-quality outputs
2. **Adaptive Processing**: Chooses appropriate depth based on task complexity
3. **Self-Awareness**: Recognizes limitations and seeks additional information
4. **Efficient Resource Use**: Fast mode for simple tasks, deliberate for complex ones
5. **Continuous Learning**: Adapts strategies based on performance history
6. **Transparency**: Provides reasoning traces and identifies knowledge gaps
7. **Robustness**: Self-correction mechanisms catch and fix errors

## Testing

```bash
# Run tests for reasoning module
pytest tests/core/reasoning/

# Specific component tests
pytest tests/core/reasoning/test_perturbation.py
pytest tests/core/reasoning/test_optimization.py
pytest tests/core/reasoning/test_verifier.py
pytest tests/core/reasoning/test_self_refine.py
pytest tests/core/reasoning/test_metacognition.py
pytest tests/core/reasoning/test_cognitive_orchestrator.py
```

## References

1. **Soft Reasoning Paper**: [OpenReview](https://openreview.net/forum?id=4gWE7CMOlH)
   - "Soft Reasoning: Navigating Solution Spaces in Large Language Models through Controlled Embedding Exploration"

2. **Self-Refine Paper**: [arXiv:2303.17651](https://arxiv.org/abs/2303.17651)
   - Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback"
   - Implements iterative refinement mimicking human revision processes

3. **Bayesian Optimization**: Shahriari et al., "Taking the Human Out of the Loop: A Review of Bayesian Optimization"

4. **Causal Inference**: Pearl, "Causality: Models, Reasoning, and Inference"

5. **Metacognition Research**: Flavell, "Metacognition and Cognitive Monitoring: A New Area of Cognitive-Developmental Inquiry"

## License

Part of AI Karen Engine - see root LICENSE file.
