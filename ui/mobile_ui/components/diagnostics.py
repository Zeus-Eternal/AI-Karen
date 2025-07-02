import streamlit as st
import psutil
import GPUtil
import socket
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import os
import subprocess
from pathlib import Path

# Constants
REFRESH_INTERVAL = 300  # seconds
LOG_TAIL_LINES = 100
CRITICAL_PATHS = ["/etc/app/config.yaml", "/var/log/app"]

class EnterpriseDiagnostics:
    def __init__(self):
        self.last_refresh = None
        self.cached_metrics = {}
        self.thresholds = {
            'cpu': {'warning': 75, 'critical': 90},
            'memory': {'warning': 80, 'critical': 90},
            'disk': {'warning': 85, 'critical': 95},
            'gpu_temp': {'warning': 80, 'critical': 90}
        }

    def _should_refresh(self) -> bool:
        if not self.last_refresh or (datetime.now() - self.last_refresh).seconds > REFRESH_INTERVAL:
            self.last_refresh = datetime.now()
            return True
        return False

    def _get_system_metrics(self) -> Dict:
        """Collect all system metrics with caching"""
        if not self._should_refresh() and self.cached_metrics:
            return self.cached_metrics

        metrics = {
            'timestamp': datetime.now(),
            'system': self._get_cpu_memory(),
            'disk': self._get_disk_metrics(),
            'network': self._get_network_metrics(),
            'gpu': self._get_gpu_metrics(),
            'processes': self._get_process_metrics(),
            'application': self._get_app_metrics(),
            'security': self._get_security_status(),
            'logs': self._get_log_snapshots()
        }
        
        # Store historical data for trends
        self._update_historical_data(metrics)
        self.cached_metrics = metrics
        return metrics

    # === Metric Collection Methods === #
    
    def _get_cpu_memory(self) -> Dict:
        """Get CPU and memory metrics"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_cores': psutil.cpu_count(),
            'memory_total': mem.total,
            'memory_used': mem.used,
            'memory_percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'load_avg': os.getloadavg()
        }

    def _get_disk_metrics(self) -> Dict:
        """Get filesystem and I/O metrics"""
        partitions = []
        for part in psutil.disk_partitions():
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                'mount': part.mountpoint,
                'total': usage.total,
                'used': usage.used,
                'percent': usage.percent,
                'inodes': self._get_inode_usage(part.mountpoint)
            })
        
        io = psutil.disk_io_counters()
        return {
            'partitions': partitions,
            'io_read': io.read_bytes,
            'io_write': io.write_bytes,
            'io_wait': psutil.cpu_times().iowait
        }

    def _get_network_metrics(self) -> Dict:
        """Get network interface metrics"""
        net = psutil.net_io_counters()
        interfaces = []
        for name, stats in psutil.net_if_stats().items():
            addrs = psutil.net_if_addrs().get(name, [])
            ipv4 = next((addr.address for addr in addrs if addr.family == socket.AF_INET), None)
            interfaces.append({
                'interface': name,
                'is_up': stats.isup,
                'ipv4': ipv4,
                'speed': stats.speed,
                'drop_in': stats.dropin,
                'drop_out': stats.dropout
            })
        
        return {
            'interfaces': interfaces,
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'dns_check': self._check_dns_resolution(),
            'http_check': self._check_http_endpoints()
        }

    def _get_gpu_metrics(self) -> Optional[Dict]:
        """Get GPU metrics if available"""
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return None
                
            return [{
                'id': gpu.id,
                'name': gpu.name,
                'load': gpu.load * 100,
                'memory_total': gpu.memoryTotal,
                'memory_used': gpu.memoryUsed,
                'memory_free': gpu.memoryFree,
                'temperature': gpu.temperature,
                'driver': self._get_gpu_driver_info()
            } for gpu in gpus]
        except:
            return None

    def _get_process_metrics(self) -> Dict:
        """Get process and thread metrics"""
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent'],
                    'threads': proc.num_threads()
                })
            except:
                continue
        
        # Sort by CPU then memory
        top_cpu = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:10]
        top_mem = sorted(procs, key=lambda x: x['memory'], reverse=True)[:10]
        
        return {
            'total_processes': len(procs),
            'top_cpu': top_cpu,
            'top_memory': top_mem
        }

    def _get_app_metrics(self) -> Dict:
        """Get application-specific metrics"""
        return {
            'requests': self._get_request_metrics(),
            'errors': self._get_error_rates(),
            'versions': self._get_dependency_versions(),
            'config_drift': self._check_config_drift(),
            'users': self._get_user_metrics()
        }

    # === UI Rendering Methods === #
    
    def render_dashboard(self):
        """Main rendering function for the dashboard"""
        st.title("🚀 Enterprise Diagnostics Dashboard")
        
        try:
            metrics = self._get_system_metrics()
            
            # Overall Status Header
            self._render_status_header(metrics)
            
            # Main Tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "System Health", 
                "Performance", 
                "Security", 
                "Recommendations"
            ])
            
            with tab1:
                self._render_system_health(metrics)
                
            with tab2:
                self._render_performance_metrics(metrics)
                
            with tab3:
                self._render_security_tab(metrics)
                
            with tab4:
                self._render_recommendations(metrics)
                
            # Download and Help Section
            self._render_footer(metrics)
            
        except Exception as e:
            st.error("Failed to generate dashboard")
            st.exception(e)

    def render_diagnostics() -> None:
        st.title("🔍 System Diagnostics")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🖥️ System Info")
            st.text(f"Platform: {platform.system()}")
            st.text(f"Platform Version: {platform.version()}")
            st.text(f"Machine: {platform.machine()}")
            st.text(f"Processor: {platform.processor()}")
            st.text(f"Python Version: {platform.python_version()}")
            st.text(f"Hostname: {socket.gethostname()}")

        with col2:
            st.subheader("📊 Resource Usage")
            mem = psutil.virtual_memory()
            st.text(f"Total RAM: {mem.total / (1024 ** 3):.2f} GB")
            st.text(f"Used RAM: {mem.used / (1024 ** 3):.2f} GB")
            st.text(f"CPU Cores: {psutil.cpu_count(logical=True)}")
            st.text(f"CPU Load: {psutil.cpu_percent(interval=1)}%")
            st.text(f"Disk Usage: {psutil.disk_usage('/').percent}%")

        st.divider()
        st.subheader("📁 Environment & Process")
        st.code("\n".join(f"{k}={v}" for k, v in os.environ.items() if "KARI" in k or "OLLAMA" in k), language="bash")

        st.subheader("🧠 Process Path & Time")
        st.text(f"Launch Time: {datetime.fromtimestamp(psutil.Process().create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
        st.text(f"Executable: {sys.executable}")
        st.text(f"Working Dir: {os.getcwd()}")
        
    def _render_status_header(self, metrics: Dict):
        """Render the colored status header"""
        status = "🟢 Healthy"
        alerts = self._detect_alerts(metrics)
        
        if any(a['severity'] == 'critical' for a in alerts):
            status = "🔴 Critical"
        elif any(a['severity'] == 'warning' for a in alerts):
            status = "🟡 Warning"
            
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.metric("Overall Status", status)
        with cols[1]:
            if alerts:
                with st.expander(f"Active Alerts ({len(alerts)})", expanded=True):
                    for alert in alerts:
                        st.error(f"{alert['source']}: {alert['message']}")
        with cols[2]:
            st.metric("Last Updated", metrics['timestamp'].strftime("%H:%M:%S"))
            
        st.divider()

    def _render_system_health(self, metrics: Dict):
        """Render the system health tab"""
        cols = st.columns(3)
        
        with cols[0]:
            self._render_cpu_memory_card(metrics['system'])
            
        with cols[1]:
            self._render_disk_card(metrics['disk'])
            
        with cols[2]:
            if metrics.get('gpu'):
                self._render_gpu_card(metrics['gpu'])
            else:
                st.info("No GPU detected")
                
        # Network Section
        st.subheader("Network Status")
        self._render_network_table(metrics['network'])
        
        # Process Section
        st.subheader("Process Monitoring")
        self._render_process_tables(metrics['processes'])

    def _render_performance_metrics(self, metrics: Dict):
        """Render performance trends and app metrics"""
        st.subheader("Resource Trends")
        self._render_trend_charts()
        
        st.subheader("Application Metrics")
        self._render_app_metrics(metrics['application'])
        
        st.subheader("Log Viewer")
        self._render_log_viewer(metrics['logs'])

    # ... (additional rendering methods for other tabs)

    # === Helper Methods === #
    
    def _detect_alerts(self, metrics: Dict) -> List[Dict]:
        """Generate alerts based on thresholds"""
        alerts = []
        
        # CPU Alert
        if metrics['system']['cpu_percent'] > self.thresholds['cpu']['critical']:
            alerts.append({
                'source': 'CPU',
                'message': f"High CPU usage: {metrics['system']['cpu_percent']}%",
                'severity': 'critical'
            })
        elif metrics['system']['cpu_percent'] > self.thresholds['cpu']['warning']:
            alerts.append({
                'source': 'CPU',
                'message': f"Elevated CPU usage: {metrics['system']['cpu_percent']}%",
                'severity': 'warning'
            })
            
        # Similar checks for memory, disk, GPU etc...
        
        return alerts

    def _update_historical_data(self, metrics: Dict):
        """Store metrics for trend analysis"""
        # Implementation would use a circular buffer or database
        pass

    def _get_inode_usage(self, mountpoint: str) -> Optional[Dict]:
        """Get inode usage for a filesystem"""
        try:
            output = subprocess.check_output(['df', '-i', mountpoint]).decode()
            lines = output.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    'total': int(parts[1]),
                    'used': int(parts[2]),
                    'percent': int(parts[4].replace('%', ''))
                }
        except:
            return None

# Initialize and run the dashboard
if __name__ == "__main__":
    diag = EnterpriseDiagnostics()
    diag.render_dashboard()