"""
Regression testing to prevent performance degradation in future updates.
Tests performance baselines and detects regressions across system updates.
"""

import pytest
import asyncio
import time
import json
import os
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass, asdict

from src.ai_karen_engine.audit.performance_auditor import PerformanceAuditor
from src.ai_karen_engine.core.service_lifecycle_manager import ServiceLifecycleManager
from src.ai_karen_engine.core.lazy_loading_controller import LazyLoadingController
from src.ai_karen_engine.core.async_task_orchestrator import AsyncTaskOrchestrator
from src.ai_karen_engine.core.resource_monitor import ResourceMonitor
from src.ai_karen_engine.core.performance_metrics import PerformanceMetric, SystemMetrics, ServiceMetrics


@dataclass
class PerformanceBaseline:
    """Performance baseline data for regression testing."""
    test_name: str
    timestamp: str
    startup_time: float
    memory_usage: int
    cpu_usage: float
    service_count: int
    response_time: float
    throughput: float
    version: str = "1.0.0"


@dataclass
class RegressionTestResult:
    """Regression test result."""
    test_name: str
    baseline: PerformanceBaseline
    current: PerformanceBaseline
    regression_detected: bool
    performance_change: Dict[str, float]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: List[str]


class PerformanceRegressionSuite:
    """Comprehensive performance regression test suite."""
    
    def __init__(self):
        self.baseline_file = "tests/performance_baselines.json"
        self.auditor = PerformanceAuditor()
        self.lifecycle_manager = ServiceLifecycleManager()
        self.lazy_controller = LazyLoadingController()
        self.task_orchestrator = AsyncTaskOrchestrator()
        self.resource_monitor = ResourceMonitor()
        
        # Performance thresholds for regression detection
        self.thresholds = {
            "startup_time": 0.20,      # 20% increase is a regression
            "memory_usage": 0.15,      # 15% increase is a regression
            "cpu_usage": 0.25,         # 25% increase is a regression
            "response_time": 0.30,     # 30% increase is a regression
            "throughput": -0.10        # 10% decrease is a regression
        }
    
    def load_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Load performance baselines from file."""
        if not os.path.exists(self.baseline_file):
            return {}
        
        try:
            with open(self.baseline_file, 'r') as f:
                data = json.load(f)
                return {
                    name: PerformanceBaseline(**baseline) 
                    for name, baseline in data.items()
                }
        except Exception as e:
            print(f"Warning: Could not load baselines: {e}")
            return {}
    
    def save_baselines(self, baselines: Dict[str, PerformanceBaseline]):
        """Save performance baselines to file."""
        try:
            os.makedirs(os.path.dirname(self.baseline_file), exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(
                    {name: asdict(baseline) for name, baseline in baselines.items()},
                    f, indent=2
                )
        except Exception as e:
            print(f"Warning: Could not save baselines: {e}")
    
    async def establish_startup_baseline(self) -> PerformanceBaseline:
        """Establish startup performance baseline."""
        # Measure startup performance
        start_time = time.time()
        
        # Simulate system startup
        await self.lifecycle_manager.start_essential_services()
        
        startup_time = time.time() - start_time
        memory_usage = psutil.Process().memory_info().rss
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Count running services
        running_services = await self.lifecycle_manager.get_running_services()
        service_count = len(running_services)
        
        return PerformanceBaseline(
            test_name="startup_performance",
            timestamp=datetime.now().isoformat(),
            startup_time=startup_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            service_count=service_count,
            response_time=0.0,
            throughput=0.0
        )
    
    async def establish_runtime_baseline(self) -> PerformanceBaseline:
        """Establish runtime performance baseline."""
        # Measure runtime performance
        start_time = time.time()
        
        # Simulate typical runtime operations
        tasks = []
        for i in range(10):
            task = self.task_orchestrator.offload_cpu_intensive_task(
                lambda: sum(j * j for j in range(1000))
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        response_time = total_time / len(tasks)
        throughput = len(tasks) / total_time
        
        memory_usage = psutil.Process().memory_info().rss
        cpu_usage = psutil.cpu_percent()
        
        return PerformanceBaseline(
            test_name="runtime_performance",
            timestamp=datetime.now().isoformat(),
            startup_time=0.0,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            service_count=0,
            response_time=response_time,
            throughput=throughput
        )
    
    async def establish_lazy_loading_baseline(self) -> PerformanceBaseline:
        """Establish lazy loading performance baseline."""
        # Measure lazy loading performance
        services_to_load = ["service1", "service2", "service3", "service4", "service5"]
        
        start_time = time.time()
        
        for service in services_to_load:
            await self.lazy_controller.get_service(service)
        
        total_time = time.time() - start_time
        response_time = total_time / len(services_to_load)
        
        memory_usage = psutil.Process().memory_info().rss
        cpu_usage = psutil.cpu_percent()
        
        return PerformanceBaseline(
            test_name="lazy_loading_performance",
            timestamp=datetime.now().isoformat(),
            startup_time=0.0,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            service_count=len(services_to_load),
            response_time=response_time,
            throughput=len(services_to_load) / total_time
        )
    
    def detect_regression(self, baseline: PerformanceBaseline, current: PerformanceBaseline) -> RegressionTestResult:
        """Detect performance regression between baseline and current measurements."""
        performance_change = {}
        regression_detected = False
        recommendations = []
        
        # Calculate performance changes
        if baseline.startup_time > 0:
            startup_change = (current.startup_time - baseline.startup_time) / baseline.startup_time
            performance_change["startup_time"] = startup_change
            if startup_change > self.thresholds["startup_time"]:
                regression_detected = True
                recommendations.append(f"Startup time increased by {startup_change*100:.1f}%")
        
        if baseline.memory_usage > 0:
            memory_change = (current.memory_usage - baseline.memory_usage) / baseline.memory_usage
            performance_change["memory_usage"] = memory_change
            if memory_change > self.thresholds["memory_usage"]:
                regression_detected = True
                recommendations.append(f"Memory usage increased by {memory_change*100:.1f}%")
        
        if baseline.cpu_usage > 0:
            cpu_change = (current.cpu_usage - baseline.cpu_usage) / baseline.cpu_usage
            performance_change["cpu_usage"] = cpu_change
            if cpu_change > self.thresholds["cpu_usage"]:
                regression_detected = True
                recommendations.append(f"CPU usage increased by {cpu_change*100:.1f}%")
        
        if baseline.response_time > 0:
            response_change = (current.response_time - baseline.response_time) / baseline.response_time
            performance_change["response_time"] = response_change
            if response_change > self.thresholds["response_time"]:
                regression_detected = True
                recommendations.append(f"Response time increased by {response_change*100:.1f}%")
        
        if baseline.throughput > 0:
            throughput_change = (current.throughput - baseline.throughput) / baseline.throughput
            performance_change["throughput"] = throughput_change
            if throughput_change < self.thresholds["throughput"]:
                regression_detected = True
                recommendations.append(f"Throughput decreased by {abs(throughput_change)*100:.1f}%")
        
        # Determine severity
        severity = self._calculate_severity(performance_change)
        
        return RegressionTestResult(
            test_name=baseline.test_name,
            baseline=baseline,
            current=current,
            regression_detected=regression_detected,
            performance_change=performance_change,
            severity=severity,
            recommendations=recommendations
        )
    
    def _calculate_severity(self, performance_change: Dict[str, float]) -> str:
        """Calculate regression severity based on performance changes."""
        max_change = max(abs(change) for change in performance_change.values())
        
        if max_change >= 0.50:  # 50% or more
            return "CRITICAL"
        elif max_change >= 0.30:  # 30-50%
            return "HIGH"
        elif max_change >= 0.15:  # 15-30%
            return "MEDIUM"
        else:
            return "LOW"
    
    async def run_regression_test(self, test_name: str) -> RegressionTestResult:
        """Run a specific regression test."""
        baselines = self.load_baselines()
        
        # Get current performance
        if test_name == "startup_performance":
            current = await self.establish_startup_baseline()
        elif test_name == "runtime_performance":
            current = await self.establish_runtime_baseline()
        elif test_name == "lazy_loading_performance":
            current = await self.establish_lazy_loading_baseline()
        else:
            raise ValueError(f"Unknown test: {test_name}")
        
        # Compare with baseline
        if test_name in baselines:
            baseline = baselines[test_name]
            result = self.detect_regression(baseline, current)
        else:
            # No baseline exists, establish one
            baselines[test_name] = current
            self.save_baselines(baselines)
            
            result = RegressionTestResult(
                test_name=test_name,
                baseline=current,
                current=current,
                regression_detected=False,
                performance_change={},
                severity="LOW",
                recommendations=["Baseline established for future regression testing"]
            )
        
        return result
    
    async def run_comprehensive_regression_suite(self) -> List[RegressionTestResult]:
        """Run comprehensive regression test suite."""
        test_names = [
            "startup_performance",
            "runtime_performance", 
            "lazy_loading_performance"
        ]
        
        results = []
        for test_name in test_names:
            try:
                result = await self.run_regression_test(test_name)
                results.append(result)
            except Exception as e:
                print(f"Regression test {test_name} failed: {e}")
        
        return results
    
    def update_baseline(self, test_name: str, new_baseline: PerformanceBaseline):
        """Update baseline for a specific test."""
        baselines = self.load_baselines()
        baselines[test_name] = new_baseline
        self.save_baselines(baselines)


@pytest.fixture
def regression_suite():
    """Create performance regression test suite fixture."""
    return PerformanceRegressionSuite()


@pytest.mark.asyncio
async def test_startup_performance_regression(regression_suite):
    """Test for startup performance regression."""
    result = await regression_suite.run_regression_test("startup_performance")
    
    # Should not have critical regressions
    assert result.severity != "CRITICAL", f"Critical startup regression: {result.recommendations}"
    
    # Warn about high severity regressions
    if result.severity == "HIGH":
        print(f"Warning: High severity startup regression detected: {result.recommendations}")
    
    print(f"Startup regression test: {result.severity} severity")
    if result.performance_change:
        for metric, change in result.performance_change.items():
            print(f"  {metric}: {change*100:+.1f}%")


@pytest.mark.asyncio
async def test_runtime_performance_regression(regression_suite):
    """Test for runtime performance regression."""
    result = await regression_suite.run_regression_test("runtime_performance")
    
    # Should not have critical regressions
    assert result.severity != "CRITICAL", f"Critical runtime regression: {result.recommendations}"
    
    print(f"Runtime regression test: {result.severity} severity")
    if result.performance_change:
        for metric, change in result.performance_change.items():
            print(f"  {metric}: {change*100:+.1f}%")


@pytest.mark.asyncio
async def test_lazy_loading_performance_regression(regression_suite):
    """Test for lazy loading performance regression."""
    result = await regression_suite.run_regression_test("lazy_loading_performance")
    
    # Should not have critical regressions
    assert result.severity != "CRITICAL", f"Critical lazy loading regression: {result.recommendations}"
    
    print(f"Lazy loading regression test: {result.severity} severity")
    if result.performance_change:
        for metric, change in result.performance_change.items():
            print(f"  {metric}: {change*100:+.1f}%")


@pytest.mark.asyncio
async def test_comprehensive_regression_suite(regression_suite):
    """Run comprehensive regression test suite."""
    results = await regression_suite.run_comprehensive_regression_suite()
    
    # Should have results for all tests
    assert len(results) >= 3, f"Not all regression tests completed: {len(results)}"
    
    # Check for critical regressions
    critical_regressions = [r for r in results if r.severity == "CRITICAL"]
    assert len(critical_regressions) == 0, f"Critical regressions detected: {[r.test_name for r in critical_regressions]}"
    
    # Report results
    print("Comprehensive regression test results:")
    for result in results:
        print(f"  {result.test_name}: {result.severity}")
        if result.regression_detected:
            print(f"    Regression: {result.recommendations}")


@pytest.mark.asyncio
async def test_memory_usage_regression():
    """Test for memory usage regression."""
    resource_monitor = ResourceMonitor()
    
    # Measure baseline memory
    initial_memory = psutil.Process().memory_info().rss
    
    # Perform operations that should not leak memory
    for i in range(5):
        lifecycle_manager = ServiceLifecycleManager()
        await lifecycle_manager.start_service(f"memory_test_{i}")
        await asyncio.sleep(0.1)
        await lifecycle_manager.shutdown_service(f"memory_test_{i}")
    
    # Allow cleanup
    await asyncio.sleep(1)
    
    final_memory = psutil.Process().memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Should not have significant memory growth (< 100MB)
    max_growth = 100 * 1024 * 1024  # 100MB
    assert memory_growth < max_growth, f"Memory regression: {memory_growth / 1024 / 1024:.1f}MB growth"
    
    print(f"Memory regression test: {memory_growth / 1024 / 1024:.1f}MB growth")


@pytest.mark.asyncio
async def test_service_count_regression():
    """Test for service count regression (too many services running)."""
    lifecycle_manager = ServiceLifecycleManager()
    
    # Start essential services only
    await lifecycle_manager.start_essential_services()
    
    # Count running services
    running_services = await lifecycle_manager.get_running_services()
    service_count = len(running_services)
    
    # Should not have too many services running (< 10 for essential only)
    max_essential_services = 10
    assert service_count <= max_essential_services, f"Too many services running: {service_count} > {max_essential_services}"
    
    print(f"Service count regression test: {service_count} services running")


@pytest.mark.asyncio
async def test_response_time_regression():
    """Test for response time regression."""
    task_orchestrator = AsyncTaskOrchestrator()
    
    # Measure response times for typical operations
    response_times = []
    
    for i in range(5):
        start_time = time.time()
        
        result = await task_orchestrator.offload_cpu_intensive_task(
            lambda: sum(j * j for j in range(10000))
        )
        
        response_time = time.time() - start_time
        response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times)
    
    # Response time should be reasonable (< 1 second for simple tasks)
    max_response_time = 1.0
    assert avg_response_time < max_response_time, f"Response time regression: {avg_response_time:.3f}s > {max_response_time}s"
    
    print(f"Response time regression test: {avg_response_time:.3f}s average")


@pytest.mark.asyncio
async def test_baseline_establishment():
    """Test baseline establishment for new installations."""
    regression_suite = PerformanceRegressionSuite()
    
    # Clear existing baselines for test
    if os.path.exists(regression_suite.baseline_file):
        os.remove(regression_suite.baseline_file)
    
    # Establish new baseline
    baseline = await regression_suite.establish_startup_baseline()
    
    # Baseline should be valid
    assert baseline.startup_time > 0, "Invalid startup time in baseline"
    assert baseline.memory_usage > 0, "Invalid memory usage in baseline"
    assert baseline.timestamp is not None, "Missing timestamp in baseline"
    
    # Save and reload baseline
    baselines = {"startup_performance": baseline}
    regression_suite.save_baselines(baselines)
    
    loaded_baselines = regression_suite.load_baselines()
    assert "startup_performance" in loaded_baselines, "Baseline not saved/loaded correctly"
    
    print("Baseline establishment test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])