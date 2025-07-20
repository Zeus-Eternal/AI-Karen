"""
Data generation and utility functions for the Streamlit UI
"""

import pandas as pd
import numpy as np
from datetime import datetime


def generate_sample_data():
    """Generate sample data for interactive components"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-07-19', freq='D')
    
    # System metrics data
    metrics_data = pd.DataFrame({
        'date': dates,
        'cpu_usage': np.random.normal(45, 15, len(dates)).clip(0, 100),
        'memory_usage': np.random.normal(60, 20, len(dates)).clip(0, 100),
        'requests': np.random.poisson(1000, len(dates)),
        'response_time': np.random.exponential(0.2, len(dates)),
        'errors': np.random.poisson(5, len(dates))
    })
    
    # Chat data
    chat_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-07-01', periods=100, freq='H'),
        'user_id': np.random.choice(['user_1', 'user_2', 'user_3', 'user_4'], 100),
        'message_length': np.random.normal(50, 20, 100).clip(5, 200),
        'sentiment': np.random.choice(['positive', 'neutral', 'negative'], 100, p=[0.6, 0.3, 0.1]),
        'topic': np.random.choice(['tech', 'support', 'general', 'feedback'], 100)
    })
    
    return metrics_data, chat_data


def generate_real_time_kpis():
    """Generate real-time KPI data"""
    system_health = np.random.uniform(85, 99)
    cpu_usage = np.random.uniform(20, 80)
    memory_usage = np.random.uniform(40, 85)
    active_users = np.random.randint(150, 500)
    requests_per_min = np.random.randint(800, 2000)
    error_rate = np.random.uniform(0.1, 2.5)
    
    return [
        ("System Health", f"{system_health:.1f}%", "🟢" if system_health > 90 else "🟡" if system_health > 80 else "🔴"),
        ("CPU Usage", f"{cpu_usage:.1f}%", "🟢" if cpu_usage < 70 else "🟡" if cpu_usage < 85 else "🔴"),
        ("Memory", f"{memory_usage:.1f}%", "🟢" if memory_usage < 80 else "🟡" if memory_usage < 90 else "🔴"),
        ("Active Users", f"{active_users:,}", "👥"),
        ("Requests/min", f"{requests_per_min:,}", "📊"),
        ("Error Rate", f"{error_rate:.2f}%", "🟢" if error_rate < 1 else "🟡" if error_rate < 2 else "🔴")
    ]


def generate_service_health_data():
    """Generate service health monitoring data"""
    services = ['API Gateway', 'Database', 'Cache', 'Auth Service', 'File Storage', 'Analytics']
    health_status = np.random.choice(['Healthy', 'Warning', 'Critical'], len(services), p=[0.7, 0.2, 0.1])
    response_times = np.random.exponential(0.1, len(services)) * 1000  # ms
    
    return pd.DataFrame({
        'Service': services,
        'Status': health_status,
        'Response Time (ms)': response_times
    })


def generate_analytics_data(time_period):
    """Generate analytics data based on time period"""
    if "7 days" in time_period:
        periods = 7
        freq = 'D'
    elif "30 days" in time_period:
        periods = 30
        freq = 'D'
    elif "90 days" in time_period:
        periods = 90
        freq = 'D'
    else:
        periods = 12
        freq = 'M'
    
    dates = pd.date_range(
        start=datetime.now() - pd.Timedelta(days=periods if freq == 'D' else periods*30), 
        end=datetime.now(), 
        freq=freq
    )
    
    analytics_data = pd.DataFrame({
        'date': dates,
        'users': np.random.poisson(1000, len(dates)) + np.random.randint(500, 1500),
        'sessions': np.random.poisson(1500, len(dates)) + np.random.randint(800, 2000),
        'requests': np.random.poisson(10000, len(dates)) + np.random.randint(5000, 15000),
        'errors': np.random.poisson(50, len(dates)) + np.random.randint(10, 100)
    })
    
    return analytics_data