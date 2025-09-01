#!/usr/bin/env python3
"""
Model Orchestrator Monitoring Setup Script

This script sets up comprehensive monitoring for the Model Orchestrator plugin,
integrating with existing Prometheus, Grafana, and logging infrastructure.
"""

import json
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def setup_prometheus_config() -> bool:
    """Set up Prometheus configuration for model orchestrator metrics."""
    try:
        prometheus_config_path = project_root / "monitoring" / "prometheus.yml"
        
        if not prometheus_config_path.exists():
            logger.error(f"Prometheus config not found: {prometheus_config_path}")
            return False
        
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify model orchestrator scrape configs exist
        scrape_configs = config.get('scrape_configs', [])
        model_orchestrator_jobs = [
            job for job in scrape_configs 
            if job.get('job_name', '').startswith('model-orchestrator')
        ]
        
        if not model_orchestrator_jobs:
            logger.warning("Model orchestrator scrape configs not found in Prometheus config")
            return False
        
        logger.info("Prometheus configuration verified for model orchestrator")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Prometheus config: {e}")
        return False


def setup_grafana_dashboards() -> bool:
    """Set up Grafana dashboards for model orchestrator."""
    try:
        dashboard_path = project_root / "monitoring" / "model_orchestrator_dashboard.json"
        
        if not dashboard_path.exists():
            logger.error(f"Model orchestrator dashboard not found: {dashboard_path}")
            return False
        
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)
        
        # Verify dashboard structure
        if 'dashboard' not in dashboard:
            logger.error("Invalid dashboard structure")
            return False
        
        panels = dashboard['dashboard'].get('panels', [])
        if len(panels) < 10:
            logger.warning(f"Dashboard has only {len(panels)} panels, expected more")
        
        logger.info(f"Grafana dashboard verified with {len(panels)} panels")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Grafana dashboards: {e}")
        return False


def setup_alert_rules() -> bool:
    """Set up alert rules for model orchestrator."""
    try:
        alert_rules_path = project_root / "monitoring" / "model_orchestrator_alerts.yml"
        
        if not alert_rules_path.exists():
            logger.error(f"Model orchestrator alert rules not found: {alert_rules_path}")
            return False
        
        with open(alert_rules_path, 'r') as f:
            alerts = yaml.safe_load(f)
        
        # Verify alert structure
        groups = alerts.get('groups', [])
        if not groups:
            logger.error("No alert groups found")
            return False
        
        total_rules = sum(len(group.get('rules', [])) for group in groups)
        logger.info(f"Alert rules verified: {len(groups)} groups, {total_rules} rules")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup alert rules: {e}")
        return False


def setup_logging_config() -> bool:
    """Set up logging configuration for model orchestrator."""
    try:
        logging_config_path = project_root / "config" / "model_orchestrator_logging.yml"
        
        if not logging_config_path.exists():
            logger.error(f"Model orchestrator logging config not found: {logging_config_path}")
            return False
        
        with open(logging_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify logging structure
        if 'logging' not in config:
            logger.error("Invalid logging configuration structure")
            return False
        
        loggers = config['logging'].get('loggers', {})
        model_orchestrator_loggers = [
            name for name in loggers.keys() 
            if 'model_orchestrator' in name or 'model-orchestrator' in name
        ]
        
        logger.info(f"Logging configuration verified with {len(model_orchestrator_loggers)} model orchestrator loggers")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup logging config: {e}")
        return False


def verify_plugin_health_integration() -> bool:
    """Verify that model orchestrator health checks are integrated."""
    try:
        # Check if health check integration exists in main.py
        main_py_path = project_root / "main.py"
        
        if not main_py_path.exists():
            logger.error("main.py not found")
            return False
        
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Look for model orchestrator health integration
        if 'model_orchestrator_health' not in content:
            logger.warning("Model orchestrator health integration not found in main.py")
            return False
        
        if 'model_orchestrator_status' not in content:
            logger.warning("Model orchestrator status not found in health endpoint")
            return False
        
        logger.info("Model orchestrator health integration verified")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify plugin health integration: {e}")
        return False


def create_monitoring_summary() -> Dict[str, Any]:
    """Create a summary of monitoring setup."""
    return {
        "prometheus": {
            "config_path": "monitoring/prometheus.yml",
            "scrape_endpoints": [
                "/api/models/metrics",
                "/api/models/health/metrics"
            ],
            "scrape_interval": "30s"
        },
        "grafana": {
            "dashboard_path": "monitoring/model_orchestrator_dashboard.json",
            "panels": [
                "Model Operations Overview",
                "Download Success Rate", 
                "Storage Usage",
                "Health Status",
                "Download Operations",
                "Download Duration",
                "Models by Library",
                "Storage by Library",
                "Active Downloads",
                "Registry Operations",
                "Error Rates",
                "License Compliance",
                "Garbage Collection"
            ]
        },
        "alerts": {
            "config_path": "monitoring/model_orchestrator_alerts.yml",
            "alert_groups": [
                "model_orchestrator_alerts",
                "model_orchestrator_sla"
            ],
            "notification_channels": [
                "slack",
                "email"
            ]
        },
        "logging": {
            "config_path": "config/model_orchestrator_logging.yml",
            "log_files": [
                "/app/logs/model_orchestrator.log",
                "/app/logs/model_orchestrator_audit.log",
                "/app/logs/model_orchestrator_errors.log"
            ],
            "aggregation": "elasticsearch"
        },
        "health_checks": {
            "endpoint": "/health",
            "model_orchestrator_section": "model_orchestrator",
            "checks": [
                "registry_healthy",
                "storage_healthy",
                "plugin_loaded"
            ]
        }
    }


def main():
    """Main setup function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Setting up Model Orchestrator monitoring...")
    
    success = True
    
    # Setup components
    if not setup_prometheus_config():
        success = False
    
    if not setup_grafana_dashboards():
        success = False
    
    if not setup_alert_rules():
        success = False
    
    if not setup_logging_config():
        success = False
    
    if not verify_plugin_health_integration():
        success = False
    
    # Create summary
    summary = create_monitoring_summary()
    summary_path = project_root / "monitoring" / "model_orchestrator_monitoring_summary.json"
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Monitoring summary saved to: {summary_path}")
    
    if success:
        logger.info("✅ Model Orchestrator monitoring setup completed successfully")
        print("\n🎯 Monitoring Setup Complete!")
        print("📊 Grafana Dashboard: http://localhost:3000")
        print("📈 Prometheus: http://localhost:9090")
        print("🔍 Health Check: http://localhost:8000/health")
        print("📋 Metrics: http://localhost:8000/api/models/metrics")
    else:
        logger.error("❌ Model Orchestrator monitoring setup completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()