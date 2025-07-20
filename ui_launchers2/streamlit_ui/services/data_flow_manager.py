"""
Data Flow Manager
Manages seamless data flow between Streamlit UI and AI Karen backend systems.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import streamlit as st
import threading
import queue
import json

from services.backend_integration import get_backend_service, run_async

logger = logging.getLogger(__name__)


@dataclass
class DataFlowEvent:
    """Represents a data flow event."""
    event_type: str
    source: str
    target: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 1  # 1=low, 2=medium, 3=high
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class DataSyncState:
    """Tracks data synchronization state."""
    last_sync: float = 0
    sync_interval: float = 30  # seconds
    pending_operations: List[str] = field(default_factory=list)
    failed_operations: List[str] = field(default_factory=list)
    sync_enabled: bool = True


class DataFlowManager:
    """Manages data flow between UI components and backend services."""
    
    def __init__(self):
        self.backend = get_backend_service()
        self.event_queue = queue.Queue()
        self.sync_state = DataSyncState()
        self.subscribers = {}  # event_type -> list of callbacks
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.logger = logging.getLogger(f"{__name__}.DataFlowManager")
        
        # Start background processing
        self._start_background_processor()
    
    def _start_background_processor(self):
        """Start background thread for processing events."""
        def process_events():
            while True:
                try:
                    if not self.event_queue.empty():
                        event = self.event_queue.get(timeout=1)
                        self._process_event(event)
                    time.sleep(0.1)
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing events: {e}")
        
        thread = threading.Thread(target=process_events, daemon=True)
        thread.start()
    
    def emit_event(self, event: DataFlowEvent):
        """Emit a data flow event."""
        self.event_queue.put(event)
        self.logger.debug(f"Emitted event: {event.event_type} from {event.source} to {event.target}")
    
    def subscribe(self, event_type: str, callback: Callable[[DataFlowEvent], None]):
        """Subscribe to data flow events."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def _process_event(self, event: DataFlowEvent):
        """Process a data flow event."""
        try:
            # Notify subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Subscriber callback failed: {e}")
            
            # Handle specific event types
            if event.event_type == "memory_store":
                self._handle_memory_store(event)
            elif event.event_type == "memory_query":
                self._handle_memory_query(event)
            elif event.event_type == "plugin_execute":
                self._handle_plugin_execute(event)
            elif event.event_type == "data_sync":
                self._handle_data_sync(event)
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            
            # Retry logic
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                self.event_queue.put(event)
    
    def _handle_memory_store(self, event: DataFlowEvent):
        """Handle memory storage events."""
        try:
            content = event.data.get("content")
            metadata = event.data.get("metadata", {})
            tags = event.data.get("tags", [])
            
            if content:
                memory_id = run_async(self.backend.memory.store_memory(
                    content=content,
                    metadata=metadata,
                    tags=tags
                ))
                
                if memory_id:
                    # Emit success event
                    success_event = DataFlowEvent(
                        event_type="memory_stored",
                        source="data_flow_manager",
                        target=event.source,
                        data={"memory_id": memory_id, "success": True}
                    )
                    self.emit_event(success_event)
                    
                    # Invalidate cache
                    self._invalidate_cache("memory_")
        
        except Exception as e:
            self.logger.error(f"Memory store failed: {e}")
    
    def _handle_memory_query(self, event: DataFlowEvent):
        """Handle memory query events."""
        try:
            query_text = event.data.get("query_text")
            top_k = event.data.get("top_k", 10)
            
            if query_text:
                # Check cache first
                cache_key = f"memory_query_{hash(query_text)}_{top_k}"
                cached_result = self._get_cached_data(cache_key)
                
                if cached_result:
                    result_event = DataFlowEvent(
                        event_type="memory_query_result",
                        source="data_flow_manager",
                        target=event.source,
                        data={"results": cached_result, "cached": True}
                    )
                    self.emit_event(result_event)
                else:
                    # Query backend
                    results = run_async(self.backend.memory.query_memories(
                        query_text=query_text,
                        top_k=top_k
                    ))
                    
                    # Cache results
                    self._cache_data(cache_key, results)
                    
                    # Emit results
                    result_event = DataFlowEvent(
                        event_type="memory_query_result",
                        source="data_flow_manager",
                        target=event.source,
                        data={"results": results, "cached": False}
                    )
                    self.emit_event(result_event)
        
        except Exception as e:
            self.logger.error(f"Memory query failed: {e}")
    
    def _handle_plugin_execute(self, event: DataFlowEvent):
        """Handle plugin execution events."""
        try:
            plugin_name = event.data.get("plugin_name")
            parameters = event.data.get("parameters", {})
            
            if plugin_name:
                result = run_async(self.backend.plugins.run_plugin(
                    plugin_name=plugin_name,
                    parameters=parameters
                ))
                
                # Emit result
                result_event = DataFlowEvent(
                    event_type="plugin_executed",
                    source="data_flow_manager",
                    target=event.source,
                    data={"result": result}
                )
                self.emit_event(result_event)
        
        except Exception as e:
            self.logger.error(f"Plugin execution failed: {e}")
    
    def _handle_data_sync(self, event: DataFlowEvent):
        """Handle data synchronization events."""
        try:
            sync_type = event.data.get("sync_type")
            
            if sync_type == "memory_stats":
                stats = run_async(self.backend.memory.get_memory_stats())
                
                # Update session state
                st.session_state["memory_stats"] = stats
                
                # Emit sync complete
                sync_event = DataFlowEvent(
                    event_type="data_synced",
                    source="data_flow_manager",
                    target=event.source,
                    data={"sync_type": sync_type, "data": stats}
                )
                self.emit_event(sync_event)
        
        except Exception as e:
            self.logger.error(f"Data sync failed: {e}")
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with TTL."""
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["data"]
            else:
                del self.cache[key]
        return None
    
    def _invalidate_cache(self, prefix: str = ""):
        """Invalidate cache entries with given prefix."""
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self.cache[key]
    
    def sync_data(self, sync_type: str, force: bool = False):
        """Trigger data synchronization."""
        current_time = time.time()
        
        if force or (current_time - self.sync_state.last_sync) > self.sync_state.sync_interval:
            sync_event = DataFlowEvent(
                event_type="data_sync",
                source="ui",
                target="backend",
                data={"sync_type": sync_type},
                priority=2
            )
            self.emit_event(sync_event)
            self.sync_state.last_sync = current_time
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status."""
        return {
            "last_sync": self.sync_state.last_sync,
            "sync_enabled": self.sync_state.sync_enabled,
            "pending_operations": len(self.sync_state.pending_operations),
            "failed_operations": len(self.sync_state.failed_operations),
            "cache_size": len(self.cache),
            "queue_size": self.event_queue.qsize()
        }


