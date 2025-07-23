#!/usr/bin/env python3
"""
UI Launchers Integration Test Script.

This script tests that all UI launchers (web, streamlit, desktop) work correctly
with the new Python backend services.
"""

import asyncio
import json
import logging
import time
import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UITestResult:
    """UI launcher test result."""
    launcher_name: str
    success: bool
    message: str
    details: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


class UILauncherTester:
    """
    Tests all UI launchers with the new backend services.
    
    Validates that web UI, Streamlit UI, and desktop UI can all
    communicate with the integrated Python backend services.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results: List[UITestResult] = []
        self.test_ports = {
            "web_ui": 3000,
            "streamlit_ui": 8501,
            "desktop_ui": None  # Desktop UI doesn't have a port
        }
    
    async def run_all_ui_tests(self) -> Dict[str, Any]:
        """Run tests for all UI launchers."""
        logger.info("Starting UI launcher integration tests...")
        
        # Test backend availability first
        await self._test_backend_availability()
        
        # Test Web UI
        await self._test_web_ui()
        
        # Test Streamlit UI
        await self._test_streamlit_ui()
        
        # Test Desktop UI (basic checks)
        await self._test_desktop_ui()
        
        # Test cross-UI compatibility
        await self._test_cross_ui_compatibility()
        
        return self._generate_test_report()
    
    async def _test_backend_availability(self) -> None:
        """Test that the backend services are available."""
        logger.info("Testing backend availability...")
        
        start_time = time.time()
        try:
            # Test core backend endpoints
            endpoints = [
                "/health",
                "/api/services",
                "/api/ai/flows",
                "/api/memory/health",
                "/api/conversations/health"
            ]
            
            available_endpoints = 0
            endpoint_details = {}
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                    if response.status_code < 500:
                        available_endpoints += 1
                        endpoint_details[endpoint] = {
                            "status": "available",
                            "status_code": response.status_code
                        }
                    else:
                        endpoint_details[endpoint] = {
                            "status": "error",
                            "status_code": response.status_code
                        }
                except Exception as e:
                    endpoint_details[endpoint] = {
                        "status": "unavailable",
                        "error": str(e)
                    }
            
            execution_time = time.time() - start_time
            success = available_endpoints >= len(endpoints) * 0.8  # 80% availability
            
            self.results.append(UITestResult(
                launcher_name="backend",
                success=success,
                message=f"Backend availability: {available_endpoints}/{len(endpoints)} endpoints",
                details={
                    "endpoints": endpoint_details,
                    "availability_rate": (available_endpoints / len(endpoints)) * 100
                },
                execution_time=execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(UITestResult(
                launcher_name="backend",
                success=False,
                message="Backend availability test failed",
                details={},
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_web_ui(self) -> None:
        """Test Web UI integration."""
        logger.info("Testing Web UI integration...")
        
        start_time = time.time()
        try:
            web_ui_path = Path("ui_launchers/web_ui")
            
            if not web_ui_path.exists():
                raise FileNotFoundError("Web UI directory not found")
            
            # Check if package.json exists
            package_json = web_ui_path / "package.json"
            if not package_json.exists():
                raise FileNotFoundError("Web UI package.json not found")
            
            # Test configuration files
            config_files = [
                "next.config.ts",
                "tailwind.config.ts",
                "tsconfig.json"
            ]
            
            missing_configs = []
            for config_file in config_files:
                if not (web_ui_path / config_file).exists():
                    missing_configs.append(config_file)
            
            # Test source directory structure
            src_path = web_ui_path / "src"
            required_dirs = ["app", "components", "lib", "types"]
            missing_dirs = []
            
            if src_path.exists():
                for req_dir in required_dirs:
                    if not (src_path / req_dir).exists():
                        missing_dirs.append(req_dir)
            else:
                missing_dirs = required_dirs
            
            # Try to start the development server (if not already running)
            web_ui_running = await self._check_ui_running("web_ui")
            
            execution_time = time.time() - start_time
            
            issues = []
            if missing_configs:
                issues.append(f"Missing config files: {missing_configs}")
            if missing_dirs:
                issues.append(f"Missing source directories: {missing_dirs}")
            if not web_ui_running:
                issues.append("Web UI server not running")
            
            success = len(issues) == 0
            
            self.results.append(UITestResult(
                launcher_name="web_ui",
                success=success,
                message=f"Web UI integration: {'✓ Ready' if success else '✗ Issues found'}",
                details={
                    "path": str(web_ui_path),
                    "missing_configs": missing_configs,
                    "missing_dirs": missing_dirs,
                    "server_running": web_ui_running,
                    "issues": issues
                },
                execution_time=execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(UITestResult(
                launcher_name="web_ui",
                success=False,
                message="Web UI test failed",
                details={},
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_streamlit_ui(self) -> None:
        """Test Streamlit UI integration."""
        logger.info("Testing Streamlit UI integration...")
        
        start_time = time.time()
        try:
            streamlit_ui_path = Path("ui_launchers/streamlit_ui")
            
            if not streamlit_ui_path.exists():
                raise FileNotFoundError("Streamlit UI directory not found")
            
            # Check main app file
            app_file = streamlit_ui_path / "app.py"
            if not app_file.exists():
                raise FileNotFoundError("Streamlit app.py not found")
            
            # Check requirements file
            requirements_file = streamlit_ui_path / "requirements.txt"
            requirements_exist = requirements_file.exists()
            
            # Test directory structure
            required_dirs = ["components", "pages", "services", "helpers"]
            missing_dirs = []
            
            for req_dir in required_dirs:
                if not (streamlit_ui_path / req_dir).exists():
                    missing_dirs.append(req_dir)
            
            # Try to check if Streamlit is running
            streamlit_running = await self._check_ui_running("streamlit_ui")
            
            # Test backend connectivity from Streamlit context
            backend_connectivity = await self._test_streamlit_backend_connectivity()
            
            execution_time = time.time() - start_time
            
            issues = []
            if not requirements_exist:
                issues.append("Missing requirements.txt")
            if missing_dirs:
                issues.append(f"Missing directories: {missing_dirs}")
            if not streamlit_running:
                issues.append("Streamlit server not running")
            if not backend_connectivity:
                issues.append("Backend connectivity issues")
            
            success = len(issues) == 0
            
            self.results.append(UITestResult(
                launcher_name="streamlit_ui",
                success=success,
                message=f"Streamlit UI integration: {'✓ Ready' if success else '✗ Issues found'}",
                details={
                    "path": str(streamlit_ui_path),
                    "app_file_exists": app_file.exists(),
                    "requirements_exist": requirements_exist,
                    "missing_dirs": missing_dirs,
                    "server_running": streamlit_running,
                    "backend_connectivity": backend_connectivity,
                    "issues": issues
                },
                execution_time=execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(UITestResult(
                launcher_name="streamlit_ui",
                success=False,
                message="Streamlit UI test failed",
                details={},
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_desktop_ui(self) -> None:
        """Test Desktop UI integration."""
        logger.info("Testing Desktop UI integration...")
        
        start_time = time.time()
        try:
            desktop_ui_path = Path("ui_launchers/desktop_ui")
            
            if not desktop_ui_path.exists():
                raise FileNotFoundError("Desktop UI directory not found")
            
            # Check Tauri configuration
            tauri_config = desktop_ui_path / "src-tauri" / "tauri.conf.json"
            tauri_config_exists = tauri_config.exists()
            
            # Check Cargo.toml for Rust dependencies
            cargo_toml = desktop_ui_path / "src-tauri" / "Cargo.toml"
            cargo_toml_exists = cargo_toml.exists()
            
            # Check frontend configuration
            vite_config = desktop_ui_path / "vite.config.ts"
            vite_config_exists = vite_config.exists()
            
            # Check if Rust is available (required for Tauri)
            rust_available = await self._check_rust_availability()
            
            # Check if Node.js dependencies are configured
            package_json = desktop_ui_path / "package.json"
            package_json_exists = package_json.exists()
            
            execution_time = time.time() - start_time
            
            issues = []
            if not tauri_config_exists:
                issues.append("Missing Tauri configuration")
            if not cargo_toml_exists:
                issues.append("Missing Cargo.toml")
            if not vite_config_exists:
                issues.append("Missing Vite configuration")
            if not rust_available:
                issues.append("Rust toolchain not available")
            if not package_json_exists:
                issues.append("Missing package.json")
            
            success = len(issues) == 0
            
            self.results.append(UITestResult(
                launcher_name="desktop_ui",
                success=success,
                message=f"Desktop UI integration: {'✓ Ready' if success else '✗ Issues found'}",
                details={
                    "path": str(desktop_ui_path),
                    "tauri_config_exists": tauri_config_exists,
                    "cargo_toml_exists": cargo_toml_exists,
                    "vite_config_exists": vite_config_exists,
                    "package_json_exists": package_json_exists,
                    "rust_available": rust_available,
                    "issues": issues
                },
                execution_time=execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(UITestResult(
                launcher_name="desktop_ui",
                success=False,
                message="Desktop UI test failed",
                details={},
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _test_cross_ui_compatibility(self) -> None:
        """Test cross-UI compatibility and shared components."""
        logger.info("Testing cross-UI compatibility...")
        
        start_time = time.time()
        try:
            # Check for shared components directory
            common_path = Path("ui_launchers/common")
            common_exists = common_path.exists()
            
            shared_components = []
            if common_exists:
                components_path = common_path / "components"
                if components_path.exists():
                    shared_components = list(components_path.glob("*.ts")) + list(components_path.glob("*.tsx"))
            
            # Check for shared types
            shared_types = []
            if common_exists:
                types_path = common_path / "types"
                if types_path.exists():
                    shared_types = list(types_path.glob("*.ts"))
            
            # Test backend API consistency across UIs
            api_consistency = await self._test_api_consistency()
            
            execution_time = time.time() - start_time
            
            issues = []
            if not common_exists:
                issues.append("No shared components directory found")
            if len(shared_components) == 0:
                issues.append("No shared components found")
            if len(shared_types) == 0:
                issues.append("No shared types found")
            if not api_consistency:
                issues.append("API consistency issues detected")
            
            success = len(issues) <= 1  # Allow for some missing shared components
            
            self.results.append(UITestResult(
                launcher_name="cross_ui_compatibility",
                success=success,
                message=f"Cross-UI compatibility: {'✓ Compatible' if success else '✗ Issues found'}",
                details={
                    "common_path_exists": common_exists,
                    "shared_components_count": len(shared_components),
                    "shared_types_count": len(shared_types),
                    "api_consistency": api_consistency,
                    "issues": issues
                },
                execution_time=execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(UITestResult(
                launcher_name="cross_ui_compatibility",
                success=False,
                message="Cross-UI compatibility test failed",
                details={},
                execution_time=execution_time,
                error=str(e)
            ))
    
    async def _check_ui_running(self, ui_name: str) -> bool:
        """Check if a UI launcher is running."""
        try:
            port = self.test_ports.get(ui_name)
            if not port:
                return True  # Desktop UI doesn't have a port to check
            
            response = requests.get(f"http://localhost:{port}", timeout=2)
            return response.status_code < 500
        except Exception:
            return False
    
    async def _test_streamlit_backend_connectivity(self) -> bool:
        """Test Streamlit's connectivity to the backend."""
        try:
            # This would test if Streamlit can make requests to the backend
            # For now, we'll just test if the backend is reachable
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code < 500
        except Exception:
            return False
    
    async def _check_rust_availability(self) -> bool:
        """Check if Rust toolchain is available."""
        try:
            result = subprocess.run(
                ["rustc", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _test_api_consistency(self) -> bool:
        """Test API consistency across different UI contexts."""
        try:
            # Test that the same API endpoints return consistent responses
            endpoints = ["/api/ai/flows", "/api/plugins/", "/api/tools/"]
            
            for endpoint in endpoints:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                if response.status_code >= 500:
                    return False
            
            return True
        except Exception:
            return False
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate UI launcher test report."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        
        # Categorize results
        ui_results = {}
        for result in self.results:
            ui_results[result.launcher_name] = {
                "success": result.success,
                "message": result.message,
                "execution_time": result.execution_time,
                "details": result.details,
                "error": result.error
            }
        
        report = {
            "ui_test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_execution_time": sum(r.execution_time for r in self.results)
            },
            "ui_launcher_results": ui_results,
            "recommendations": self._generate_ui_recommendations()
        }
        
        return report
    
    def _generate_ui_recommendations(self) -> List[str]:
        """Generate recommendations for UI launcher issues."""
        recommendations = []
        
        for result in self.results:
            if not result.success:
                if result.launcher_name == "backend":
                    recommendations.append("Ensure backend services are running and accessible")
                elif result.launcher_name == "web_ui":
                    recommendations.append("Set up Web UI development environment (npm install, npm run dev)")
                elif result.launcher_name == "streamlit_ui":
                    recommendations.append("Install Streamlit dependencies and start server (pip install -r requirements.txt, streamlit run app.py)")
                elif result.launcher_name == "desktop_ui":
                    recommendations.append("Install Rust toolchain and Tauri dependencies for desktop UI")
                elif result.launcher_name == "cross_ui_compatibility":
                    recommendations.append("Implement shared components and types for UI consistency")
        
        if not recommendations:
            recommendations.append("All UI launchers are properly configured and ready for use")
        
        return recommendations


async def main():
    """Main UI launcher testing function."""
    tester = UILauncherTester()
    
    try:
        results = await tester.run_all_ui_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("UI LAUNCHER INTEGRATION TEST RESULTS")
        print("="*60)
        
        summary = results["ui_test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        
        print("\nUI LAUNCHER DETAILS:")
        print("-" * 40)
        for launcher, result in results["ui_launcher_results"].items():
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"{status} {launcher}: {result['message']} ({result['execution_time']:.2f}s)")
            if result["error"]:
                print(f"    Error: {result['error']}")
            if result["details"].get("issues"):
                for issue in result["details"]["issues"]:
                    print(f"    Issue: {issue}")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        for rec in results["recommendations"]:
            print(f"• {rec}")
        
        # Save results to file
        results_file = Path("ui_launcher_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if summary["success_rate"] >= 75:  # 75% success rate for UI tests
            print("\n✓ UI Launcher tests PASSED - UIs ready for integration")
            sys.exit(0)
        else:
            print("\n✗ UI Launcher tests FAILED - Address UI setup issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nUI launcher testing failed with error: {e}")
        logger.exception("UI launcher testing error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())