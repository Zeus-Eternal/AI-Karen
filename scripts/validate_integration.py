#!/usr/bin/env python3
"""
Integration Validation Script for AI Karen Engine.

This script validates the integration between the new Python backend services
and the existing AI Karen engine, ensuring feature parity and performance.
"""

import asyncio
import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import requests

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.service_registry import get_service_registry, initialize_services
from ai_karen_engine.core.config_manager import get_config_manager
from ai_karen_engine.core.health_monitor import get_health_monitor, setup_default_health_checks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    success: bool
    message: str
    execution_time: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IntegrationValidator:
    """
    Validates the AI Karen engine integration.
    
    Tests service initialization, API endpoints, feature parity,
    and performance benchmarks.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.service_registry = None
        self.health_monitor = None
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("Starting AI Karen integration validation...")
        
        # Test service initialization
        await self._test_service_initialization()
        
        # Test configuration management
        await self._test_configuration_management()
        
        # Test health monitoring
        await self._test_health_monitoring()
        
        # Test API endpoints
        await self._test_api_endpoints()
        
        # Test service integration
        await self._test_service_integration()
        
        # Test performance benchmarks
        await self._test_performance_benchmarks()
        
        # Generate summary
        return self._generate_summary()
    
    async def _test_service_initialization(self) -> None:
        """Test service registry and service initialization."""
        logger.info("Testing service initialization...")
        
        start_time = time.time()
        try:
            # Initialize services
            await initialize_services()
            self.service_registry = get_service_registry()
            
            # Check if all services are registered
            services = self.service_registry.list_services()
            expected_services = [
                "ai_orchestrator", "memory_service", "conversation_service",
                "plugin_service", "tool_service", "analytics_service"
            ]
            
            missing_services = [s for s in expected_services if s not in services]
            if missing_services:
                raise ValueError(f"Missing services: {missing_services}")
            
            # Check service status
            ready_services = sum(
                1 for info in services.values()
                if info["status"] == "ready"
            )
            
            execution_time = time.time() - start_time
            
            self.results.append(ValidationResult(
                test_name="service_initialization",
                success=ready_services == len(expected_services),
                message=f"Initialized {ready_services}/{len(expected_services)} services",
                execution_time=execution_time,
                details={
                    "services": services,
                    "ready_count": ready_services,
                    "total_count": len(expected_services)
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(ValidationResult(
                test_name="service_initialization",
                success=False,
                message="Service initialization failed",
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_configuration_management(self) -> None:
        """Test configuration management system."""
        logger.info("Testing configuration management...")
        
        start_time = time.time()
        try:
            config_manager = get_config_manager()
            config = config_manager.load_config()
            
            # Validate configuration structure
            required_sections = [
                "environment", "database", "redis", "vector_db",
                "llm", "security", "monitoring", "web_ui"
            ]
            
            missing_sections = []
            for section in required_sections:
                if not hasattr(config, section):
                    missing_sections.append(section)
            
            execution_time = time.time() - start_time
            
            self.results.append(ValidationResult(
                test_name="configuration_management",
                success=len(missing_sections) == 0,
                message=f"Configuration loaded with {len(required_sections) - len(missing_sections)}/{len(required_sections)} sections",
                execution_time=execution_time,
                details={
                    "environment": config.environment.value,
                    "missing_sections": missing_sections,
                    "config_sections": required_sections
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(ValidationResult(
                test_name="configuration_management",
                success=False,
                message="Configuration management failed",
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_health_monitoring(self) -> None:
        """Test health monitoring system."""
        logger.info("Testing health monitoring...")
        
        start_time = time.time()
        try:
            await setup_default_health_checks()
            self.health_monitor = get_health_monitor()
            
            # Perform health checks
            health_results = await self.health_monitor.check_all_services()
            
            # Get health summary
            summary = self.health_monitor.get_health_summary()
            
            execution_time = time.time() - start_time
            
            healthy_services = summary["healthy_services"]
            total_services = summary["total_services"]
            
            self.results.append(ValidationResult(
                test_name="health_monitoring",
                success=healthy_services > 0,
                message=f"Health monitoring active with {healthy_services}/{total_services} healthy services",
                execution_time=execution_time,
                details={
                    "health_summary": summary,
                    "health_results": {
                        name: {
                            "status": result.status.value,
                            "message": result.message
                        }
                        for name, result in health_results.items()
                    }
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(ValidationResult(
                test_name="health_monitoring",
                success=False,
                message="Health monitoring failed",
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_api_endpoints(self) -> None:
        """Test API endpoints availability."""
        logger.info("Testing API endpoints...")
        
        endpoints_to_test = [
            ("/health", "GET"),
            ("/api/services", "GET"),
            ("/api/health/summary", "GET"),
            ("/api/config", "GET"),
            ("/api/ai/flows", "GET"),
            ("/api/plugins/", "GET"),
            ("/api/tools/", "GET"),
            ("/api/memory/health", "GET"),
            ("/api/conversations/health", "GET")
        ]
        
        successful_endpoints = 0
        endpoint_results = {}
        
        for endpoint, method in endpoints_to_test:
            start_time = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.request(method, f"{self.base_url}{endpoint}", timeout=10)
                
                execution_time = time.time() - start_time
                
                if response.status_code < 500:  # Accept 4xx as valid (auth issues, etc.)
                    successful_endpoints += 1
                    endpoint_results[endpoint] = {
                        "success": True,
                        "status_code": response.status_code,
                        "response_time": execution_time
                    }
                else:
                    endpoint_results[endpoint] = {
                        "success": False,
                        "status_code": response.status_code,
                        "response_time": execution_time,
                        "error": response.text[:200]
                    }
                    
            except Exception as e:
                execution_time = time.time() - start_time
                endpoint_results[endpoint] = {
                    "success": False,
                    "status_code": 0,
                    "response_time": execution_time,
                    "error": str(e)
                }
        
        self.results.append(ValidationResult(
            test_name="api_endpoints",
            success=successful_endpoints >= len(endpoints_to_test) * 0.8,  # 80% success rate
            message=f"API endpoints: {successful_endpoints}/{len(endpoints_to_test)} accessible",
            execution_time=sum(r.get("response_time", 0) for r in endpoint_results.values()),
            details={"endpoints": endpoint_results}
        ))
    
    async def _test_service_integration(self) -> None:
        """Test service integration and communication."""
        logger.info("Testing service integration...")
        
        start_time = time.time()
        try:
            if not self.service_registry:
                raise ValueError("Service registry not initialized")
            
            # Test AI Orchestrator
            ai_orchestrator = await self.service_registry.get_service("ai_orchestrator")
            if not ai_orchestrator:
                raise ValueError("AI Orchestrator not available")
            
            # Test Memory Service
            memory_service = await self.service_registry.get_service("memory_service")
            if not memory_service:
                raise ValueError("Memory Service not available")
            
            # Test Conversation Service
            conversation_service = await self.service_registry.get_service("conversation_service")
            if not conversation_service:
                raise ValueError("Conversation Service not available")
            
            # Test Plugin Service
            plugin_service = await self.service_registry.get_service("plugin_service")
            if not plugin_service:
                raise ValueError("Plugin Service not available")
            
            # Test Tool Service
            tool_service = await self.service_registry.get_service("tool_service")
            if not tool_service:
                raise ValueError("Tool Service not available")
            
            execution_time = time.time() - start_time
            
            self.results.append(ValidationResult(
                test_name="service_integration",
                success=True,
                message="All core services accessible and integrated",
                execution_time=execution_time,
                details={
                    "services_tested": [
                        "ai_orchestrator", "memory_service", "conversation_service",
                        "plugin_service", "tool_service"
                    ]
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(ValidationResult(
                test_name="service_integration",
                success=False,
                message="Service integration failed",
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_performance_benchmarks(self) -> None:
        """Test performance benchmarks."""
        logger.info("Testing performance benchmarks...")
        
        start_time = time.time()
        try:
            if not self.service_registry:
                raise ValueError("Service registry not initialized")
            
            # Benchmark service initialization time
            init_times = []
            for _ in range(3):  # Test 3 times
                init_start = time.time()
                await self.service_registry.get_service("ai_orchestrator")
                init_times.append(time.time() - init_start)
            
            avg_init_time = sum(init_times) / len(init_times)
            
            # Benchmark health check time
            if self.health_monitor:
                health_start = time.time()
                await self.health_monitor.check_all_services()
                health_check_time = time.time() - health_start
            else:
                health_check_time = 0
            
            execution_time = time.time() - start_time
            
            # Performance criteria
            init_time_ok = avg_init_time < 1.0  # Should initialize in under 1 second
            health_check_ok = health_check_time < 5.0  # Health check should complete in under 5 seconds
            
            self.results.append(ValidationResult(
                test_name="performance_benchmarks",
                success=init_time_ok and health_check_ok,
                message=f"Performance: init={avg_init_time:.2f}s, health={health_check_time:.2f}s",
                execution_time=execution_time,
                details={
                    "average_init_time": avg_init_time,
                    "health_check_time": health_check_time,
                    "init_time_ok": init_time_ok,
                    "health_check_ok": health_check_ok,
                    "benchmarks": {
                        "max_init_time": 1.0,
                        "max_health_check_time": 5.0
                    }
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(ValidationResult(
                test_name="performance_benchmarks",
                success=False,
                message="Performance benchmarking failed",
                execution_time=execution_time,
                error=str(e)
            ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        total_execution_time = sum(r.execution_time for r in self.results)
        
        summary = {
            "validation_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_execution_time": total_execution_time
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "execution_time": r.execution_time,
                    "error": r.error,
                    "details": r.details
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_tests = [r for r in self.results if not r.success]
        
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests before deployment")
        
        # Check performance
        perf_result = next((r for r in self.results if r.test_name == "performance_benchmarks"), None)
        if perf_result and perf_result.details:
            if not perf_result.details.get("init_time_ok"):
                recommendations.append("Optimize service initialization time")
            if not perf_result.details.get("health_check_ok"):
                recommendations.append("Optimize health check performance")
        
        # Check API endpoints
        api_result = next((r for r in self.results if r.test_name == "api_endpoints"), None)
        if api_result and not api_result.success:
            recommendations.append("Fix API endpoint accessibility issues")
        
        if not recommendations:
            recommendations.append("All validations passed - system ready for deployment")
        
        return recommendations


async def main():
    """Main validation function."""
    validator = IntegrationValidator()
    
    try:
        results = await validator.run_all_validations()
        
        # Print summary
        print("\n" + "="*60)
        print("AI KAREN INTEGRATION VALIDATION RESULTS")
        print("="*60)
        
        summary = results["validation_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        
        print("\nTEST DETAILS:")
        print("-" * 40)
        for test in results["test_results"]:
            status = "✓ PASS" if test["success"] else "✗ FAIL"
            print(f"{status} {test['test_name']}: {test['message']} ({test['execution_time']:.2f}s)")
            if test["error"]:
                print(f"    Error: {test['error']}")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        for rec in results["recommendations"]:
            print(f"• {rec}")
        
        # Save results to file
        results_file = Path("validation_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if summary["success_rate"] >= 80:
            print("\n✓ Validation PASSED - System ready for integration")
            sys.exit(0)
        else:
            print("\n✗ Validation FAILED - Address issues before deployment")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nValidation failed with error: {e}")
        logger.exception("Validation error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())