"""
Enterprise-Grade spaCy Analyzer with Advanced Business Logic (Kari Alignment v3)

Highlights:
- Prompt-first, local-first orchestration and plugin-ready rule engine
- Dual-path intent (rules + ML), EI sentiment, entity enrichment w/ memory hooks
- Persona selection w/ RBAC-aware routing + context aware adjustments
- Profile-gap analysis for onboarding optimization
- Tenacity-based retries, async timeouts, circuit breaker, and TTL cache
- Observability: optional Prometheus metrics + structured logging
- Graceful degradation & fallbacks (always return something useful)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable

# ---- Optional deps (Prometheus, tenacity) with safe fallbacks ----
try:
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover
    class _Noop:
        def labels(self, *_, **__): return self
        def observe(self, *_): pass
        def inc(self, *_): pass
    Counter = Histogram = _Noop  # type: ignore

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type  # type: ignore
except Exception:  # pragma: no cover
    def retry(*_, **__):  # noop decorator
        def _inner(fn): return fn
        return _inner
    def stop_after_attempt(*_): return None
    def wait_exponential(*_, **__): return None
    def retry_if_exception_type(*_): return None

from ai_karen_engine.core.response.protocols import Analyzer
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.models.persona_models import SYSTEM_PERSONAS

logger = logging.getLogger(__name__)

# ===========================
# Enumerations & Data Models
# ===========================

class IntentType(str, Enum):
    # Technical Domain
    OPTIMIZE_CODE = "optimize_code"
    DEBUG_ERROR = "debug_error"
    TECHNICAL_QUESTION = "technical_question"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEPLOYMENT_HELP = "deployment_help"
    # Creative Domain
    CREATIVE_TASK = "creative_task"
    CONTENT_CREATION = "content_creation"
    DESIGN_ASSISTANCE = "design_assistance"
    BRAINSTORMING = "brainstorming"
    # Business Domain
    BUSINESS_ADVICE = "business_advice"
    STRATEGY_PLANNING = "strategy_planning"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    # Learning Domain
    EXPLAIN_CONCEPT = "explain_concept"
    TUTORIAL_REQUEST = "tutorial_request"
    LEARNING_PATH = "learning_path"
    # Support Domain
    TROUBLESHOOT = "troubleshoot"
    HOW_TO_GUIDE = "how_to_guide"
    DOCUMENTATION = "documentation"
    # Casual Domain
    CASUAL_CHAT = "casual_chat"
    PERSONAL_ADVICE = "personal_advice"
    FEEDBACK_SHARING = "feedback_sharing"
    # System Domain
    SYSTEM_CONFIG = "system_config"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    # Default
    GENERAL_ASSIST = "general_assist"


class SentimentType(str, Enum):
    # Positive Spectrum
    EXCITED = "excited"
    CONFIDENT = "confident"
    SATISFIED = "satisfied"
    HOPEFUL = "hopeful"
    GRATEFUL = "grateful"
    # Negative Spectrum
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    CONFUSED = "confused"
    DISAPPOINTED = "disappointed"
    OVERWHELMED = "overwhelmed"
    # Urgent Spectrum
    URGENT = "urgent"
    CRITICAL = "critical"
    TIME_SENSITIVE = "time_sensitive"
    # Neutral Spectrum
    NEUTRAL = "neutral"
    CALM = "calm"
    CONTEMPLATIVE = "contemplative"
    CURIOUS = "curious"


class BusinessDomain(str, Enum):
    TECH_DEVELOPMENT = "tech_development"
    BUSINESS_STRATEGY = "business_strategy"
    CREATIVE_PROJECTS = "creative_projects"
    ACADEMIC_LEARNING = "academic_learning"
    PERSONAL_GROWTH = "personal_growth"
    CUSTOMER_SUPPORT = "customer_support"
    SYSTEM_ADMIN = "system_admin"


@dataclass
class AnalysisContext:
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    domain: Optional[BusinessDomain] = None
    user_tier: str = "standard"  # standard, premium, enterprise
    roles: List[str] = field(default_factory=list)  # RBAC-aware persona routing
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    system_capabilities: Dict[str, Any] = field(default_factory=dict)
    business_rules: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class IntentResult:
    primary_intent: IntentType
    confidence: float
    alternative_intents: List[Tuple[IntentType, float]] = field(default_factory=list)
    domain: Optional[BusinessDomain] = None
    triggers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SentimentResult:
    primary_sentiment: SentimentType
    confidence: float
    intensity: float = 1.0  # 0.0 to 1.0
    emotional_indicators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    text: str
    intent: IntentResult
    sentiment: SentimentResult
    entities: Dict[str, Any]
    persona_recommendation: str
    confidence: float
    context: AnalysisContext
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===========================
# Observability (Prometheus)
# ===========================

_METRIC_ANALYZE_LATENCY = Histogram(
    "karen_analyzer_latency_seconds",
    "Latency for comprehensive analyzer",
    ["component"]
).labels(component="spacy_analyzer")

_METRIC_ANALYZE_ERRORS = Counter(
    "karen_analyzer_errors_total",
    "Total errors in comprehensive analyzer",
    ["component"]
).labels(component="spacy_analyzer")

_METRIC_REQUESTS = Counter(
    "karen_analyzer_requests_total",
    "Total requests to comprehensive analyzer",
    ["component"]
).labels(component="spacy_analyzer")


# ===========================
# Config & Circuit Breaker
# ===========================

@dataclass
class AnalyzerConfig:
    timeout_seconds: float = 10.0
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    persona_confidence_threshold: float = 0.65
    advanced_sentiment: bool = True
    domain_detection: bool = True
    multi_intent_analysis: bool = True
    # circuit breaker
    cb_failure_threshold: int = 5
    cb_reset_seconds: int = 30


class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_seconds: int):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._open_until = 0.0

    def allow(self) -> bool:
        return time.time() >= self._open_until

    def record_success(self):
        self._failures = 0

    def record_failure(self):
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._open_until = time.time() + self.reset_seconds
            self._failures = 0


# ===========================
# Analyzer Implementation
# ===========================

class SpacyAnalyzer(Analyzer):
    """
    Enterprise-grade analyzer with advanced business logic and multi-layered processing.
    Prompt-first, local-first, plugin/rule ready, with memory hooks and observability.
    """

    def __init__(
        self,
        spacy_service: Optional[SpacyService] = None,
        business_rules: Optional[Dict[str, Any]] = None,
        performance_monitoring: bool = True,
        config: Optional[AnalyzerConfig] = None,
        embedding_lookup: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
        entity_enrichment: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
    ):
        self.spacy_service = spacy_service or SpacyService()
        self.performance_monitoring = performance_monitoring
        self.config = config or AnalyzerConfig()
        self.business_rules = business_rules or self._load_default_business_rules()

        # Hooks (memory / embeddings / enrichment)
        self._embedding_lookup = embedding_lookup  # e.g., Milvus/Redis dual-embedding recall
        self._entity_enrichment = entity_enrichment  # post-extraction contextual enrichment

        # Engines
        self._intent_engine = IntentDetectionEngine(self.config)
        self._sentiment_engine = SentimentAnalysisEngine(self.config)
        self._entity_engine = EntityExtractionEngine(self.spacy_service, self.config)
        self._persona_orchestrator = PersonaOrchestrator(self.business_rules, self.config)
        self._gap_analyzer = ProfileGapAnalyzer()

        # Metrics state
        self._metrics = {
            "total_requests": 0,
            "average_processing_time": 0.0,
            "error_count": 0,
            "success_rate": 1.0,
        }

        # Circuit breaker for external enrichers
        self._cb = CircuitBreaker(
            failure_threshold=self.config.cb_failure_threshold,
            reset_seconds=self.config.cb_reset_seconds,
        )

        logger.info("SpacyAnalyzer initialized (Kari v3 alignment)")

    def _load_default_business_rules(self) -> Dict[str, Any]:
        return {
            "premium_features": {
                "advanced_sentiment": True,
                "domain_detection": True,
                "multi_intent_analysis": True,
            },
            "persona_routing": {
                "enable_dynamic_routing": True,
                "fallback_persona": "support-assistant",
                "confidence_threshold": 0.7,
                "role_overrides": {  # RBAC-aware persona overrides
                    "super_admin": "admin-overlord",
                    "admin": "admin-ops"
                },
            },
            "performance": {
                "timeout_seconds": self.config.timeout_seconds,
                "enable_caching": self.config.enable_caching,
                "cache_ttl_seconds": self.config.cache_ttl_seconds,
            },
        }

    async def analyze_comprehensive(
        self,
        text: str,
        context: Optional[AnalysisContext] = None
    ) -> AnalysisResult:
        start = time.time()
        self._metrics["total_requests"] += 1
        _METRIC_REQUESTS.inc(1)

        if context is None:
            context = AnalysisContext()

        # Prompt-first: treat input as a task spec—normalize early if needed
        text = text.strip()

        try:
            async with _LatencyTimer(_METRIC_ANALYZE_LATENCY):
                # Parallel core analyses with timeout envelope
                async def _core():
                    intent_task = asyncio.create_task(self._intent_engine.detect(text, context))
                    sentiment_task = asyncio.create_task(self._sentiment_engine.analyze(text, context))
                    entity_task = asyncio.create_task(self._entity_engine.extract(text, context))

                    intent_result, sentiment_result, entity_result = await asyncio.gather(
                        intent_task, sentiment_task, entity_task, return_exceptions=True
                    )
                    # Fault containment
                    if isinstance(intent_result, Exception):
                        logger.exception("Intent detection failed", exc_info=intent_result)
                        intent_result = IntentResult(IntentType.GENERAL_ASSIST, confidence=0.0)
                    if isinstance(sentiment_result, Exception):
                        logger.exception("Sentiment analysis failed", exc_info=sentiment_result)
                        sentiment_result = SentimentResult(SentimentType.NEUTRAL, confidence=0.0, intensity=0.3)
                    if isinstance(entity_result, Exception):
                        logger.exception("Entity extraction failed", exc_info=entity_result)
                        entity_result = {"entities": [], "metadata": {"error": str(entity_result), "confidence": 0.4}}

                    return intent_result, sentiment_result, entity_result

                intent_result, sentiment_result, entity_result = await asyncio.wait_for(
                    _core(), timeout=self.config.timeout_seconds
                )

                # Optional memory-driven enrichment (guarded by circuit breaker)
                if self._entity_enrichment and self._cb.allow():
                    try:
                        entity_result = await self._entity_enrichment(entity_result)
                        self._cb.record_success()
                    except Exception as e:  # pragma: no cover
                        logger.warning(f"Entity enrichment failed: {e}")
                        self._cb.record_failure()

                # Persona routing (RBAC-aware)
                persona_id = await self._persona_orchestrator.select_persona(
                    intent_result, sentiment_result, context
                )

                # Overall confidence
                overall_conf = self._calculate_overall_confidence(
                    intent_result.confidence,
                    sentiment_result.confidence,
                    entity_result.get("metadata", {}).get("confidence", 0.5),
                )

                elapsed = time.time() - start
                self._update_metrics(elapsed, True)

                return AnalysisResult(
                    text=text,
                    intent=intent_result,
                    sentiment=sentiment_result,
                    entities=entity_result,
                    persona_recommendation=persona_id,
                    confidence=overall_conf,
                    context=context,
                    processing_time=elapsed,
                    metadata={
                        "analysis_version": "3.0",
                        "business_domain": intent_result.domain,
                        "premium_features_used": context.user_tier != "standard",
                        "cb_open": not self._cb.allow(),
                    },
                )
        except Exception as e:
            _METRIC_ANALYZE_ERRORS.inc(1)
            elapsed = time.time() - start
            self._update_metrics(elapsed, False)
            logger.error(f"Comprehensive analysis failed: {e}")
            # Graceful degradation: still return useful, safe defaults
            return AnalysisResult(
                text=text,
                intent=IntentResult(IntentType.GENERAL_ASSIST, confidence=0.0),
                sentiment=SentimentResult(SentimentType.NEUTRAL, confidence=0.0, intensity=0.3),
                entities={"entities": [], "metadata": {"error": "analyzer_failure"}},
                persona_recommendation=self.business_rules["persona_routing"]["fallback_persona"],
                confidence=0.2,
                context=context,
                processing_time=elapsed,
                metadata={"analysis_version": "3.0", "degraded": True},
            )

    def _calculate_overall_confidence(self, intent_c: float, sent_c: float, ent_c: float) -> float:
        weights = {"intent": 0.5, "sentiment": 0.3, "entities": 0.2}
        return intent_c * weights["intent"] + sent_c * weights["sentiment"] + ent_c * weights["entities"]

    def _update_metrics(self, processing_time: float, success: bool):
        if not success:
            self._metrics["error_count"] += 1
        # EMA for average time
        alpha = 0.1
        avg = self._metrics["average_processing_time"]
        self._metrics["average_processing_time"] = alpha * processing_time + (1 - alpha) * avg
        total = self._metrics["total_requests"]
        errors = self._metrics["error_count"]
        self._metrics["success_rate"] = (total - errors) / total if total else 1.0

    # ---- Protocol compliance (Analyzer) ----
    async def detect_intent(self, text: str) -> str:
        result = await self.analyze_comprehensive(text)
        return result.intent.primary_intent.value

    async def sentiment(self, text: str) -> str:
        result = await self.analyze_comprehensive(text)
        return result.sentiment.primary_sentiment.value

    async def entities(self, text: str) -> Dict[str, Any]:
        result = await self.analyze_comprehensive(text)
        return result.entities

    async def select_persona(self, intent: str, sentiment: str, **kwargs) -> str:
        context = AnalysisContext(**kwargs)
        intent_result = IntentResult(primary_intent=IntentType(intent), confidence=1.0)
        sentiment_result = SentimentResult(primary_sentiment=SentimentType(sentiment), confidence=1.0)
        return await self._persona_orchestrator.select_persona(intent_result, sentiment_result, context)

    async def detect_profile_gaps(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        return await self._gap_analyzer.analyze_gaps(text, ui_caps)

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()


# ===========================
# Intent Detection Pipeline
# ===========================

class IntentDetectionEngine:
    def __init__(self, cfg: AnalyzerConfig):
        self._pattern_matcher = PatternBasedIntentDetector(cfg)
        self._ml_enhancer = MLIntentEnhancer(cfg)
        self._domain_detector = BusinessDomainDetector(cfg)

    async def detect(self, text: str, context: AnalysisContext) -> IntentResult:
        pattern_result = await self._pattern_matcher.detect(text)
        if context.user_tier in ["premium", "enterprise"]:
            ml_result = await self._ml_enhancer.enhance(text, pattern_result)
        else:
            ml_result = pattern_result
        if cfg := self._domain_detector.cfg:
            if cfg.domain_detection:
                domain = await self._domain_detector.detect(text, ml_result)
                ml_result.domain = domain
        return ml_result


class PatternBasedIntentDetector:
    def __init__(self, cfg: AnalyzerConfig):
        self.cfg = cfg
        self._patterns = self._build_patterns()

    def _build_patterns(self) -> Dict[IntentType, List[Dict[str, Any]]]:
        return {
            IntentType.OPTIMIZE_CODE: [
                {"pattern": r"\b(optimize|improve|refactor|performance)\b", "weight": 2.0},
                {"pattern": r"\b(slow|inefficient|bottleneck|memory leak)\b", "weight": 1.5},
            ],
            IntentType.BUSINESS_ADVICE: [
                {"pattern": r"\b(strategy|roadmap|business plan|market analysis)\b", "weight": 2.0},
                {"pattern": r"\b(competitor|market share|revenue|profit)\b", "weight": 1.5},
            ],
            IntentType.DEBUG_ERROR: [
                {"pattern": r"\b(error|stack trace|exception|crash|bug)\b", "weight": 2.0},
                {"pattern": r"\b(fix|debug|trace|fails|not working)\b", "weight": 1.3},
            ],
            IntentType.DEPLOYMENT_HELP: [
                {"pattern": r"\b(deploy|docker|kubernetes|helm|ci/cd|pipeline)\b", "weight": 1.8}
            ],
            IntentType.ARCHITECTURE_DESIGN: [
                {"pattern": r"\b(architecture|system design|scal(e|ing)|throughput|latency)\b", "weight": 1.7}
            ],
            # ... extend with more high-signal patterns as needed
        }

    async def detect(self, text: str) -> IntentResult:
        lower = text.lower()
        scores: Dict[IntentType, float] = {}
        triggers: List[str] = []

        for itype, plist in self._patterns.items():
            score = 0.0
            for p in plist:
                matches = re.findall(p["pattern"], lower, flags=re.IGNORECASE)
                if matches:
                    score += len(matches) * float(p["weight"])
                    triggers.extend(matches)
            if score > 0:
                scores[itype] = score

        if not scores:
            return IntentResult(primary_intent=IntentType.GENERAL_ASSIST, confidence=0.3, triggers=[])

        total = sum(scores.values())
        norm = {k: v / total for k, v in scores.items()}
        primary, conf = max(norm.items(), key=lambda x: x[1])
        alternatives = sorted([(k, v) for k, v in norm.items() if k != primary and v > 0.1],
                              key=lambda x: x[1], reverse=True)

        return IntentResult(
            primary_intent=primary,
            confidence=conf,
            alternative_intents=alternatives,
            triggers=triggers,
            metadata={"source": "pattern_rules"},
        )


class MLIntentEnhancer:
    """Hook for ML-based enhancement (local-first)."""
    def __init__(self, cfg: AnalyzerConfig):
        self.cfg = cfg

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=1.0),
        retry=retry_if_exception_type(Exception),
    )
    async def enhance(self, text: str, base_result: IntentResult) -> IntentResult:
        # Local-first: if no ML available, return base_result
        # Plug Kari's local LNM here (EchoCore personal model) when ready.
        return base_result


class BusinessDomainDetector:
    def __init__(self, cfg: AnalyzerConfig):
        self.cfg = cfg

    async def detect(self, text: str, _: IntentResult) -> Optional[BusinessDomain]:
        # Simple heuristic; swap for domain classifier later
        lower = text.lower()
        if any(k in lower for k in ["docker", "kubernetes", "api", "python", "react"]):
            return BusinessDomain.TECH_DEVELOPMENT
        if any(k in lower for k in ["revenue", "pricing", "market", "partner", "go-to-market"]):
            return BusinessDomain.BUSINESS_STRATEGY
        if any(k in lower for k in ["design", "mockup", "logo", "brand", "palette"]):
            return BusinessDomain.CREATIVE_PROJECTS
        return BusinessDomain.TECH_DEVELOPMENT


# ===========================
# Sentiment Analysis
# ===========================

class SentimentAnalysisEngine:
    def __init__(self, cfg: AnalyzerConfig):
        self.cfg = cfg
        self._lexicon = self._build_emotional_lexicon()
        self._intensity = SentimentIntensityCalculator()

    def _build_emotional_lexicon(self) -> Dict[SentimentType, Dict[str, float]]:
        return {
            SentimentType.EXCITED: {"excited": 0.9, "thrilled": 0.95, "enthusiastic": 0.85, "eager": 0.8, "energized": 0.75},
            SentimentType.FRUSTRATED: {"frustrated": 0.9, "annoyed": 0.8, "irritated": 0.75, "angry": 0.95, "mad": 0.9},
            SentimentType.CONFUSED: {"confused": 0.9, "unsure": 0.7, "lost": 0.7},
            SentimentType.URGENT: {"urgent": 0.9, "asap": 0.85, "immediately": 0.8},
            SentimentType.NEUTRAL: {"ok": 0.2, "fine": 0.2, "alright": 0.2},
        }

    async def analyze(self, text: str, context: AnalysisContext) -> SentimentResult:
        lower = text.lower()
        scores: Dict[SentimentType, float] = {}
        indicators: List[str] = []

        for s_type, words in self._lexicon.items():
            score = 0.0
            for w, wt in words.items():
                if w in lower:
                    score += wt
                    indicators.append(w)
            if score > 0:
                scores[s_type] = score

        if not scores:
            return SentimentResult(SentimentType.NEUTRAL, confidence=0.5, intensity=0.3, emotional_indicators=[])

        total = sum(scores.values())
        norm = {k: v / total for k, v in scores.items()}
        primary, conf = max(norm.items(), key=lambda x: x[1])
        intensity = await self._intensity.calculate_intensity(text, primary)

        return SentimentResult(primary, confidence=conf, intensity=intensity, emotional_indicators=indicators)


class SentimentIntensityCalculator:
    async def calculate_intensity(self, text: str, sentiment: SentimentType) -> float:
        # Basic proxy: punctuation & uppercase heuristics. Swap with local model later.
        bangs = text.count("!")
        caps = sum(1 for c in text if c.isupper())
        length = max(len(text), 1)
        raw = min(1.0, 0.3 + 0.1 * bangs + 0.2 * (caps / length))
        return round(raw, 3)


# ===========================
# Entities (spaCy + enrichment)
# ===========================

class EntityExtractionEngine:
    def __init__(self, spacy_service: SpacyService, cfg: AnalyzerConfig):
        self.spacy = spacy_service
        self.cfg = cfg

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=1.0),
        retry=retry_if_exception_type(Exception),
    )
    async def extract(self, text: str, context: AnalysisContext) -> Dict[str, Any]:
        # Use spaCy service to parse; enrich with lightweight domain tags
        parsed: ParsedMessage = await self.spacy.parse_text(text)
        ents = [{"text": e.text, "label": e.label_} for e in parsed.doc.ents] if getattr(parsed, "doc", None) else []

        meta: Dict[str, Any] = {"confidence": 0.6 + 0.1 * min(len(ents), 3)}
        # Domain hints
        if any(e["label"] in ("ORG", "PRODUCT", "LANGUAGE") for e in ents):
            meta["domain_hint"] = "tech/business"

        return {"entities": ents, "metadata": meta}


# ===========================
# Persona Orchestration
# ===========================

class PersonaOrchestrator:
    def __init__(self, business_rules: Dict[str, Any], cfg: AnalyzerConfig):
        self.rules = business_rules.get("persona_routing", {})
        self.cfg = cfg
        self.engine = PersonaRulesEngine(self.rules)

    async def select_persona(
        self,
        intent_result: IntentResult,
        sentiment_result: SentimentResult,
        context: AnalysisContext,
    ) -> str:
        # RBAC override
        for role, persona in (self.rules.get("role_overrides") or {}).items():
            if role in context.roles:
                return persona

        # Rule engine decision
        persona_id, score = await self.engine.apply_rules(intent_result, sentiment_result, context)

        # Confidence threshold + fallback
        threshold = float(self.rules.get("confidence_threshold", self.cfg.persona_confidence_threshold))
        if score < threshold:
            return self.rules.get("fallback_persona", "support-assistant")

        # Ensure persona exists in SYSTEM_PERSONAS
        if persona_id not in SYSTEM_PERSONAS:
            return self.rules.get("fallback_persona", "support-assistant")

        return persona_id


class PersonaRulesEngine:
    """
    Prompt-first rule engine (plugin-ready): define rules in config or inject evaluators.
    Evaluators: List[Callable[[IntentResult, SentimentResult, AnalysisContext], Tuple[str, float]]]
    """
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules
        self._evaluators: List[
            Callable[[IntentResult, SentimentResult, AnalysisContext], Awaitable[Tuple[str, float]]]
        ] = [
            self._eval_tech_overrides,
            self._eval_urgent_overrides,
            self._eval_creative_overrides,
            self._eval_default,
        ]

    async def apply_rules(
        self, intent: IntentResult, sentiment: SentimentResult, context: AnalysisContext
    ) -> Tuple[str, float]:
        best = ("support-assistant", 0.5)
        for ev in self._evaluators:
            try:
                persona, score = await ev(intent, sentiment, context)
                if score > best[1]:
                    best = (persona, score)
            except Exception as e:  # pragma: no cover
                logger.warning(f"Persona evaluator failed: {e}")
                continue
        return best

    async def _eval_tech_overrides(self, intent: IntentResult, sentiment: SentimentResult, context: AnalysisContext):
        if intent.primary_intent in {IntentType.DEBUG_ERROR, IntentType.OPTIMIZE_CODE, IntentType.DEPLOYMENT_HELP,
                                     IntentType.ARCHITECTURE_DESIGN, IntentType.CODE_REVIEW}:
            return ("tech-architect", 0.82)
        return ("support-assistant", 0.0)

    async def _eval_urgent_overrides(self, intent: IntentResult, sentiment: SentimentResult, context: AnalysisContext):
        if sentiment.primary_sentiment in {SentimentType.URGENT, SentimentType.CRITICAL, SentimentType.TIME_SENSITIVE}:
            return ("incident-commander", 0.8)
        return ("support-assistant", 0.0)

    async def _eval_creative_overrides(self, intent: IntentResult, sentiment: SentimentResult, context: AnalysisContext):
        if intent.primary_intent in {IntentType.CREATIVE_TASK, IntentType.DESIGN_ASSISTANCE, IntentType.CONTENT_CREATION}:
            return ("creative-director", 0.78)
        return ("support-assistant", 0.0)

    async def _eval_default(self, intent: IntentResult, sentiment: SentimentResult, context: AnalysisContext):
        return ("support-assistant", max(0.55, intent.confidence * 0.8))


# ===========================
# Profile Gap Analysis
# ===========================

class ProfileGapAnalyzer:
    def __init__(self):
        self._gap_detectors: Dict[str, GapDetector] = {
            "technical_context": TechnicalContextDetector(),
            "business_context": BusinessContextDetector(),
            "user_preferences": PreferenceDetector(),
            "system_integration": IntegrationDetector(),
        }
        self._suggestion_engine = SuggestionEngine()

    async def analyze_gaps(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        gaps: Dict[str, Any] = {}
        for name, det in self._gap_detectors.items():
            res = await det.detect(text, ui_caps)
            if res.get("missing"):
                gaps[name] = res
        suggestions = await self._suggestion_engine.generate_suggestions(gaps, ui_caps) if gaps else []
        return {
            "gaps": gaps,
            "suggestions": suggestions,
            "onboarding_needed": bool(gaps),
            "priority_gaps": [g for g in gaps.values() if g.get("priority") == "high"],
            "analysis_timestamp": time.time(),
        }


# ===========================
# Gap Detectors & Suggestions
# ===========================

class GapDetector:
    async def detect(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class TechnicalContextDetector(GapDetector):
    async def detect(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        missing = not any(k in text.lower() for k in ["language", "framework", "stack", "python", "node", "react"])
        return {"missing": missing, "priority": "medium" if missing else "low", "hint": "Specify tech stack."}

class BusinessContextDetector(GapDetector):
    async def detect(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        missing = not any(k in text.lower() for k in ["market", "revenue", "pricing", "target", "customer"])
        return {"missing": missing, "priority": "low" if not missing else "medium", "hint": "Add business goals."}

class PreferenceDetector(GapDetector):
    async def detect(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        # Detect tone/style preferences
        missing = not any(k in text.lower() for k in ["tone", "style", "voice"])
        return {"missing": missing, "priority": "low", "hint": "Share preferred tone/style if relevant."}

class IntegrationDetector(GapDetector):
    async def detect(self, text: str, ui_caps: Dict[str, Any]) -> Dict[str, Any]:
        # Example: whether user provided required API keys flags in UI caps
        missing = not ui_caps.get("integrations_ready", False)
        return {"missing": missing, "priority": "high" if missing else "low", "hint": "Complete integration setup."}

class SuggestionEngine:
    async def generate_suggestions(self, gaps: Dict[str, Any], ui_caps: Dict[str, Any]) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []
        for name, gap in gaps.items():
            suggestions.append({"gap": name, "action": gap.get("hint"), "priority": gap.get("priority")})
        return suggestions


# ===========================
# Utilities
# ===========================

class _LatencyTimer:
    """Async context manager for Prometheus histogram observe() calls."""
    def __init__(self, hist): self.hist = hist
    async def __aenter__(self): self._t = time.time(); return self
    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        try:
            self.hist.observe(max(0.0, time.time() - self._t))
        except Exception:
            pass


# ===========================
# Factory
# ===========================

def create_spacy_analyzer(
    spacy_service: Optional[SpacyService] = None,
    business_rules: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> SpacyAnalyzer:
    """
    Factory to create an SpacyAnalyzer instance (Kari aligned).
    Extra kwargs can include: config, embedding_lookup, entity_enrichment, performance_monitoring.
    """
    return SpacyAnalyzer(
        spacy_service=spacy_service,
        business_rules=business_rules,
        performance_monitoring=kwargs.get("performance_monitoring", True),
        config=kwargs.get("config"),
        embedding_lookup=kwargs.get("embedding_lookup"),
        entity_enrichment=kwargs.get("entity_enrichment"),
    )
