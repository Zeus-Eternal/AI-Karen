"""
Extension Profiler

Provides performance profiling capabilities for extensions including
function-level profiling, memory usage tracking, and performance analysis.
"""

import time
import functools
import threading
import psutil
import tracemalloc
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, ContextManager
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import contextmanager
import cProfile
import pstats
import io

from .models import PerformanceProfile


@dataclass
class FunctionProfile:
    """Profile data for a single function."""
    function_name: str
    module_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    memory_usage: List[float] = field(default_factory=list)
    call_stack_depth: List[int] = field(default_factory=list)
    
    @property
    def average_time(self) -> float:
        """Calculate average execution time."""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def average_memory(self) -> float:
        """Calculate average memory usage."""
        return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0.0


@dataclass
class ProfileSession:
    """Represents a profiling session."""
    session_id: str
    extension_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    function_profiles: Dict[str, FunctionProfile] = field(default_factory=dict)
    memory_snapshots: List[tuple] = field(default_factory=list)  # (timestamp, memory_mb)
    cpu_samples: List[tuple] = field(default_factory=list)  # (timestamp, cpu_percent)
    configuration: Dict[str, Any] = field(default_factory=dict)


class MemoryTracker:
    """Tracks memory usage during profiling."""
    
    def __init__(self):
        self.snapshots = deque(maxlen=1000)
        self.tracking = False
        self.baseline_memory = 0
    
    def start_tracking(self):
        """Start memory tracking."""
        if not self.tracking:
            tracemalloc.start()
            self.tracking = True
            self.baseline_memory = self._get_current_memory()
    
    def stop_tracking(self):
        """Stop memory tracking."""
        if self.tracking:
            tracemalloc.stop()
            self.tracking = False
    
    def take_snapshot(self) -> float:
        """Take a memory snapshot and return current usage in MB."""
        current_memory = self._get_current_memory()
        self.snapshots.append((datetime.utcnow(), current_memory))
        return current_memory
    
    def get_memory_delta(self) -> float:
        """Get memory usage delta from baseline."""
        current_memory = self._get_current_memory()
        return current_memory - self.baseline_memory
    
    def _get_current_memory(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0


class CPUTracker:
    """Tracks CPU usage during profiling."""
    
    def __init__(self):
        self.samples = deque(maxlen=1000)
        self.process = psutil.Process()
    
    def take_sample(self) -> float:
        """Take a CPU usage sample."""
        try:
            cpu_percent = self.process.cpu_percent()
            self.samples.append((datetime.utcnow(), cpu_percent))
            return cpu_percent
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0


class ExtensionProfiler:
    """
    Performance profiler for extensions.
    
    Features:
    - Function-level performance profiling
    - Memory usage tracking
    - CPU usage monitoring
    - Call stack analysis
    - Performance bottleneck detection
    - Profile session management
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        debug_manager=None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.debug_manager = debug_manager
        
        # Profiling state
        self.active_sessions: Dict[str, ProfileSession] = {}
        self.function_profiles: Dict[str, FunctionProfile] = {}
        self.memory_tracker = MemoryTracker()
        self.cpu_tracker = CPUTracker()
        
        # Configuration
        self.profile_memory = True
        self.profile_cpu = True
        self.max_call_stack_depth = 50
        self.sampling_interval = 1.0  # seconds
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Built-in profiler
        self.cprofile_enabled = False
        self.cprofile_data = None
    
    def start_session(
        self,
        session_id: Optional[str] = None,
        profile_memory: bool = True,
        profile_cpu: bool = True,
        enable_cprofile: bool = False
    ) -> str:
        """Start a new profiling session."""
        if session_id is None:
            session_id = f"profile_{int(time.time())}"
        
        with self.lock:
            if session_id in self.active_sessions:
                raise ValueError(f"Profile session {session_id} already active")
            
            session = ProfileSession(
                session_id=session_id,
                extension_id=self.extension_id,
                start_time=datetime.utcnow(),
                configuration={
                    'profile_memory': profile_memory,
                    'profile_cpu': profile_cpu,
                    'enable_cprofile': enable_cprofile
                }
            )
            
            self.active_sessions[session_id] = session
            
            # Start tracking
            if profile_memory:
                self.memory_tracker.start_tracking()
            
            if enable_cprofile:
                self.cprofile_enabled = True
                self.cprofile_data = cProfile.Profile()
                self.cprofile_data.enable()
        
        return session_id
    
    def stop_session(self, session_id: str) -> ProfileSession:
        """Stop a profiling session and return results."""
        with self.lock:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Profile session {session_id} not found")
            
            # Stop profiling
            session.end_time = datetime.utcnow()
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            
            # Stop tracking
            if session.configuration.get('profile_memory'):
                self.memory_tracker.stop_tracking()
                session.memory_snapshots = list(self.memory_tracker.snapshots)
            
            if session.configuration.get('profile_cpu'):
                session.cpu_samples = list(self.cpu_tracker.samples)
            
            # Stop cProfile if enabled
            if self.cprofile_enabled and self.cprofile_data:
                self.cprofile_data.disable()
                self.cprofile_enabled = False
            
            # Copy function profiles
            session.function_profiles = dict(self.function_profiles)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            return session
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._profile_function_call(func, args, kwargs)
        
        return wrapper
    
    @contextmanager
    def profile_block(self, block_name: str):
        """Context manager to profile a code block."""
        start_time = time.perf_counter()
        start_memory = self.memory_tracker.take_snapshot() if self.profile_memory else 0
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            end_memory = self.memory_tracker.take_snapshot() if self.profile_memory else 0
            memory_delta = end_memory - start_memory
            
            self._record_profile_data(
                function_name=block_name,
                module_name="<block>",
                duration=duration,
                memory_usage=memory_delta
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all profiled functions."""
        with self.lock:
            summary = {
                'total_functions': len(self.function_profiles),
                'total_calls': sum(p.call_count for p in self.function_profiles.values()),
                'total_time': sum(p.total_time for p in self.function_profiles.values()),
                'functions': []
            }
            
            # Sort functions by total time
            sorted_functions = sorted(
                self.function_profiles.values(),
                key=lambda p: p.total_time,
                reverse=True
            )
            
            for profile in sorted_functions[:20]:  # Top 20 functions
                summary['functions'].append({
                    'name': profile.function_name,
                    'module': profile.module_name,
                    'calls': profile.call_count,
                    'total_time': profile.total_time,
                    'avg_time': profile.average_time,
                    'min_time': profile.min_time,
                    'max_time': profile.max_time,
                    'avg_memory': profile.average_memory
                })
            
            return summary
    
    def get_bottlenecks(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        with self.lock:
            bottlenecks = []
            
            # Sort by total time
            sorted_functions = sorted(
                self.function_profiles.values(),
                key=lambda p: p.total_time,
                reverse=True
            )
            
            for i, profile in enumerate(sorted_functions[:top_n]):
                bottleneck = {
                    'rank': i + 1,
                    'function': profile.function_name,
                    'module': profile.module_name,
                    'total_time': profile.total_time,
                    'call_count': profile.call_count,
                    'avg_time': profile.average_time,
                    'time_percentage': (profile.total_time / sum(p.total_time for p in self.function_profiles.values())) * 100,
                    'recommendations': self._generate_bottleneck_recommendations(profile)
                }
                bottlenecks.append(bottleneck)
            
            return bottlenecks
    
    def get_memory_analysis(self) -> Dict[str, Any]:
        """Get memory usage analysis."""
        if not self.memory_tracker.snapshots:
            return {'error': 'No memory data available'}
        
        snapshots = list(self.memory_tracker.snapshots)
        memory_values = [snapshot[1] for snapshot in snapshots]
        
        return {
            'current_memory_mb': memory_values[-1] if memory_values else 0,
            'peak_memory_mb': max(memory_values) if memory_values else 0,
            'min_memory_mb': min(memory_values) if memory_values else 0,
            'avg_memory_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
            'memory_growth_mb': memory_values[-1] - memory_values[0] if len(memory_values) > 1 else 0,
            'snapshots_count': len(snapshots),
            'memory_trend': self._calculate_memory_trend(memory_values)
        }
    
    def get_cpu_analysis(self) -> Dict[str, Any]:
        """Get CPU usage analysis."""
        if not self.cpu_tracker.samples:
            return {'error': 'No CPU data available'}
        
        samples = list(self.cpu_tracker.samples)
        cpu_values = [sample[1] for sample in samples]
        
        return {
            'current_cpu_percent': cpu_values[-1] if cpu_values else 0,
            'peak_cpu_percent': max(cpu_values) if cpu_values else 0,
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'samples_count': len(samples),
            'high_cpu_periods': len([v for v in cpu_values if v > 80])
        }
    
    def export_cprofile_stats(self) -> Optional[str]:
        """Export cProfile statistics as string."""
        if not self.cprofile_data:
            return None
        
        s = io.StringIO()
        stats = pstats.Stats(self.cprofile_data, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats()
        
        return s.getvalue()
    
    def clear_profiles(self):
        """Clear all profiling data."""
        with self.lock:
            self.function_profiles.clear()
            self.memory_tracker.snapshots.clear()
            self.cpu_tracker.samples.clear()
            self.cprofile_data = None
    
    def _profile_function_call(self, func: Callable, args: tuple, kwargs: dict):
        """Profile a function call."""
        function_name = func.__name__
        module_name = func.__module__
        
        # Start timing
        start_time = time.perf_counter()
        start_memory = self.memory_tracker.take_snapshot() if self.profile_memory else 0
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # Record error in profiling data
            self._record_profile_data(
                function_name=function_name,
                module_name=module_name,
                duration=time.perf_counter() - start_time,
                memory_usage=0,
                error=str(e)
            )
            raise
        finally:
            # End timing
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            end_memory = self.memory_tracker.take_snapshot() if self.profile_memory else 0
            memory_delta = end_memory - start_memory
            
            self._record_profile_data(
                function_name=function_name,
                module_name=module_name,
                duration=duration,
                memory_usage=memory_delta
            )
    
    def _record_profile_data(
        self,
        function_name: str,
        module_name: str,
        duration: float,
        memory_usage: float,
        error: Optional[str] = None
    ):
        """Record profiling data for a function call."""
        with self.lock:
            profile_key = f"{module_name}.{function_name}"
            
            if profile_key not in self.function_profiles:
                self.function_profiles[profile_key] = FunctionProfile(
                    function_name=function_name,
                    module_name=module_name
                )
            
            profile = self.function_profiles[profile_key]
            profile.call_count += 1
            profile.total_time += duration
            profile.min_time = min(profile.min_time, duration)
            profile.max_time = max(profile.max_time, duration)
            
            if self.profile_memory and memory_usage != 0:
                profile.memory_usage.append(memory_usage)
            
            # Record call stack depth
            import inspect
            stack_depth = len(inspect.stack())
            profile.call_stack_depth.append(stack_depth)
    
    def _generate_bottleneck_recommendations(self, profile: FunctionProfile) -> List[str]:
        """Generate recommendations for performance bottlenecks."""
        recommendations = []
        
        # High total time
        if profile.total_time > 10.0:  # More than 10 seconds total
            recommendations.append("High total execution time - consider optimization or caching")
        
        # High average time
        if profile.average_time > 1.0:  # More than 1 second average
            recommendations.append("High average execution time - review algorithm efficiency")
        
        # High call count with significant time
        if profile.call_count > 1000 and profile.total_time > 5.0:
            recommendations.append("Frequently called expensive function - consider caching or memoization")
        
        # High memory usage
        if profile.average_memory > 100:  # More than 100MB average
            recommendations.append("High memory usage - review data structures and memory management")
        
        # High variance in execution time
        if profile.max_time > profile.min_time * 10:  # 10x variance
            recommendations.append("High execution time variance - investigate inconsistent performance")
        
        return recommendations
    
    def _calculate_memory_trend(self, memory_values: List[float]) -> str:
        """Calculate memory usage trend."""
        if len(memory_values) < 2:
            return "insufficient_data"
        
        # Simple linear trend calculation
        start_avg = sum(memory_values[:len(memory_values)//4]) / (len(memory_values)//4)
        end_avg = sum(memory_values[-len(memory_values)//4:]) / (len(memory_values)//4)
        
        change_percent = ((end_avg - start_avg) / start_avg) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"


def profile_extension_function(profiler: ExtensionProfiler):
    """Decorator factory for profiling extension functions."""
    def decorator(func: Callable) -> Callable:
        return profiler.profile_function(func)
    return decorator


def profile_async_function(profiler: ExtensionProfiler):
    """Decorator for profiling async functions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            function_name = func.__name__
            module_name = func.__module__
            
            start_time = time.perf_counter()
            start_memory = profiler.memory_tracker.take_snapshot() if profiler.profile_memory else 0
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                end_memory = profiler.memory_tracker.take_snapshot() if profiler.profile_memory else 0
                memory_delta = end_memory - start_memory
                
                profiler._record_profile_data(
                    function_name=function_name,
                    module_name=module_name,
                    duration=duration,
                    memory_usage=memory_delta
                )
        
        return wrapper
    return decorator