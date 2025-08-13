"""
Performance Benchmarking System - Task 8.4
Implements continuous performance monitoring with SLO tracking,
automated performance regression testing, and real-time dashboards.
"""

import asyncio
import logging
import time
import uuid
import json
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from enum import Enum
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class BenchmarkType(str, Enum):
    """Types of performance benchmarks"""
    VECTOR_QUERY = "vector_query"
    LLM_GENERATION = "llm_generation"
    E2E_PIPELINE = "e2e_pipeline"
    MEMORY_OPERATIONS = "memory_operations"
    CACHE_PERFORMANCE = "cache_performance"

class LoadProfile(str, Enum):
    """Load testing profiles"""
    LIGHT = "light"      # 1 RPS
    MODERATE = "moderate" # 5 RPS  
    HEAVY = "heavy"      # 20 RPS
    BURST = "burst"      # Variable load with spikes

@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarks"""
    benchmark_type: BenchmarkType
    load_profile: LoadProfile
    duration_seconds: int = 60
    target_rps: float = 1.0
    max_concurrent: int = 10
    warmup_seconds: int = 10
    
    # SLO targets
    target_p95_latency_ms: float = 1000.0
    target_p99_latency_ms: float = 2000.0
    target_error_rate: float = 0.01  # 1%
    target_throughput_rps: float = 1.0

@dataclass
class BenchmarkResult:
    """Results from a performance benchmark"""
    benchmark_id: str
    benchmark_type: BenchmarkType
    load_profile: LoadProfile
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Request statistics
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    
    # Latency statistics
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    
    # Throughput statistics
    actual_rps: float
    peak_rps: float
    
    # SLO compliance
    slo_compliance: Dict[str, bool]
    
    # Additional metrics
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceBenchmarker:
    """Performance benchmarking and monitoring system"""
    
    def __init__(self, max_workers: int = 20):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Benchmark history
        self.benchmark_history: List[BenchmarkResult] = []
        self.active_benchmarks: Dict[str, Dict[str, Any]] = {}
        
        # Performance baselines
        self.baselines: Dict[BenchmarkType, Dict[str, float]] = {}
        
        # Regression detection
        self.regression_threshold = 0.2  # 20% degradation threshold
        self.regression_alerts: List[Dict[str, Any]] = []
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    async def run_benchmark(
        self,
        config: BenchmarkConfig,
        test_function: Callable,
        test_data: List[Any],
        correlation_id: Optional[str] = None
    ) -> BenchmarkResult:
        """Run a performance benchmark"""
        benchmark_id = correlation_id or str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(
            f"Starting benchmark {config.benchmark_type.value} "
            f"with {config.load_profile.value} load profile",
            extra={"benchmark_id": benchmark_id}
        )
        
        # Initialize benchmark tracking
        with self.lock:
            self.active_benchmarks[benchmark_id] = {
                "config": config,
                "start_time": start_time,
                "requests_completed": 0,
                "requests_failed": 0,
                "latencies": []
            }
        
        try:
            # Warmup phase
            if config.warmup_seconds > 0:
                await self._warmup_phase(config, test_function, test_data, benchmark_id)
            
            # Main benchmark phase
            results = await self._execute_benchmark(
                config, test_function, test_data, benchmark_id
            )
            
            # Calculate final results
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            benchmark_result = self._calculate_benchmark_result(
                benchmark_id, config, start_time, end_time, duration, results
            )
            
            # Store results
            with self.lock:
                self.benchmark_history.append(benchmark_result)
                self.active_benchmarks.pop(benchmark_id, None)
            
            # Check for regressions
            await self._check_for_regressions(benchmark_result)
            
            logger.info(
                f"Benchmark completed: {benchmark_result.successful_requests}/{benchmark_result.total_requests} "
                f"requests, p95: {benchmark_result.p95_latency_ms:.2f}ms, "
                f"RPS: {benchmark_result.actual_rps:.2f}",
                extra={"benchmark_id": benchmark_id}
            )
            
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}", extra={"benchmark_id": benchmark_id})
            
            # Clean up
            with self.lock:
                self.active_benchmarks.pop(benchmark_id, None)
            
            raise
    
    async def _warmup_phase(
        self,
        config: BenchmarkConfig,
        test_function: Callable,
        test_data: List[Any],
        benchmark_id: str
    ):
        """Execute warmup phase"""
        logger.info(f"Starting warmup phase ({config.warmup_seconds}s)", 
                   extra={"benchmark_id": benchmark_id})
        
        warmup_requests = min(config.warmup_seconds * 2, len(test_data))  # 2 RPS during warmup
        
        tasks = []
        for i in range(warmup_requests):
            if i < len(test_data):
                task = asyncio.create_task(
                    self._execute_single_request(test_function, test_data[i], benchmark_id, warmup=True)
                )
                tasks.append(task)
                
                # Small delay between warmup requests
                await asyncio.sleep(0.5)
        
        # Wait for warmup to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Warmup phase completed", extra={"benchmark_id": benchmark_id})
    
    async def _execute_benchmark(
        self,
        config: BenchmarkConfig,
        test_function: Callable,
        test_data: List[Any],
        benchmark_id: str
    ) -> Dict[str, Any]:
        """Execute the main benchmark"""
        logger.info("Starting main benchmark phase", extra={"benchmark_id": benchmark_id})
        
        if config.load_profile == LoadProfile.LIGHT:
            return await self._execute_constant_load(config, test_function, test_data, benchmark_id, 1.0)
        elif config.load_profile == LoadProfile.MODERATE:
            return await self._execute_constant_load(config, test_function, test_data, benchmark_id, 5.0)
        elif config.load_profile == LoadProfile.HEAVY:
            return await self._execute_constant_load(config, test_function, test_data, benchmark_id, 20.0)
        elif config.load_profile == LoadProfile.BURST:
            return await self._execute_burst_load(config, test_function, test_data, benchmark_id)
        else:
            return await self._execute_constant_load(config, test_function, test_data, benchmark_id, config.target_rps)
    
    async def _execute_constant_load(
        self,
        config: BenchmarkConfig,
        test_function: Callable,
        test_data: List[Any],
        benchmark_id: str,
        target_rps: float
    ) -> Dict[str, Any]:
        """Execute benchmark with constant load"""
        interval = 1.0 / target_rps if target_rps > 0 else 1.0
        total_requests = int(config.duration_seconds * target_rps)
        
        # Limit to available test data
        total_requests = min(total_requests, len(test_data))
        
        tasks = []
        start_time = time.time()
        
        for i in range(total_requests):
            # Schedule request
            task = asyncio.create_task(
                self._execute_single_request(test_function, test_data[i % len(test_data)], benchmark_id)
            )
            tasks.append(task)
            
            # Control rate
            if i < total_requests - 1:  # Don't sleep after last request
                await asyncio.sleep(interval)
            
            # Check if we've exceeded duration
            if time.time() - start_time > config.duration_seconds:
                break
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "total_scheduled": len(tasks),
            "results": results
        }
    
    async def _execute_burst_load(
        self,
        config: BenchmarkConfig,
        test_function: Callable,
        test_data: List[Any],
        benchmark_id: str
    ) -> Dict[str, Any]:
        """Execute benchmark with burst load pattern"""
        # Burst pattern: 1 RPS for 20s, then 10 RPS for 20s, then 1 RPS for 20s
        phases = [
            (20, 1.0),   # 20 seconds at 1 RPS
            (20, 10.0),  # 20 seconds at 10 RPS  
            (20, 1.0)    # 20 seconds at 1 RPS
        ]
        
        all_tasks = []
        data_index = 0
        
        for phase_duration, phase_rps in phases:
            phase_tasks = []
            interval = 1.0 / phase_rps
            phase_requests = int(phase_duration * phase_rps)
            
            logger.info(f"Starting burst phase: {phase_rps} RPS for {phase_duration}s",
                       extra={"benchmark_id": benchmark_id})
            
            for i in range(phase_requests):
                if data_index >= len(test_data):
                    data_index = 0  # Wrap around
                
                task = asyncio.create_task(
                    self._execute_single_request(test_function, test_data[data_index], benchmark_id)
                )
                phase_tasks.append(task)
                data_index += 1
                
                if i < phase_requests - 1:
                    await asyncio.sleep(interval)
            
            all_tasks.extend(phase_tasks)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        return {
            "total_scheduled": len(all_tasks),
            "results": results
        }
    
    async def _execute_single_request(
        self,
        test_function: Callable,
        test_data: Any,
        benchmark_id: str,
        warmup: bool = False
    ) -> Dict[str, Any]:
        """Execute a single test request"""
        start_time = time.time()
        
        try:
            # Execute the test function
            if asyncio.iscoroutinefunction(test_function):
                result = await test_function(test_data)
            else:
                result = test_function(test_data)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics (skip during warmup)
            if not warmup:
                with self.lock:
                    if benchmark_id in self.active_benchmarks:
                        self.active_benchmarks[benchmark_id]["requests_completed"] += 1
                        self.active_benchmarks[benchmark_id]["latencies"].append(latency_ms)
            
            return {
                "success": True,
                "latency_ms": latency_ms,
                "result": result
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            # Record error (skip during warmup)
            if not warmup:
                with self.lock:
                    if benchmark_id in self.active_benchmarks:
                        self.active_benchmarks[benchmark_id]["requests_failed"] += 1
                        self.active_benchmarks[benchmark_id]["latencies"].append(latency_ms)
            
            return {
                "success": False,
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    def _calculate_benchmark_result(
        self,
        benchmark_id: str,
        config: BenchmarkConfig,
        start_time: datetime,
        end_time: datetime,
        duration: float,
        results: Dict[str, Any]
    ) -> BenchmarkResult:
        """Calculate final benchmark results"""
        with self.lock:
            benchmark_data = self.active_benchmarks.get(benchmark_id, {})
            latencies = benchmark_data.get("latencies", [])
            requests_completed = benchmark_data.get("requests_completed", 0)
            requests_failed = benchmark_data.get("requests_failed", 0)
        
        total_requests = requests_completed + requests_failed
        error_rate = requests_failed / max(total_requests, 1)
        actual_rps = requests_completed / max(duration, 0.001)
        
        # Calculate latency statistics
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            
            avg_latency = statistics.mean(latencies)
            p50_latency = sorted_latencies[int(n * 0.5)]
            p95_latency = sorted_latencies[int(n * 0.95)]
            p99_latency = sorted_latencies[int(n * 0.99)]
            max_latency = max(latencies)
            min_latency = min(latencies)
        else:
            avg_latency = p50_latency = p95_latency = p99_latency = 0.0
            max_latency = min_latency = 0.0
        
        # Check SLO compliance
        slo_compliance = {
            "p95_latency": p95_latency <= config.target_p95_latency_ms,
            "p99_latency": p99_latency <= config.target_p99_latency_ms,
            "error_rate": error_rate <= config.target_error_rate,
            "throughput": actual_rps >= config.target_throughput_rps
        }
        
        return BenchmarkResult(
            benchmark_id=benchmark_id,
            benchmark_type=config.benchmark_type,
            load_profile=config.load_profile,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=total_requests,
            successful_requests=requests_completed,
            failed_requests=requests_failed,
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            max_latency_ms=max_latency,
            min_latency_ms=min_latency,
            actual_rps=actual_rps,
            peak_rps=actual_rps,  # For constant load, peak = average
            slo_compliance=slo_compliance
        )
    
    async def _check_for_regressions(self, result: BenchmarkResult):
        """Check for performance regressions"""
        benchmark_type = result.benchmark_type
        
        # Get baseline for this benchmark type
        if benchmark_type not in self.baselines:
            # First run, establish baseline
            self.baselines[benchmark_type] = {
                "p95_latency_ms": result.p95_latency_ms,
                "throughput_rps": result.actual_rps,
                "error_rate": result.error_rate
            }
            logger.info(f"Established baseline for {benchmark_type.value}")
            return
        
        baseline = self.baselines[benchmark_type]
        
        # Check for regressions
        regressions = []
        
        # Latency regression (higher is worse)
        if result.p95_latency_ms > baseline["p95_latency_ms"] * (1 + self.regression_threshold):
            regressions.append({
                "metric": "p95_latency_ms",
                "baseline": baseline["p95_latency_ms"],
                "current": result.p95_latency_ms,
                "degradation_pct": ((result.p95_latency_ms / baseline["p95_latency_ms"]) - 1) * 100
            })
        
        # Throughput regression (lower is worse)
        if result.actual_rps < baseline["throughput_rps"] * (1 - self.regression_threshold):
            regressions.append({
                "metric": "throughput_rps",
                "baseline": baseline["throughput_rps"],
                "current": result.actual_rps,
                "degradation_pct": ((baseline["throughput_rps"] / result.actual_rps) - 1) * 100
            })
        
        # Error rate regression (higher is worse)
        if result.error_rate > baseline["error_rate"] * (1 + self.regression_threshold):
            regressions.append({
                "metric": "error_rate",
                "baseline": baseline["error_rate"],
                "current": result.error_rate,
                "degradation_pct": ((result.error_rate / max(baseline["error_rate"], 0.001)) - 1) * 100
            })
        
        if regressions:
            alert = {
                "benchmark_id": result.benchmark_id,
                "benchmark_type": benchmark_type.value,
                "timestamp": datetime.utcnow(),
                "regressions": regressions
            }
            
            with self.lock:
                self.regression_alerts.append(alert)
            
            logger.warning(
                f"Performance regression detected in {benchmark_type.value}: "
                f"{len(regressions)} metrics degraded",
                extra={"benchmark_id": result.benchmark_id}
            )
        else:
            # Update baseline with better performance
            if result.p95_latency_ms < baseline["p95_latency_ms"]:
                baseline["p95_latency_ms"] = result.p95_latency_ms
            if result.actual_rps > baseline["throughput_rps"]:
                baseline["throughput_rps"] = result.actual_rps
            if result.error_rate < baseline["error_rate"]:
                baseline["error_rate"] = result.error_rate
    
    def get_benchmark_history(
        self,
        benchmark_type: Optional[BenchmarkType] = None,
        limit: int = 100
    ) -> List[BenchmarkResult]:
        """Get benchmark history"""
        with self.lock:
            history = self.benchmark_history.copy()
        
        if benchmark_type:
            history = [r for r in history if r.benchmark_type == benchmark_type]
        
        # Sort by start time (most recent first)
        history.sort(key=lambda r: r.start_time, reverse=True)
        
        return history[:limit]
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get performance dashboard data"""
        with self.lock:
            recent_results = self.benchmark_history[-50:] if self.benchmark_history else []
            active_benchmarks = len(self.active_benchmarks)
            regression_alerts = self.regression_alerts[-10:]  # Last 10 alerts
        
        # Calculate summary statistics
        dashboard = {
            "summary": {
                "total_benchmarks": len(self.benchmark_history),
                "active_benchmarks": active_benchmarks,
                "recent_regressions": len(regression_alerts),
                "last_updated": datetime.utcnow().isoformat()
            },
            "recent_results": [],
            "slo_compliance": {},
            "regression_alerts": regression_alerts,
            "baselines": self.baselines.copy()
        }
        
        # Process recent results
        for result in recent_results:
            dashboard["recent_results"].append({
                "benchmark_id": result.benchmark_id,
                "benchmark_type": result.benchmark_type.value,
                "load_profile": result.load_profile.value,
                "start_time": result.start_time.isoformat(),
                "duration_seconds": result.duration_seconds,
                "p95_latency_ms": result.p95_latency_ms,
                "actual_rps": result.actual_rps,
                "error_rate": result.error_rate,
                "slo_compliance": result.slo_compliance
            })
        
        # Calculate SLO compliance by benchmark type
        for benchmark_type in BenchmarkType:
            type_results = [r for r in recent_results if r.benchmark_type == benchmark_type]
            if type_results:
                compliant_results = [r for r in type_results if all(r.slo_compliance.values())]
                compliance_rate = len(compliant_results) / len(type_results)
                
                dashboard["slo_compliance"][benchmark_type.value] = {
                    "compliance_rate": compliance_rate,
                    "total_runs": len(type_results),
                    "compliant_runs": len(compliant_results)
                }
        
        return dashboard
    
    def export_results(self, format: str = "json") -> str:
        """Export benchmark results"""
        with self.lock:
            data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_benchmarks": len(self.benchmark_history),
                "baselines": self.baselines,
                "regression_alerts": self.regression_alerts,
                "benchmark_results": []
            }
            
            for result in self.benchmark_history:
                data["benchmark_results"].append({
                    "benchmark_id": result.benchmark_id,
                    "benchmark_type": result.benchmark_type.value,
                    "load_profile": result.load_profile.value,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "duration_seconds": result.duration_seconds,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "error_rate": result.error_rate,
                    "avg_latency_ms": result.avg_latency_ms,
                    "p50_latency_ms": result.p50_latency_ms,
                    "p95_latency_ms": result.p95_latency_ms,
                    "p99_latency_ms": result.p99_latency_ms,
                    "max_latency_ms": result.max_latency_ms,
                    "min_latency_ms": result.min_latency_ms,
                    "actual_rps": result.actual_rps,
                    "peak_rps": result.peak_rps,
                    "slo_compliance": result.slo_compliance,
                    "metadata": result.metadata
                })
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Global instance
_performance_benchmarker: Optional[PerformanceBenchmarker] = None

def get_performance_benchmarker() -> PerformanceBenchmarker:
    """Get the global performance benchmarker instance"""
    global _performance_benchmarker
    
    if _performance_benchmarker is None:
        _performance_benchmarker = PerformanceBenchmarker()
    
    return _performance_benchmarker