class StreamlitDataBridge:
    """Bridge between Streamlit components and data flow manager."""
    
    def __init__(self, data_flow_manager: DataFlowManager):
        self.dfm = data_flow_manager
        self.component_states = {}
    
    def store_memory_async(self, content: str, metadata: Dict[str, Any] = None, tags: List[str] = None):
        """Store memory asynchronously."""
        event = DataFlowEvent(
            event_type="memory_store",
            source="streamlit_ui",
            target="backend",
            data={
                "content": content,
                "metadata": metadata or {},
                "tags": tags or []
            }
        )
        self.dfm.emit_event(event)
    
    def query_memory_async(self, query_text: str, top_k: int = 10, callback: Callable = None):
        """Query memory asynchronously."""
        event = DataFlowEvent(
            event_type="memory_query",
            source="streamlit_ui",
            target="backend",
            data={
                "query_text": query_text,
                "top_k": top_k
            }
        )
        
        if callback:
            # Subscribe to result
            def result_handler(result_event: DataFlowEvent):
                if result_event.target == "streamlit_ui":
                    callback(result_event.data.get("results", []))
            
            self.dfm.subscribe("memory_query_result", result_handler)
        
        self.dfm.emit_event(event)
    
    def execute_plugin_async(self, plugin_name: str, parameters: Dict[str, Any], callback: Callable = None):
        """Execute plugin asynchronously."""
        event = DataFlowEvent(
            event_type="plugin_execute",
            source="streamlit_ui",
            target="backend",
            data={
                "plugin_name": plugin_name,
                "parameters": parameters
            }
        )
        
        if callback:
            # Subscribe to result
            def result_handler(result_event: DataFlowEvent):
                if result_event.target == "streamlit_ui":
                    callback(result_event.data.get("result"))
            
            self.dfm.subscribe("plugin_executed", result_handler)
        
        self.dfm.emit_event(event)
    
    def sync_component_state(self, component_id: str, state: Dict[str, Any]):
        """Sync component state."""
        self.component_states[component_id] = {
            "state": state,
            "timestamp": time.time()
        }
        
        # Store in session state for persistence
        if "component_states" not in st.session_state:
            st.session_state.component_states = {}
        st.session_state.component_states[component_id] = state
    
    def get_component_state(self, component_id: str) -> Dict[str, Any]:
        """Get component state."""
        # Try session state first
        if "component_states" in st.session_state:
            if component_id in st.session_state.component_states:
                return st.session_state.component_states[component_id]
        
        # Fallback to local state
        if component_id in self.component_states:
            return self.component_states[component_id]["state"]
        
        return {}
    
    def register_real_time_updates(self, component_id: str, update_interval: int = 30):
        """Register component for real-time updates."""
        def update_handler(event: DataFlowEvent):
            if event.event_type == "data_synced":
                # Update component state
                self.sync_component_state(component_id, {
                    "last_update": time.time(),
                    "data": event.data.get("data")
                })
        
        self.dfm.subscribe("data_synced", update_handler)
        
        # Trigger periodic sync
        self.dfm.sync_data("component_update")


