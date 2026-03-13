
# Performance Adaptive Routing Dashboard

This module provides comprehensive dashboard components for visualizing performance metrics and routing decisions for the Karen AI intelligent fallback system.

## Components

- **PerformanceMetricsDashboard**: Real-time performance metrics visualization
- **RoutingDecisions**: Visualizes routing choices and rationale
- **ProviderComparison**: Compares provider performance
- **RoutingAnalytics**: Displays routing effectiveness and trends
- **PerformanceAlerts**: Shows performance degradation and anomalies
- **AdaptiveStrategy**: Displays current routing strategy and configuration

## Features

- Real-time performance monitoring with charts and graphs
- Interactive routing decision visualization
- Provider performance comparisons
- Performance trend analysis and predictions
- Anomaly detection and alerts
- Configurable routing strategies
- Responsive design with accessibility support

## Usage

```tsx
import { PerformanceMetricsDashboard } from '@/components/performance-adaptive-routing';

function Dashboard() {
  return (
    <div>
      <PerformanceMetricsDashboard />
      {/* Other components */}
    </div>
  );
}
