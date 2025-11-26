#!/usr/bin/env python3
"""
User-friendly dashboard for model management and server monitoring

This module provides a web-based dashboard for managing models,
monitoring server performance, and configuring the llama.cpp server.
"""

import os
import sys
import json
import time
import psutil
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict

# FastAPI imports
FastAPI = None
HTTPException = None
Request = None
Depends = None
HTMLResponse = None
JSONResponse = None
StaticFiles = None
Jinja2Templates = None
CORSMiddleware = None
uvicorn = None
FASTAPI_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException, Request, Depends
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Local imports
try:
    from .config_manager import ConfigManager
    from .error_handler import ErrorCategory, ErrorLevel, handle_error
    from .system_optimizer import SystemOptimizer, get_system_optimizer
    from .backend import get_server
except ImportError:
    # Fallback for standalone usage
    class ConfigManager:
        def __init__(self, config_path=None):
            self.config = {}
        
        def get(self, key, default=None):
            return default
        
        def set(self, key, value):
            pass
        
        def save_config(self):
            return True
    
    class ErrorCategory:
        SYSTEM = 0
        MODEL = 1
        CONFIGURATION = 2
    
    class ErrorLevel:
        ERROR = 0
    
    def handle_error(category, code, details=None, level=ErrorLevel.ERROR):
        pass
    
    class SystemOptimizer:
        def __init__(self):
            self.system_specs = None
            self.recommended_profile = "balanced"
            self.optimization_settings = {}
        
        def apply_optimization_settings(self, config_path=None):
            return True
    
    def get_system_optimizer():
        return SystemOptimizer()
    
    def get_server():
        return None


@dataclass
class ServerStatus:
    """Server status information"""
    running: bool
    uptime_seconds: float
    requests_processed: int
    active_models: List[str]
    system_cpu_percent: float
    system_memory_percent: float
    system_disk_percent: float
    last_error: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class ModelInfo:
    """Model information"""
    name: str
    path: str
    size_mb: float
    loaded: bool
    loading_time: Optional[float] = None
    last_used: Optional[datetime] = None
    parameters: Optional[int] = None
    context_length: Optional[int] = None


