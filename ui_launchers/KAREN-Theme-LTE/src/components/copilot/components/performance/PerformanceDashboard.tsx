import React, { useState, useEffect, useRef } from 'react';
import { usePerformanceMonitor } from '../../utils/performance-monitoring';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: {
    used: number;
    total: number;
    percentage: number;
    limit: number;
  };
  timestamp: number;
}

interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface PerformanceDashboardProps {
  theme: Theme;
  isVisible?: boolean;
  onClose?: () => void;
  className?: string;
}

interface PerformanceMetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status?: 'normal' | 'warning' | 'critical';
  theme: Theme;
}

/**
 * Performance metric card component
 */
const PerformanceMetricCard: React.FC<PerformanceMetricCardProps> = ({
  title,
  value,
  unit,
  status = 'normal',
  theme
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'warning': return theme.colors.warning;
      case 'critical': return theme.colors.error;
      default: return theme.colors.primary;
    }
  };

  return (
    <div
      className="performance-metric-card"
      style={{
        backgroundColor: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        padding: theme.spacing.md,
        boxShadow: theme.shadows.sm,
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing.xs
      }}
    >
      <div
        className="metric-title"
        style={{
          fontSize: theme.typography.fontSize.sm,
          color: theme.colors.textSecondary,
          fontWeight: theme.typography.fontWeight.normal
        }}
      >
        {title}
      </div>
      <div
        className="metric-value"
        style={{
          fontSize: theme.typography.fontSize.lg,
          color: getStatusColor(),
          fontWeight: theme.typography.fontWeight.bold,
          display: 'flex',
          alignItems: 'baseline',
          gap: theme.spacing.xs
        }}
      >
        {value}
        {unit && (
          <span
            className="metric-unit"
            style={{
              fontSize: theme.typography.fontSize.sm,
              fontWeight: theme.typography.fontWeight.normal
            }}
          >
            {unit}
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * Performance bar chart component
 */
interface PerformanceBarChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  maxValue: number;
  theme: Theme;
}

const PerformanceBarChart: React.FC<PerformanceBarChartProps> = ({
  data,
  maxValue,
  theme
}) => {
  return (
    <div
      className="performance-bar-chart"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing.sm
      }}
    >
      {data.map((item, index) => (
        <div
          key={index}
          className="bar-chart-item"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.sm
          }}
        >
          <div
            className="bar-chart-label"
            style={{
              width: '120px',
              fontSize: theme.typography.fontSize.xs,
              color: theme.colors.textSecondary
            }}
          >
            {item.label}
          </div>
          <div
            className="bar-chart-container"
            style={{
              flex: 1,
              height: '20px',
              backgroundColor: theme.colors.border,
              borderRadius: '4px',
              overflow: 'hidden',
              position: 'relative'
            }}
          >
            <div
              className="bar-chart-fill"
              style={{
                height: '100%',
                width: `${(item.value / maxValue) * 100}%`,
                backgroundColor: item.color || theme.colors.primary,
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div
            className="bar-chart-value"
            style={{
              width: '50px',
              fontSize: theme.typography.fontSize.xs,
              color: theme.colors.text,
              textAlign: 'right'
            }}
          >
            {item.value.toFixed(2)}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Performance dashboard component
 */
export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  theme,
  isVisible = true,
  onClose,
  className = ''
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [isExpanded, setIsExpanded] = useState(true);
  const maxMetrics = useRef(20);

  const { metrics: currentMetrics } = usePerformanceMonitor('PerformanceDashboard', {
    enableMemoryTracking: true,
    sampleInterval: 1000,
    onMetricsUpdate: (newMetrics) => {
      setMetrics(prev => {
        const updated = [...prev, newMetrics];
        // Keep only the most recent metrics
        return updated.slice(-(maxMetrics.current || 20));
      });
    }
  });

  // Calculate average metrics
  const avgRenderTime = metrics.length > 0
    ? metrics.reduce((sum, m) => sum + m.renderTime, 0) / metrics.length
    : 0;

  const latestMetrics = metrics[metrics.length - 1];
  const memoryPercentage = latestMetrics?.memoryUsage?.percentage || 0;

  // Get memory status
  const getMemoryStatus = (): 'normal' | 'warning' | 'critical' => {
    if (memoryPercentage > 90) return 'critical';
    if (memoryPercentage > 70) return 'warning';
    return 'normal';
  };

  // Prepare chart data
  const chartData = metrics
    .slice(-10) // Last 10 metrics
    .map((m, index) => ({
      label: `${index + 1}`,
      value: m.renderTime,
      color: m.renderTime > 16 ? theme.colors.warning : theme.colors.primary
    }));

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`performance-dashboard ${className}`}
      style={{
        position: 'fixed',
        bottom: theme.spacing.lg,
        right: theme.spacing.lg,
        width: isExpanded ? '400px' : '60px',
        backgroundColor: theme.colors.background,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        boxShadow: theme.shadows.lg,
        zIndex: 1000,
        transition: 'width 0.3s ease',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <div
        className="dashboard-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: theme.spacing.md,
          borderBottom: `1px solid ${theme.colors.border}`,
          backgroundColor: theme.colors.surface
        }}
      >
        <div
          className="dashboard-title"
          style={{
            fontSize: theme.typography.fontSize.lg,
            fontWeight: theme.typography.fontWeight.bold,
            color: theme.colors.text
          }}
        >
          {isExpanded ? 'Performance Dashboard' : '⚡'}
        </div>
        <div
          className="dashboard-controls"
          style={{
            display: 'flex',
            gap: theme.spacing.sm
          }}
        >
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'none',
              border: 'none',
              color: theme.colors.textSecondary,
              cursor: 'pointer',
              fontSize: '1rem'
            }}
            aria-label={isExpanded ? 'Collapse dashboard' : 'Expand dashboard'}
          >
            {isExpanded ? '−' : '+'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: theme.colors.textSecondary,
                cursor: 'pointer',
                fontSize: '1rem'
              }}
              aria-label="Close dashboard"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div
          className="dashboard-content"
          style={{
            padding: theme.spacing.md,
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.md
          }}
        >
          {/* Metrics Grid */}
          <div
            className="metrics-grid"
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: theme.spacing.sm
            }}
          >
            <PerformanceMetricCard
              title="Avg. Render Time"
              value={avgRenderTime.toFixed(2)}
              unit="ms"
              status={avgRenderTime > 16 ? 'warning' : 'normal'}
              theme={theme}
            />
            <PerformanceMetricCard
              title="Memory Usage"
              value={memoryPercentage.toFixed(1)}
              unit="%"
              status={getMemoryStatus()}
              theme={theme}
            />
          </div>

          {/* Render Time Chart */}
          <div
            className="chart-container"
            style={{
              backgroundColor: theme.colors.surface,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              padding: theme.spacing.md
            }}
          >
            <div
              className="chart-title"
              style={{
                fontSize: theme.typography.fontSize.sm,
                fontWeight: theme.typography.fontWeight.medium,
                color: theme.colors.text,
                marginBottom: theme.spacing.sm
              }}
            >
              Render Time History (ms)
            </div>
            <PerformanceBarChart
              data={chartData}
              maxValue={Math.max(...chartData.map(d => d.value), 50)}
              theme={theme}
            />
          </div>

          {/* Memory Usage Details */}
          {latestMetrics?.memoryUsage && (
            <div
              className="memory-details"
              style={{
                backgroundColor: theme.colors.surface,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius,
                padding: theme.spacing.md
              }}
            >
              <div
                className="memory-title"
                style={{
                  fontSize: theme.typography.fontSize.sm,
                  fontWeight: theme.typography.fontWeight.medium,
                  color: theme.colors.text,
                  marginBottom: theme.spacing.sm
                }}
              >
                Memory Usage Details
              </div>
              <div
                className="memory-info"
                style={{
                  fontSize: theme.typography.fontSize.xs,
                  color: theme.colors.textSecondary,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: theme.spacing.xs
                }}
              >
                <div>
                  Used: {(latestMetrics.memoryUsage.used / 1024 / 1024).toFixed(2)} MB
                </div>
                <div>
                  Total: {(latestMetrics.memoryUsage.total / 1024 / 1024).toFixed(2)} MB
                </div>
                <div>
                  Limit: {(latestMetrics.memoryUsage.limit / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PerformanceDashboard;