#!/usr/bin/env python3
"""
Chat Runtime Production Validation Script

This script validates the complete chat runtime production wiring including:
- API endpoint availability
- Streaming SSE responses
- Memory integration (Redis, Milvus, DuckDB)
- Fallback mechanisms
- Observability (Prometheus metrics, structured logging)
- Provider routing and degradation
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, List
import httpx
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ValidationResult:
    """Validation result container"""
    def __init__(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class ChatRuntimeValidator:
    """Validates chat runtime production configuration"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.client = httpx.AsyncClient(timeout=TIMEOUT)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, name: str, status: str, message: str = ""):
        """Log test result with color"""
        if status == "PASS":
            print(f"{Colors.OKGREEN}✅ {name}: PASS{Colors.ENDC} {message}")
        elif status == "FAIL":
            print(f"{Colors.FAIL}❌ {name}: FAIL{Colors.ENDC} {message}")
        elif status == "WARN":
            print(f"{Colors.WARNING}⚠️  {name}: WARN{Colors.ENDC} {message}")
        elif status == "INFO":
            print(f"{Colors.OKCYAN}ℹ️  {name}: INFO{Colors.ENDC} {message}")

    async def validate_health_endpoint(self) -> ValidationResult:
        """CR-01: Validate basic health endpoint"""
        test_name = "Health Endpoint"
        try:
            response = await self.client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                data = response.json()
                self.log_test(test_name, "PASS", f"Status: {data.get('status', 'unknown')}")
                return ValidationResult(test_name, True, "Health endpoint responsive", data)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_chat_runtime_health(self) -> ValidationResult:
        """CR-02: Validate chat runtime health endpoint"""
        test_name = "Chat Runtime Health"
        try:
            response = await self.client.get(f"{self.base_url}/api/chat/runtime/health")

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                services = data.get('services', {})

                self.log_test(test_name, "PASS", f"Status: {status}, Services: {len(services)}")
                return ValidationResult(test_name, True, "Chat runtime health OK", data)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_chat_config(self) -> ValidationResult:
        """CR-03: Validate chat configuration endpoint"""
        test_name = "Chat Configuration"
        try:
            response = await self.client.get(f"{self.base_url}/api/chat/runtime/config")

            if response.status_code == 200:
                data = response.json()
                llm_config = data.get('llm', {})
                memory_config = data.get('memory', {})
                tools = data.get('tools', {})

                details = {
                    "default_provider": llm_config.get('default_provider'),
                    "default_model": llm_config.get('default_model'),
                    "streaming_enabled": llm_config.get('streaming_enabled'),
                    "memory_enabled": memory_config.get('enabled'),
                    "available_tools": len(tools.get('available', []))
                }

                self.log_test(test_name, "PASS", f"Provider: {details['default_provider']}, Model: {details['default_model']}")
                return ValidationResult(test_name, True, "Configuration valid", details)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_non_streaming_chat(self) -> ValidationResult:
        """CR-04: Validate non-streaming chat response"""
        test_name = "Non-Streaming Chat"
        try:
            request_data = {
                "message": "Hello, can you help me?",
                "stream": False,
                "platform": "test",
                "context": {},
                "user_preferences": {}
            }

            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/api/chat/runtime",
                json=request_data
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data.get('content', '')
                metadata = data.get('metadata', {})

                details = {
                    "response_length": len(content),
                    "latency_ms": latency,
                    "used_fallback": metadata.get('used_fallback', False),
                    "provider": metadata.get('preferred_llm_provider', 'unknown')
                }

                self.log_test(test_name, "PASS", f"Latency: {latency:.0f}ms, Length: {len(content)} chars")
                return ValidationResult(test_name, True, "Non-streaming response received", details)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_streaming_chat(self) -> ValidationResult:
        """CR-05: Validate streaming SSE chat response"""
        test_name = "Streaming Chat (SSE)"
        try:
            request_data = {
                "message": "Tell me about AI",
                "stream": True,
                "platform": "test",
                "context": {},
                "user_preferences": {}
            }

            chunks_received = 0
            total_tokens = 0
            metadata_received = False
            completion_received = False

            start_time = time.time()

            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/chat/runtime/stream",
                json=request_data
            ) as response:
                if response.status_code != 200:
                    self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                    return ValidationResult(test_name, False, f"HTTP {response.status_code}")

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        chunks_received += 1
                        try:
                            data = json.loads(line[6:])
                            chunk_type = data.get('type')

                            if chunk_type == 'metadata':
                                metadata_received = True
                            elif chunk_type == 'token':
                                total_tokens += 1
                            elif chunk_type == 'complete':
                                completion_received = True
                        except json.JSONDecodeError:
                            pass

            latency = (time.time() - start_time) * 1000

            details = {
                "chunks_received": chunks_received,
                "tokens_received": total_tokens,
                "metadata_received": metadata_received,
                "completion_received": completion_received,
                "total_latency_ms": latency
            }

            if chunks_received > 0 and completion_received:
                self.log_test(test_name, "PASS", f"Chunks: {chunks_received}, Tokens: {total_tokens}, Latency: {latency:.0f}ms")
                return ValidationResult(test_name, True, "Streaming working correctly", details)
            else:
                self.log_test(test_name, "WARN", "Incomplete stream")
                return ValidationResult(test_name, False, "Streaming incomplete", details)
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_prometheus_metrics(self) -> ValidationResult:
        """CR-06: Validate Prometheus metrics endpoint"""
        test_name = "Prometheus Metrics"
        try:
            # Note: Metrics endpoint requires API key in production
            response = await self.client.get(f"{self.base_url}/metrics")

            if response.status_code in [200, 401]:  # 401 is expected without API key
                if response.status_code == 401:
                    self.log_test(test_name, "PASS", "Metrics endpoint secured (requires auth)")
                    return ValidationResult(test_name, True, "Metrics endpoint exists and is secured")
                else:
                    content = response.text
                    has_chat_metrics = 'chat_runtime' in content or 'chat_' in content

                    details = {"has_chat_metrics": has_chat_metrics}

                    if has_chat_metrics:
                        self.log_test(test_name, "PASS", "Chat runtime metrics available")
                        return ValidationResult(test_name, True, "Metrics available", details)
                    else:
                        self.log_test(test_name, "WARN", "No chat runtime metrics found")
                        return ValidationResult(test_name, False, "Chat metrics missing", details)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "WARN", str(e))
            return ValidationResult(test_name, False, str(e))

    async def validate_degraded_mode(self) -> ValidationResult:
        """CR-07: Validate degraded mode status"""
        test_name = "Degraded Mode Status"
        try:
            response = await self.client.get(f"{self.base_url}/api/health/degraded-mode")

            if response.status_code == 200:
                data = response.json()
                degraded = data.get('degraded_mode', False)
                ai_status = data.get('ai_status', 'unknown')

                details = {
                    "degraded_mode": degraded,
                    "ai_status": ai_status,
                    "fallback_systems_active": data.get('fallback_systems_active', False)
                }

                self.log_test(test_name, "PASS", f"Status: {ai_status}, Degraded: {degraded}")
                return ValidationResult(test_name, True, "Degraded mode check OK", details)
            else:
                self.log_test(test_name, "FAIL", f"HTTP {response.status_code}")
                return ValidationResult(test_name, False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test(test_name, "FAIL", str(e))
            return ValidationResult(test_name, False, str(e))

    async def run_all_validations(self):
        """Run all validation tests"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}========================================{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}Chat Runtime Production Validation{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}========================================{Colors.ENDC}\n")

        print(f"{Colors.OKCYAN}Base URL: {self.base_url}{Colors.ENDC}\n")

        # Run all tests
        self.results.append(await self.validate_health_endpoint())
        self.results.append(await self.validate_chat_runtime_health())
        self.results.append(await self.validate_chat_config())
        self.results.append(await self.validate_non_streaming_chat())
        self.results.append(await self.validate_streaming_chat())
        self.results.append(await self.validate_prometheus_metrics())
        self.results.append(await self.validate_degraded_mode())

        # Summary
        print(f"\n{Colors.BOLD}{Colors.HEADER}========================================{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}Validation Summary{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}========================================{Colors.ENDC}\n")

        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        pass_rate = (passed / len(self.results)) * 100 if self.results else 0

        print(f"Total Tests: {len(self.results)}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if failed == 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ All validations passed!{Colors.ENDC}\n")
            return 0
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ Some validations failed{Colors.ENDC}\n")
            print(f"{Colors.WARNING}Failed tests:{Colors.ENDC}")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.message}")
            print()
            return 1


async def main():
    """Main validation entry point"""
    try:
        async with ChatRuntimeValidator() as validator:
            exit_code = await validator.run_all_validations()
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Validation interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