class Dashboard:
    """Dashboard for model management and server monitoring"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the dashboard
        
        Args:
            config_path: Path to configuration file
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for the dashboard")
        
        self.config_path = Path(config_path) if config_path else None
        self.config_manager = ConfigManager(config_path)
        self.system_optimizer = get_system_optimizer()
        self.server = get_server()
        
        # Initialize FastAPI app
        if not FASTAPI_AVAILABLE or FastAPI is None:
            raise ImportError("FastAPI is required for the dashboard")
        
        self.app = FastAPI(
            title="Llama.cpp Server Dashboard",
            description="Dashboard for managing models and monitoring server performance",
            version="1.0.0"
        )
        
        # Add CORS middleware
        if CORSMiddleware is not None:
            self.app.add_middleware(
                CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            )
        
        # Setup static files and templates
        self._setup_static_files()
        
        # Setup routes
        self._setup_routes()
        
        # Server status
        self.start_time = time.time()
        self.requests_processed = 0
        self.last_error = None
    
    def _setup_static_files(self):
        """Setup static files and templates"""
        # Create static directory if it doesn't exist
        static_dir = Path(__file__).parent / "static"
        static_dir.mkdir(exist_ok=True)
        
        # Create templates directory if it doesn't exist
        templates_dir = Path(__file__).parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Mount static files
        if StaticFiles is not None:
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Setup templates
        if Jinja2Templates is not None:
            self.templates = Jinja2Templates(directory=str(templates_dir))
        else:
            self.templates = None
        
        # Create basic HTML template if it doesn't exist
        index_template = templates_dir / "index.html"
        if not index_template.exists():
            self._create_index_template(index_template)
        
        # Create basic CSS if it doesn't exist
        css_file = static_dir / "style.css"
        if not css_file.exists():
            self._create_css_file(css_file)
        
        # Create basic JS if it doesn't exist
        js_file = static_dir / "script.js"
        if not js_file.exists():
            self._create_js_file(js_file)
    
    def _create_index_template(self, template_path: Path):
        """Create basic HTML template"""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Llama.cpp Server Dashboard</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Llama.cpp Server Dashboard</h1>
            <div class="status-indicator" id="server-status">
                <span class="status-dot"></span>
                <span class="status-text">Checking...</span>
            </div>
        </header>
        
        <main class="main-content">
            <div class="tabs">
                <button class="tab-button active" data-tab="dashboard">Dashboard</button>
                <button class="tab-button" data-tab="models">Models</button>
                <button class="tab-button" data-tab="settings">Settings</button>
                <button class="tab-button" data-tab="logs">Logs</button>
            </div>
            
            <div class="tab-content">
                <div id="dashboard-tab" class="tab-pane active">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>System Status</h3>
                            <div class="status-grid">
                                <div class="status-item">
                                    <span class="status-label">CPU:</span>
                                    <span class="status-value" id="cpu-status">-</span>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Memory:</span>
                                    <span class="status-value" id="memory-status">-</span>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Disk:</span>
                                    <span class="status-value" id="disk-status">-</span>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Uptime:</span>
                                    <span class="status-value" id="uptime-status">-</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>Server Information</h3>
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-label">Host:</span>
                                    <span class="info-value" id="server-host">-</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Port:</span>
                                    <span class="info-value" id="server-port">-</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Requests:</span>
                                    <span class="info-value" id="requests-count">0</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Active Models:</span>
                                    <span class="info-value" id="active-models-count">0</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>Performance</h3>
                            <div class="chart-container">
                                <canvas id="performance-chart"></canvas>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>Recent Activity</h3>
                            <div class="activity-list" id="activity-list">
                                <div class="activity-item">No recent activity</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="models-tab" class="tab-pane">
                    <div class="models-header">
                        <h2>Model Management</h2>
                        <button class="btn btn-primary" id="add-model-btn">Add Model</button>
                    </div>
                    
                    <div class="models-table-container">
                        <table class="models-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Size</th>
                                    <th>Status</th>
                                    <th>Last Used</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="models-table-body">
                                <tr>
                                    <td colspan="5">Loading models...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="settings-tab" class="tab-pane">
                    <h2>Server Settings</h2>
                    
                    <form id="settings-form" class="settings-form">
                        <div class="settings-section">
                            <h3>Server Configuration</h3>
                            <div class="form-group">
                                <label for="host">Host</label>
                                <input type="text" id="host" name="host" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="port">Port</label>
                                <input type="number" id="port" name="port" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="log-level">Log Level</label>
                                <select id="log-level" name="log_level" class="form-control">
                                    <option value="DEBUG">DEBUG</option>
                                    <option value="INFO">INFO</option>
                                    <option value="WARNING">WARNING</option>
                                    <option value="ERROR">ERROR</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="settings-section">
                            <h3>Performance Settings</h3>
                            <div class="form-group">
                                <label for="num-threads">Number of Threads</label>
                                <input type="number" id="num-threads" name="num_threads" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="batch-size">Batch Size</label>
                                <input type="number" id="batch-size" name="batch_size" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="context-window">Context Window</label>
                                <input type="number" id="context-window" name="context_window" class="form-control">
                            </div>
                            <div class="form-group">
                                <label class="form-check">
                                    <input type="checkbox" id="low-vram" name="low_vram" class="form-check-input">
                                    <span class="form-check-label">Low VRAM Mode</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="settings-section">
                            <h3>Model Settings</h3>
                            <div class="form-group">
                                <label for="model-dir">Model Directory</label>
                                <input type="text" id="model-dir" name="models_directory" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="max-loaded-models">Max Loaded Models</label>
                                <input type="number" id="max-loaded-models" name="max_loaded_models" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="max-cache-gb">Max Cache (GB)</label>
                                <input type="number" id="max-cache-gb" name="max_cache_gb" step="0.1" class="form-control">
                            </div>
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Save Settings</button>
                            <button type="button" class="btn btn-secondary" id="reset-settings">Reset to Defaults</button>
                            <button type="button" class="btn btn-secondary" id="optimize-settings">Optimize for System</button>
                        </div>
                    </form>
                </div>
                
                <div id="logs-tab" class="tab-pane">
                    <h2>Server Logs</h2>
                    
                    <div class="logs-controls">
                        <div class="form-group">
                            <label for="log-level-filter">Filter by Level:</label>
                            <select id="log-level-filter" class="form-control">
                                <option value="ALL">All Levels</option>
                                <option value="DEBUG">DEBUG</option>
                                <option value="INFO">INFO</option>
                                <option value="WARNING">WARNING</option>
                                <option value="ERROR">ERROR</option>
                                <option value="CRITICAL">CRITICAL</option>
                            </select>
                        </div>
                        <button class="btn btn-secondary" id="refresh-logs">Refresh</button>
                        <button class="btn btn-secondary" id="clear-logs">Clear</button>
                    </div>
                    
                    <div class="logs-container">
                        <div id="logs-content">Loading logs...</div>
                    </div>
                </div>
            </div>
        </main>
        
        <footer class="footer">
            <p>Llama.cpp Server Dashboard &copy; 2023</p>
        </footer>
    </div>
    
    <div id="modal-overlay" class="modal-overlay hidden">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-title">Modal Title</h3>
                <button class="modal-close" id="modal-close">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
                Modal content
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
                <button class="btn btn-primary" id="modal-confirm">Confirm</button>
            </div>
        </div>
    </div>
    
    <script src="/static/script.js"></script>
</body>
</html>
"""
        
        with open(template_path, 'w') as f:
            f.write(html_content)
    
    def _create_css_file(self, css_path: Path):
        """Create basic CSS file"""
        css_content = """
/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Roboto', sans-serif;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Header styles */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 15px;
    border-bottom: 1px solid #ddd;
}

.header h1 {
    font-size: 28px;
    font-weight: 500;
    color: #2c3e50;
}

.status-indicator {
    display: flex;
    align-items: center;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #95a5a6;
    margin-right: 8px;
}

.status-dot.online {
    background-color: #2ecc71;
}

.status-dot.offline {
    background-color: #e74c3c;
}

.status-text {
    font-size: 14px;
    font-weight: 500;
}

/* Tab styles */
.tabs {
    display: flex;
    border-bottom: 1px solid #ddd;
    margin-bottom: 20px;
}

.tab-button {
    padding: 10px 20px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    color: #7f8c8d;
    transition: all 0.3s ease;
}

.tab-button:hover {
    color: #3498db;
}

.tab-button.active {
    color: #3498db;
    border-bottom-color: #3498db;
}

/* Tab content styles */
.tab-content {
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 20px;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}

/* Dashboard grid styles */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.card {
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 20px;
}

.card h3 {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 15px;
    color: #2c3e50;
}

.status-grid, .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.status-item, .info-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
}

.status-label, .info-label {
    font-weight: 500;
    color: #7f8c8d;
}

.status-value, .info-value {
    font-weight: 500;
}

/* Chart container */
.chart-container {
    height: 200px;
    position: relative;
}

/* Activity list */
.activity-list {
    max-height: 300px;
    overflow-y: auto;
}

.activity-item {
    padding: 10px;
    border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
    border-bottom: none;
}

/* Models management */
.models-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.models-header h2 {
    font-size: 22px;
    font-weight: 500;
}

.models-table-container {
    overflow-x: auto;
}

.models-table {
    width: 100%;
    border-collapse: collapse;
}

.models-table th, .models-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #f0f0f0;
}

.models-table th {
    font-weight: 500;
    color: #7f8c8d;
    background-color: #f8f9fa;
}

.models-table tr:hover {
    background-color: #f8f9fa;
}

/* Button styles */
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn-primary {
    background-color: #3498db;
    color: white;
}

.btn-primary:hover {
    background-color: #2980b9;
}

.btn-secondary {
    background-color: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background-color: #7f8c8d;
}

.btn-danger {
    background-color: #e74c3c;
    color: white;
}

.btn-danger:hover {
    background-color: #c0392b;
}

.btn-sm {
    padding: 4px 8px;
    font-size: 12px;
}

/* Form styles */
.settings-form {
    max-width: 800px;
}

.settings-section {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f0f0f0;
}

.settings-section h3 {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 15px;
    color: #2c3e50;
}

.form-group {
    margin-bottom: 15px;
}

.form-label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

.form-control {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.form-control:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-check {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.form-check-input {
    margin-right: 8px;
}

.form-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

/* Logs styles */
.logs-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    align-items: center;
}

.logs-container {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 15px;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    max-height: 500px;
    overflow-y: auto;
}

.log-entry {
    margin-bottom: 5px;
    padding-bottom: 5px;
    border-bottom: 1px solid #34495e;
}

.log-entry:last-child {
    border-bottom: none;
}

.log-timestamp {
    color: #95a5a6;
    margin-right: 10px;
}

.log-level-debug {
    color: #3498db;
}

.log-level-info {
    color: #2ecc71;
}

.log-level-warning {
    color: #f39c12;
}

.log-level-error {
    color: #e74c3c;
}

.log-level-critical {
    color: #8e44ad;
}

/* Modal styles */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-overlay.hidden {
    display: none;
}

.modal {
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    width: 90%;
    max-width: 500px;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
    font-size: 18px;
    font-weight: 500;
}

.modal-close {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #7f8c8d;
}

.modal-close:hover {
    color: #2c3e50;
}

.modal-body {
    padding: 15px;
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 15px;
    border-top: 1px solid #f0f0f0;
}

/* Footer styles */
.footer {
    margin-top: 30px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    text-align: center;
    color: #7f8c8d;
    font-size: 14px;
}

/* Responsive styles */
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    .status-grid, .info-grid {
        grid-template-columns: 1fr;
    }
    
    .header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .status-indicator {
        margin-top: 10px;
    }
    
    .models-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    
    .form-actions {
        flex-direction: column;
    }
    
    .logs-controls {
        flex-direction: column;
        align-items: flex-start;
    }
}
"""
        
        with open(css_path, 'w') as f:
            f.write(css_content)
    
    def _create_js_file(self, js_path: Path):
        """Create basic JavaScript file"""
        js_content = """
// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            // Load tab content if needed
            if (tabId === 'dashboard') {
                loadDashboardData();
            } else if (tabId === 'models') {
                loadModelsData();
            } else if (tabId === 'settings') {
                loadSettingsData();
            } else if (tabId === 'logs') {
                loadLogsData();
            }
        });
    });
    
    // Initialize modal
    const modalOverlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    const modalCancel = document.getElementById('modal-cancel');
    
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    if (modalCancel) {
        modalCancel.addEventListener('click', closeModal);
    }
    
    function closeModal() {
        modalOverlay.classList.add('hidden');
    }
    
    // Initialize dashboard
    loadDashboardData();
    
    // Set up periodic refresh
    setInterval(loadDashboardData, 5000); // Refresh every 5 seconds
});

// Load dashboard data
function loadDashboardData() {
    // Load server status
    fetch('/api/server/status')
        .then(response => response.json())
        .then(data => {
            updateServerStatus(data);
        })
        .catch(error => {
            console.error('Error loading server status:', error);
        });
    
    // Load system status
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus(data);
        })
        .catch(error => {
            console.error('Error loading system status:', error);
        });
    
    // Load performance data
    fetch('/api/performance/data')
        .then(response => response.json())
        .then(data => {
            updatePerformanceChart(data);
        })
        .catch(error => {
            console.error('Error loading performance data:', error);
        });
    
    // Load activity data
    fetch('/api/activity/recent')
        .then(response => response.json())
        .then(data => {
            updateActivityList(data);
        })
        .catch(error => {
            console.error('Error loading activity data:', error);
        });
}

// Update server status
function updateServerStatus(data) {
    const statusIndicator = document.getElementById('server-status');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    
    if (data.running) {
        statusDot.classList.add('online');
        statusDot.classList.remove('offline');
        statusText.textContent = 'Online';
    } else {
        statusDot.classList.add('offline');
        statusDot.classList.remove('online');
        statusText.textContent = 'Offline';
    }
    
    // Update server information
    document.getElementById('server-host').textContent = data.host || 'localhost';
    document.getElementById('server-port').textContent = data.port || '8080';
    document.getElementById('requests-count').textContent = data.requests_processed || '0';
    document.getElementById('active-models-count').textContent = data.active_models?.length || '0';
    
    // Update uptime
    if (data.uptime_seconds) {
        const uptime = formatUptime(data.uptime_seconds);
        document.getElementById('uptime-status').textContent = uptime;
    }
}

// Update system status
function updateSystemStatus(data) {
    document.getElementById('cpu-status').textContent = `${data.cpu_percent}%`;
    document.getElementById('memory-status').textContent = `${data.memory_percent}%`;
    document.getElementById('disk-status').textContent = `${data.disk_percent}%`;
}

// Update performance chart
function updatePerformanceChart(data) {
    // This is a placeholder for a real chart implementation
    // In a real implementation, you would use a charting library like Chart.js
    const chartContainer = document.getElementById('performance-chart');
    chartContainer.textContent = 'Performance chart would be displayed here';
}

// Update activity list
function updateActivityList(data) {
    const activityList = document.getElementById('activity-list');
    
    if (data.length === 0) {
        activityList.innerHTML = '<div class="activity-item">No recent activity</div>';
        return;
    }
    
    activityList.innerHTML = '';
    data.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.textContent = `${activity.timestamp}: ${activity.message}`;
        activityList.appendChild(item);
    });
}

// Load models data
function loadModelsData() {
    fetch('/api/models/list')
        .then(response => response.json())
        .then(data => {
            updateModelsTable(data);
        })
        .catch(error => {
            console.error('Error loading models data:', error);
        });
}

// Update models table
function updateModelsTable(data) {
    const tableBody = document.getElementById('models-table-body');
    
    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No models found</td></tr>';
        return;
    }
    
    tableBody.innerHTML = '';
    data.forEach(model => {
        const row = document.createElement('tr');
        
        // Name
        const nameCell = document.createElement('td');
        nameCell.textContent = model.name;
        row.appendChild(nameCell);
        
        // Size
        const sizeCell = document.createElement('td');
        sizeCell.textContent = formatFileSize(model.size_mb);
        row.appendChild(sizeCell);
        
        // Status
        const statusCell = document.createElement('td');
        statusCell.textContent = model.loaded ? 'Loaded' : 'Not Loaded';
        row.appendChild(statusCell);
        
        // Last Used
        const lastUsedCell = document.createElement('td');
        lastUsedCell.textContent = model.last_used || 'Never';
        row.appendChild(lastUsedCell);
        
        // Actions
        const actionsCell = document.createElement('td');
        
        if (model.loaded) {
            const unloadButton = document.createElement('button');
            unloadButton.textContent = 'Unload';
            unloadButton.className = 'btn btn-sm btn-secondary';
            unloadButton.onclick = function() {
                unloadModel(model.name);
            };
            actionsCell.appendChild(unloadButton);
        } else {
            const loadButton = document.createElement('button');
            loadButton.textContent = 'Load';
            loadButton.className = 'btn btn-sm btn-primary';
            loadButton.onclick = function() {
                loadModel(model.name);
            };
            actionsCell.appendChild(loadButton);
        }
        
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.className = 'btn btn-sm btn-danger';
        deleteButton.onclick = function() {
            deleteModel(model.name);
        };
        actionsCell.appendChild(deleteButton);
        
        row.appendChild(actionsCell);
        
        tableBody.appendChild(row);
    });
}

// Load settings data
function loadSettingsData() {
    fetch('/api/settings/get')
        .then(response => response.json())
        .then(data => {
            updateSettingsForm(data);
        })
        .catch(error => {
            console.error('Error loading settings data:', error);
        });
}

// Update settings form
function updateSettingsForm(data) {
    // Update server settings
    if (data.server) {
        document.getElementById('host').value = data.server.host || '';
        document.getElementById('port').value = data.server.port || '';
        document.getElementById('log-level').value = data.server.log_level || 'INFO';
    }
    
    // Update performance settings
    if (data.performance) {
        document.getElementById('num-threads').value = data.performance.num_threads || '';
        document.getElementById('batch-size').value = data.performance.batch_size || '';
        document.getElementById('context-window').value = data.performance.context_window || '';
        document.getElementById('low-vram').checked = data.performance.low_vram || false;
    }
    
    // Update model settings
    if (data.models) {
        document.getElementById('model-dir').value = data.models.directory || '';
        document.getElementById('max-loaded-models').value = data.models.max_loaded_models || '';
        document.getElementById('max-cache-gb').value = data.models.max_cache_gb || '';
    }
}

// Load logs data
function loadLogsData() {
    const levelFilter = document.getElementById('log-level-filter').value;
    
    fetch(`/api/logs/get?level=${levelFilter}`)
        .then(response => response.json())
        .then(data => {
            updateLogsContent(data);
        })
        .catch(error => {
            console.error('Error loading logs data:', error);
        });
}

// Update logs content
function updateLogsContent(data) {
    const logsContent = document.getElementById('logs-content');
    
    if (data.length === 0) {
        logsContent.textContent = 'No logs found';
        return;
    }
    
    logsContent.innerHTML = '';
    data.forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        
        const timestamp = document.createElement('span');
        timestamp.className = 'log-timestamp';
        timestamp.textContent = log.timestamp;
        entry.appendChild(timestamp);
        
        const level = document.createElement('span');
        level.className = `log-level-${log.level.toLowerCase()}`;
        level.textContent = `[${log.level}]`;
        entry.appendChild(level);
        
        const message = document.createElement('span');
        message.textContent = ` ${log.message}`;
        entry.appendChild(message);
        
        logsContent.appendChild(entry);
    });
}

// Format file size
function formatFileSize(sizeMb) {
    if (sizeMb < 1024) {
        return `${sizeMb.toFixed(2)} MB`;
    } else {
        return `${(sizeMb / 1024).toFixed(2)} GB`;
    }
}

// Format uptime
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Load model
function loadModel(modelName) {
    fetch(`/api/models/load`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: modelName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Model ${modelName} loaded successfully`);
            loadModelsData(); // Refresh models list
        } else {
            alert(`Failed to load model: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error loading model:', error);
        alert(`Error loading model: ${error.message}`);
    });
}

// Unload model
function unloadModel(modelName) {
    fetch(`/api/models/unload`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: modelName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Model ${modelName} unloaded successfully`);
            loadModelsData(); // Refresh models list
        } else {
            alert(`Failed to unload model: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error unloading model:', error);
        alert(`Error unloading model: ${error.message}`);
    });
}

// Delete model
function deleteModel(modelName) {
    if (confirm(`Are you sure you want to delete the model ${modelName}?`)) {
        fetch(`/api/models/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: modelName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Model ${modelName} deleted successfully`);
                loadModelsData(); // Refresh models list
            } else {
                alert(`Failed to delete model: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error deleting model:', error);
            alert(`Error deleting model: ${error.message}`);
        });
    }
}

// Save settings
document.getElementById('settings-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const settings = {};
    
    for (const [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    fetch('/api/settings/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Settings saved successfully');
        } else {
            alert(`Failed to save settings: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        alert(`Error saving settings: ${error.message}`);
    });
});

// Reset settings
document.getElementById('reset-settings')?.addEventListener('click', function() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
        fetch('/api/settings/reset', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Settings reset to defaults');
                loadSettingsData(); // Refresh settings form
            } else {
                alert(`Failed to reset settings: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error resetting settings:', error);
            alert(`Error resetting settings: ${error.message}`);
        });
    }
});

// Optimize settings
document.getElementById('optimize-settings')?.addEventListener('click', function() {
    fetch('/api/settings/optimize', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Settings optimized for your system');
            loadSettingsData(); // Refresh settings form
        } else {
            alert(`Failed to optimize settings: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error optimizing settings:', error);
        alert(`Error optimizing settings: ${error.message}`);
    });
});

// Refresh logs
document.getElementById('refresh-logs')?.addEventListener('click', function() {
    loadLogsData();
});

// Clear logs
document.getElementById('clear-logs')?.addEventListener('click', function() {
    if (confirm('Are you sure you want to clear all logs?')) {
        fetch('/api/logs/clear', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Logs cleared successfully');
                loadLogsData(); // Refresh logs
            } else {
                alert(`Failed to clear logs: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error clearing logs:', error);
            alert(`Error clearing logs: ${error.message}`);
        });
    }
});

// Log level filter change
document.getElementById('log-level-filter')?.addEventListener('change', function() {
    loadLogsData();
});

// Add model button
document.getElementById('add-model-btn')?.addEventListener('click', function() {
    // In a real implementation, this would open a modal to add a new model
    alert('Add model functionality would be implemented here');
});
"""
        
        with open(js_path, 'w') as f:
            f.write(js_content)
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def dashboard():
            """Dashboard home page"""
            if self.templates and HTMLResponse:
                return self.templates.TemplateResponse("index.html", {"request": {}})
            return "<html><body>Dashboard requires Jinja2Templates</body></html>"
        
        @self.app.get("/api/server/status")
        async def server_status():
            """Get server status"""
            try:
                # Get server information
                host = self.config_manager.get("server.host", "localhost")
                port = self.config_manager.get("server.port", 8080)
                
                # Get active models
                active_models = []
                if self.server and hasattr(self.server, 'loaded_models'):
                    active_models = list(self.server.loaded_models.keys())
                
                # Calculate uptime
                uptime_seconds = time.time() - self.start_time
                
                return {
                    "running": True,
                    "host": host,
                    "port": port,
                    "uptime_seconds": uptime_seconds,
                    "requests_processed": self.requests_processed,
                    "active_models": active_models,
                    "last_error": self.last_error,
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.SYSTEM,
                        "001",
                        f"Failed to get server status: {e}",
                        ErrorLevel.ERROR
                    )
                return {"running": False, "error": str(e)}
        
        @self.app.get("/api/system/status")
        async def system_status():
            """Get system status"""
            try:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Get memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                return {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.SYSTEM,
                        "002",
                        f"Failed to get system status: {e}",
                        ErrorLevel.ERROR
                    )
                return {"error": str(e)}
        
        @self.app.get("/api/performance/data")
        async def performance_data():
            """Get performance data"""
            try:
                # This is a placeholder for real performance data
                # In a real implementation, you would collect and return actual performance metrics
                return {
                    "cpu_usage": [20, 25, 30, 35, 40, 45, 50, 45, 40, 35, 30, 25],
                    "memory_usage": [40, 42, 44, 46, 48, 50, 48, 46, 44, 42, 40, 38],
                    "response_times": [100, 120, 110, 130, 140, 150, 160, 150, 140, 130, 120, 110],
                    "timestamps": [
                        datetime.now().isoformat() for _ in range(12)
                    ]
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.SYSTEM,
                        "003",
                        f"Failed to get performance data: {e}",
                        ErrorLevel.ERROR
                    )
                return {"error": str(e)}
        
        @self.app.get("/api/activity/recent")
        async def recent_activity():
            """Get recent activity"""
            try:
                # This is a placeholder for real activity data
                # In a real implementation, you would collect and return actual activity logs
                return [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "message": "Server started"
                    },
                    {
                        "timestamp": (datetime.now()).isoformat(),
                        "message": "Model loaded: llama-2-7b-chat"
                    },
                    {
                        "timestamp": (datetime.now()).isoformat(),
                        "message": "Request processed: /health"
                    }
                ]
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.SYSTEM,
                        "004",
                        f"Failed to get recent activity: {e}",
                        ErrorLevel.ERROR
                    )
                return {"error": str(e)}
        
        @self.app.get("/api/models/list")
        async def list_models():
            """List available models"""
            try:
                model_dir_path = self.config_manager.get("models.directory", "")
                if model_dir_path:
                    model_dir = Path(model_dir_path)
                else:
                    model_dir = Path("models")
                models = []
                
                if model_dir.exists():
                    for model_file in model_dir.glob("*.gguf"):
                        model_info = ModelInfo(
                            name=model_file.stem,
                            path=str(model_file),
                            size_mb=model_file.stat().st_size / (1024 * 1024),
                            loaded=False,  # This would be determined by the actual server
                            loading_time=None,
                            last_used=None,
                            parameters=None,  # This would be extracted from the model
                            context_length=None  # This would be extracted from the model
                        )
                        models.append(asdict(model_info))
                
                return models
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.MODEL,
                        "001",
                        f"Failed to list models: {e}",
                        ErrorLevel.ERROR
                    )
                return {"error": str(e)}
        
        @self.app.post("/api/models/load")
        async def load_model():
            """Load a model"""
            try:
                # In a real implementation, you would get the data from the request
                data = {"name": "model_name"}
                model_name = data.get("name")
                
                if not model_name:
                    return {"success": False, "error": "Model name is required"}
                
                # In a real implementation, you would actually load the model
                # For now, we'll just return a success response
                return {
                    "success": True,
                    "message": f"Model {model_name} loaded successfully"
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.MODEL,
                        "002",
                        f"Failed to load model: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/models/unload")
        async def unload_model():
            """Unload a model"""
            try:
                # In a real implementation, you would get the data from the request
                data = {"name": "model_name"}
                model_name = data.get("name")
                
                if not model_name:
                    return {"success": False, "error": "Model name is required"}
                
                # In a real implementation, you would actually unload the model
                # For now, we'll just return a success response
                return {
                    "success": True,
                    "message": f"Model {model_name} unloaded successfully"
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.MODEL,
                        "003",
                        f"Failed to unload model: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/models/delete")
        async def delete_model():
            """Delete a model"""
            try:
                # In a real implementation, you would get the data from the request
                data = {"name": "model_name"}
                model_name = data.get("name")
                
                if not model_name:
                    return {"success": False, "error": "Model name is required"}
                
                model_dir_path = self.config_manager.get("models.directory", "")
                if model_dir_path:
                    model_dir = Path(model_dir_path)
                else:
                    model_dir = Path("models")
                model_path = model_dir / f"{model_name}.gguf"
                
                if not model_path.exists():
                    return {"success": False, "error": "Model file not found"}
                
                model_path.unlink()
                
                return {
                    "success": True,
                    "message": f"Model {model_name} deleted successfully"
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.MODEL,
                        "004",
                        f"Failed to delete model: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/settings/get")
        async def get_settings():
            """Get current settings"""
            try:
                # Get all configuration settings
                settings = self.config_manager.config
                
                return settings
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.CONFIGURATION,
                        "001",
                        f"Failed to get settings: {e}",
                        ErrorLevel.ERROR
                    )
                return {"error": str(e)}
        
        @self.app.post("/api/settings/save")
        async def save_settings():
            """Save settings"""
            try:
                # In a real implementation, you would get the data from the request
                data = {"key": "value"}
                
                # Apply settings
                for key, value in data.items():
                    self.config_manager.set(key, value)
                
                # Save configuration
                success = self.config_manager.save_config()
                
                if success:
                    return {
                        "success": True,
                        "message": "Settings saved successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to save settings"
                    }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.CONFIGURATION,
                        "002",
                        f"Failed to save settings: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/settings/reset")
        async def reset_settings():
            """Reset settings to defaults"""
            try:
                # In a real implementation, you would reset to default settings
                # For now, we'll just return a success response
                return {
                    "success": True,
                    "message": "Settings reset to defaults"
                }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.CONFIGURATION,
                        "003",
                        f"Failed to reset settings: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/settings/optimize")
        async def optimize_settings():
            """Optimize settings for current system"""
            try:
                # Apply optimization settings
                success = self.system_optimizer.apply_optimization_settings(self.config_path)
                
                if success:
                    return {
                        "success": True,
                        "message": "Settings optimized for your system"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to optimize settings"
                    }
            except Exception as e:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.CONFIGURATION,
                        "004",
                        f"Failed to optimize settings: {e}",
                        ErrorLevel.ERROR
                    )
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/logs/get")
        async def get_logs(level: str = "ALL"):
            """Get logs"""
            try:
                # This is a placeholder for real log data
                # In a real implementation, you would read from actual log files
                logs = [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": "Server started"
                    },
                    {
                        "timestamp": (datetime.now()).isoformat(),
                        "level": "INFO",
                        "message": "Model loaded: llama-2-7b-chat"
                    },
                    {
                        "timestamp": (datetime.now()).isoformat(),
                        "level": "WARNING",
                        "message": "High memory usage detected"
                    }
                ]
                
                # Filter by level if specified
                if level != "ALL":
                    logs = [log for log in logs if log["level"] == level]
                
                return logs
            except Exception as e:
                handle_error(
                    ErrorCategory.SYSTEM,
                    "005",
                    f"Failed to get logs: {e}",
                    ErrorLevel.ERROR
                )
                return {"error": str(e)}
        
        @self.app.post("/api/logs/clear")
        async def clear_logs():
            """Clear logs"""
            try:
                # In a real implementation, you would clear actual log files
                # For now, we'll just return a success response
                return {
                    "success": True,
                    "message": "Logs cleared successfully"
                }
            except Exception as e:
                handle_error(
                    ErrorCategory.SYSTEM,
                    "006",
                    f"Failed to clear logs: {e}",
                    ErrorLevel.ERROR
                )
                return {"success": False, "error": str(e)}
    
    def run(self, host: str = "localhost", port: int = 8081, debug: bool = False):
        """Run the dashboard server
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Whether to run in debug mode
        """
        if uvicorn is not None:
            uvicorn.run(self.app, host=host, port=port)


def create_dashboard(config_path: Optional[Union[str, Path]] = None) -> Dashboard:
    """Create dashboard instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dashboard instance
    """
    return Dashboard(config_path)


def run_dashboard(config_path: Optional[Union[str, Path]] = None, 
                 host: str = "localhost", port: int = 8081, debug: bool = False):
    """Run dashboard server
    
    Args:
        config_path: Path to configuration file
        host: Host to bind to
        port: Port to bind to
        debug: Whether to run in debug mode
    """
    dashboard = create_dashboard(config_path)
    dashboard.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard()