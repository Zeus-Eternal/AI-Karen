"""
Backend Integration Test Suite
Tests the integration between Streamlit UI and AI Karen backend services.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
import streamlit as st

from backend_integration import (
    get_backend_service,
    MemoryServiceAdapter,
    PluginServiceAdapter,
    PageServiceAdapter,
    AnalyticsServiceAdapter,
    ServiceConfig
)
from data_flow_manager import get_data_flow_manager, get_streamlit_bridge

logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Test suite for backend integration."""
    
    def __init__(self):
        self.backend = get_backend_service()
        self.dfm = get_data_flow_manager()
        self.bridge = get_streamlit_bridge()
        self.test_results = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        st.write("🧪 Running Backend Integration Tests...")
        
        tests = [
            ("Backend Service Connection", self.test_backend_connection),
            ("Memory Service Integration", self.test_memory_service),
            ("Plugin Service Integration", self.test_plugin_service),
            ("Page Service Integration", self.test_page_service),
            ("Analytics Service Integration", self.test_analytics_service),
            ("Data Flow Manager", self.test_data_flow_manager),
            ("Streamlit Bridge", self.test_streamlit_bridge),
            ("Health Check", self.test_health_check)
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (test_name, test_func) in enumerate(tests):
            status_text.text(f"Running: {test_name}")
            
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "details": result if isinstance(result, dict) else {"success": result}
                }
            except Exception as e:
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "details": {"error": str(e)}
                }
            
            progress_bar.progress((i + 1) / len(tests))
        
        status_text.text("Tests completed!")
        return self.test_results
    
    async def test_backend_connection(self) -> bool:
        """Test basic backend service connection."""
        try:
            # Test service initialization
            assert self.backend is not None, "Backend service not initialized"
            
            # Test service adapters
            assert self.backend.memory is not None, "Memory adapter not available"
            assert self.backend.plugins is not None, "Plugin adapter not available"
            assert self.backend.pages is not None, "Page adapter not available"
            assert self.backend.analytics is not None, "Analytics adapter not available"
            
            return True
        except Exception as e:
            logger.error(f"Backend connection test failed: {e}")
            return False
    
    async def test_memory_service(self) -> Dict[str, Any]:
        """Test memory service integration."""
        try:
            results = {}
            
            # Test memory storage
            test_content = f"Test memory content - {time.time()}"
            memory_id = await self.backend.memory.store_memory(
                content=test_content,
                metadata={"test": True},
                tags=["integration_test"]
            )
            results["store_memory"] = memory_id is not None
            
            # Test memory query
            if memory_id:
                memories = await self.backend.memory.query_memories(
                    query_text="test memory",
                    top_k=5
                )
                results["query_memories"] = len(memories) >= 0
            else:
                results["query_memories"] = False
            
            # Test memory stats
            stats = await self.backend.memory.get_memory_stats()
            results["memory_stats"] = "error" not in stats
            
            # Cleanup test memory
            if memory_id:
                deleted = await self.backend.memory.delete_memory(memory_id)
                results["delete_memory"] = deleted
            
            return results
        except Exception as e:
            logger.error(f"Memory service test failed: {e}")
            return {"error": str(e)}
    
    async def test_plugin_service(self) -> Dict[str, Any]:
        """Test plugin service integration."""
        try:
            results = {}
            
            # Test get available plugins
            plugins = self.backend.plugins.get_available_plugins()
            results["get_plugins"] = len(plugins) >= 0
            
            # Test plugin execution (with a safe plugin if available)
            if plugins:
                # Try to find a safe test plugin
                test_plugin = next((p for p in plugins if "hello" in p["name"].lower()), None)
                if test_plugin:
                    result = await self.backend.plugins.run_plugin(
                        plugin_name=test_plugin["name"],
                        parameters={"test": True}
                    )
                    results["execute_plugin"] = result.get("success", False)
                else:
                    results["execute_plugin"] = "No safe test plugin found"
            else:
                results["execute_plugin"] = "No plugins available"
            
            return results
        except Exception as e:
            logger.error(f"Plugin service test failed: {e}")
            return {"error": str(e)}
    
    async def test_page_service(self) -> Dict[str, Any]:
        """Test page service integration."""
        try:
            results = {}
            
            # Test get available pages
            pages = self.backend.pages.get_available_pages()
            results["get_pages"] = len(pages) >= 0
            
            # Test page access check
            if pages:
                test_page = pages[0]
                has_access = self.backend.pages.check_page_access(test_page["route"])
                results["check_access"] = isinstance(has_access, bool)
            else:
                results["check_access"] = "No pages available"
            
            return results
        except Exception as e:
            logger.error(f"Page service test failed: {e}")
            return {"error": str(e)}
    
    async def test_analytics_service(self) -> Dict[str, Any]:
        """Test analytics service integration."""
        try:
            results = {}
            
            # Test system metrics
            metrics = await self.backend.analytics.get_system_metrics()
            results["system_metrics"] = len(metrics) > 0
            
            # Test usage analytics
            analytics = await self.backend.analytics.get_usage_analytics()
            results["usage_analytics"] = len(analytics) > 0
            
            return results
        except Exception as e:
            logger.error(f"Analytics service test failed: {e}")
            return {"error": str(e)}
    
    async def test_data_flow_manager(self) -> Dict[str, Any]:
        """Test data flow manager."""
        try:
            results = {}
            
            # Test data flow manager initialization
            results["dfm_initialized"] = self.dfm is not None
            
            # Test sync status
            status = self.dfm.get_sync_status()
            results["sync_status"] = isinstance(status, dict)
            
            # Test event emission (non-blocking)
            from data_flow_manager import DataFlowEvent
            test_event = DataFlowEvent(
                event_type="test_event",
                source="integration_test",
                target="test",
                data={"test": True}
            )
            self.dfm.emit_event(test_event)
            results["emit_event"] = True
            
            return results
        except Exception as e:
            logger.error(f"Data flow manager test failed: {e}")
            return {"error": str(e)}
    
    async def test_streamlit_bridge(self) -> Dict[str, Any]:
        """Test Streamlit bridge."""
        try:
            results = {}
            
            # Test bridge initialization
            results["bridge_initialized"] = self.bridge is not None
            
            # Test component state management
            test_state = {"test_key": "test_value", "timestamp": time.time()}
            self.bridge.sync_component_state("test_component", test_state)
            retrieved_state = self.bridge.get_component_state("test_component")
            results["state_management"] = retrieved_state.get("test_key") == "test_value"
            
            return results
        except Exception as e:
            logger.error(f"Streamlit bridge test failed: {e}")
            return {"error": str(e)}
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test overall system health check."""
        try:
            health = await self.backend.health_check()
            
            results = {
                "health_check_available": health is not None,
                "overall_status": health.get("overall", "unknown"),
                "services_count": len(health.get("services", {}))
            }
            
            # Check individual service health
            services = health.get("services", {})
            for service_name, service_info in services.items():
                results[f"{service_name}_status"] = service_info.get("status", "unknown")
            
            return results
        except Exception as e:
            logger.error(f"Health check test failed: {e}")
            return {"error": str(e)}
    
    def render_test_results(self):
        """Render test results in Streamlit."""
        if not self.test_results:
            st.warning("No test results available. Run tests first.")
            return
        
        st.subheader("🧪 Integration Test Results")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results.values() if result["status"] == "FAIL")
        error_tests = sum(1 for result in self.test_results.values() if result["status"] == "ERROR")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", total_tests)
        with col2:
            st.metric("Passed", passed_tests, delta=None)
        with col3:
            st.metric("Failed", failed_tests, delta=None)
        with col4:
            st.metric("Errors", error_tests, delta=None)
        
        # Overall status
        if error_tests > 0:
            st.error("🚨 Some tests encountered errors")
        elif failed_tests > 0:
            st.warning("⚠️ Some tests failed")
        else:
            st.success("✅ All tests passed!")
        
        # Detailed results
        st.markdown("### Detailed Results")
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            details = result["details"]
            
            # Status icon
            if status == "PASS":
                icon = "✅"
                color = "green"
            elif status == "FAIL":
                icon = "❌"
                color = "red"
            else:  # ERROR
                icon = "🚨"
                color = "orange"
            
            with st.expander(f"{icon} {test_name} - {status}"):
                if isinstance(details, dict):
                    for key, value in details.items():
                        if key == "error":
                            st.error(f"Error: {value}")
                        else:
                            st.write(f"**{key}:** {value}")
                else:
                    st.write(details)


def render_integration_test_page():
    """Render the integration test page."""
    st.title("🔧 Backend Integration Tests")
    st.markdown("Test the integration between Streamlit UI and AI Karen backend services.")
    
    # Initialize test suite
    if "test_suite" not in st.session_state:
        st.session_state.test_suite = IntegrationTestSuite()
    
    test_suite = st.session_state.test_suite
    
    # Test controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Run All Tests", type="primary"):
            with st.spinner("Running integration tests..."):
                # Run tests asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(test_suite.run_all_tests())
                st.success("Tests completed!")
                st.rerun()
    
    with col2:
        if st.button("📊 Show Results"):
            test_suite.render_test_results()
    
    with col3:
        if st.button("🔄 Clear Results"):
            st.session_state.test_suite = IntegrationTestSuite()
            st.success("Results cleared!")
            st.rerun()
    
    # Show current results if available
    if test_suite.test_results:
        st.markdown("---")
        test_suite.render_test_results()
    
    # Backend status
    st.markdown("---")
    st.subheader("🔍 Backend Status")
    
    try:
        backend = get_backend_service()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Service Adapters:**")
            st.write(f"- Memory: {'✅' if backend.memory else '❌'}")
            st.write(f"- Plugins: {'✅' if backend.plugins else '❌'}")
            st.write(f"- Pages: {'✅' if backend.pages else '❌'}")
            st.write(f"- Analytics: {'✅' if backend.analytics else '❌'}")
        
        with col2:
            st.write("**Configuration:**")
            st.write(f"- Tenant ID: {backend.config.tenant_id}")
            st.write(f"- User ID: {backend.config.user_id or 'Not set'}")
            st.write(f"- Caching: {'✅' if backend.config.enable_caching else '❌'}")
            st.write(f"- Cache TTL: {backend.config.cache_ttl}s")
    
    except Exception as e:
        st.error(f"Failed to get backend status: {e}")
    
    # Data flow status
    try:
        dfm = get_data_flow_manager()
        status = dfm.get_sync_status()
        
        st.markdown("### 🔄 Data Flow Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cache Size", status["cache_size"])
            st.metric("Queue Size", status["queue_size"])
        
        with col2:
            st.metric("Pending Ops", status["pending_operations"])
            st.metric("Failed Ops", status["failed_operations"])
        
        with col3:
            from datetime import datetime
            last_sync = datetime.fromtimestamp(status["last_sync"]) if status["last_sync"] > 0 else None
            st.write(f"**Last Sync:** {last_sync.strftime('%H:%M:%S') if last_sync else 'Never'}")
            st.write(f"**Sync Enabled:** {'✅' if status['sync_enabled'] else '❌'}")
    
    except Exception as e:
        st.error(f"Failed to get data flow status: {e}")


if __name__ == "__main__":
    render_integration_test_page()