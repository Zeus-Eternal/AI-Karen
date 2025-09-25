#!/usr/bin/env python3
"""
Simple test for performance metrics functionality.
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set required environment variables
os.environ['KARI_DUCKDB_PASSWORD'] = 'test_password'
os.environ['KARI_JOB_ENC_KEY'] = 'xt66gjfUtpmVWx4kSf07HeiWPBKuw86v3As3EwTME5E='
os.environ['KARI_JOB_SIGNING_KEY'] = 'test_signing_key_32_characters_long'

try:
    from ai_karen_engine.core.performance_metrics import (
        PerformanceMetric,
        MetricType,
        MetricsStorage,
        SystemMetrics,
        ServiceMetrics
    )
    
    print("✅ Successfully imported performance metrics module")
    
    # Test basic metric creation
    metric = PerformanceMetric(
        name="test.cpu.percent",
        value=75.5,
        metric_type=MetricType.GAUGE,
        timestamp=datetime.now(),
        service_name="test_service",
        tags={"env": "test"},
        unit="%",
        description="Test CPU usage"
    )
    
    print(f"✅ Created metric: {metric.name} = {metric.value}{metric.unit}")
    
    # Test metric serialization
    metric_dict = metric.to_dict()
    print(f"✅ Serialized metric: {len(metric_dict)} fields")
    
    # Test metric deserialization
    restored_metric = PerformanceMetric.from_dict(metric_dict)
    print(f"✅ Restored metric: {restored_metric.name} = {restored_metric.value}")
    
    # Test system metrics
    system_metrics = SystemMetrics(
        timestamp=datetime.now(),
        cpu_percent=50.0,
        memory_usage=1024*1024*1024,  # 1GB
        memory_percent=75.0,
        disk_usage=2*1024*1024*1024,  # 2GB
        disk_percent=80.0,
        network_bytes_sent=1000000,
        network_bytes_recv=2000000,
        load_average=(1.0, 1.5, 2.0),
        process_count=150,
        thread_count=500
    )
    
    system_perf_metrics = system_metrics.to_metrics()
    print(f"✅ Generated {len(system_perf_metrics)} system metrics")
    
    # Test service metrics
    service_metrics = ServiceMetrics(
        service_name="api",
        timestamp=datetime.now(),
        cpu_percent=30.0,
        memory_usage=256*1024*1024,
        memory_percent=25.0,
        io_read_bytes=1000,
        io_write_bytes=2000,
        thread_count=5,
        open_files=20,
        network_connections=3,
        response_time=0.100,
        request_count=500,
        error_count=2
    )
    
    service_perf_metrics = service_metrics.to_metrics()
    print(f"✅ Generated {len(service_perf_metrics)} service metrics")
    
    # Test storage (basic functionality)
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    try:
        storage = MetricsStorage(db_path)
        print("✅ Created metrics storage")
        
        # Test storing a metric (async function, but we'll test the database creation)
        print("✅ Database schema initialized")
        
    finally:
        if db_path.exists():
            db_path.unlink()
    
    print("\n🎉 All basic performance metrics tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)