# Global instances
_data_flow_manager: Optional[DataFlowManager] = None
_streamlit_bridge: Optional[StreamlitDataBridge] = None


def get_data_flow_manager() -> DataFlowManager:
    """Get or create global data flow manager."""
    global _data_flow_manager
    if _data_flow_manager is None:
        _data_flow_manager = DataFlowManager()
    return _data_flow_manager


def get_streamlit_bridge() -> StreamlitDataBridge:
    """Get or create global Streamlit bridge."""
    global _streamlit_bridge
    if _streamlit_bridge is None:
        _streamlit_bridge = StreamlitDataBridge(get_data_flow_manager())
    return _streamlit_bridge


# Streamlit-specific utilities
def with_data_flow(func):
    """Decorator to inject data flow capabilities into Streamlit components."""
    def wrapper(*args, **kwargs):
        bridge = get_streamlit_bridge()
        return func(bridge, *args, **kwargs)
    return wrapper


@st.cache_data(ttl=60)
def get_real_time_data(data_type: str) -> Dict[str, Any]:
    """Get real-time data with caching."""
    dfm = get_data_flow_manager()
    
    if data_type == "system_health":
        return run_async(dfm.backend.health_check())
    elif data_type == "memory_stats":
        return run_async(dfm.backend.memory.get_memory_stats())
    elif data_type == "analytics":
        return run_async(dfm.backend.analytics.get_usage_analytics())
    else:
        return {}


def render_data_flow_status():
    """Render data flow status for debugging."""
    dfm = get_data_flow_manager()
    status = dfm.get_sync_status()
    
    with st.expander("🔄 Data Flow Status"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cache Size", status["cache_size"])
            st.metric("Queue Size", status["queue_size"])
        
        with col2:
            st.metric("Pending Ops", status["pending_operations"])
            st.metric("Failed Ops", status["failed_operations"])
        
        with col3:
            last_sync = datetime.fromtimestamp(status["last_sync"]) if status["last_sync"] > 0 else None
            st.write(f"**Last Sync:** {last_sync.strftime('%H:%M:%S') if last_sync else 'Never'}")
            st.write(f"**Sync Enabled:** {'✅' if status['sync_enabled'] else '❌'}")
        
        if st.button("🔄 Force Sync"):
            dfm.sync_data("manual", force=True)
            st.success("Sync triggered!")
            st.rerun()


# Auto-initialization
if "data_flow_initialized" not in st.session_state:
    get_data_flow_manager()
    get_streamlit_bridge()
    st.session_state.data_flow_initialized = True