/**
 * Accessibility Monitoring and Reporting System
 * Comprehensive accessibility monitoring and reporting for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';
import { WCAGComplianceReport } from './wcag-compliance';

// Monitoring event types
export type MonitoringEventType = 
  | 'violation_detected'
  | 'compliance_score_change'
  | 'preference_change'
  | 'user_interaction'
  | 'error_occurred'
  | 'test_completed'
  | 'accessibility_feature_used';

// Monitoring event interface
export interface MonitoringEvent {
  id: string;
  type: MonitoringEventType;
  timestamp: Date;
  data: MonitoringEventData;
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId?: string;
  sessionId: string;
  userAgent: string;
  url: string;
}

export interface MonitoringEventData {
  violationType?: string;
  score?: number;
  report?: WCAGComplianceReport;
  feature?: string;
  preference?: string;
  oldValue?: unknown;
  newValue?: unknown;
  message?: string;
  stack?: string;
  context?: string;
  type?: string;
  description?: string;
  impact?: string;
  wcagCriteria?: string[];
  action?: string;
  [key: string]: unknown;
}

// Monitoring metrics
export interface MonitoringMetrics {
  totalEvents: number;
  violationsByType: Record<string, number>;
  violationsBySeverity: Record<string, number>;
  complianceScoreHistory: Array<{ timestamp: Date; score: number }>;
  featureUsage: Record<string, number>;
  errorRate: number;
  averageResponseTime: number;
  userSatisfactionScore: number;
}

// Accessibility monitoring hook
export function useAccessibilityMonitoring() {
  const { state, addViolation, updateComplianceScore } = useAccessibility();
  const [events, setEvents] = useState<MonitoringEvent[]>([]);
  const [metrics, setMetrics] = useState<MonitoringMetrics>({
    totalEvents: 0,
    violationsByType: {},
    violationsBySeverity: {},
    complianceScoreHistory: [],
    featureUsage: {},
    errorRate: 0,
    averageResponseTime: 0,
    userSatisfactionScore: 0,
  });
  const [isMonitoring, setIsMonitoring] = useState(true);
  const sessionIdRef = useRef<string>(generateSessionId());

  // Generate session ID
  function generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Update metrics based on new event
  const updateMetrics = useCallback((event: MonitoringEvent) => {
    setMetrics(prev => {
      const newMetrics = { ...prev };
      
      // Update total events
      newMetrics.totalEvents++;
      
      // Update violations by type
      if (event.type === 'violation_detected') {
        const violationType = event.data.violationType || 'unknown';
        newMetrics.violationsByType[violationType] = (newMetrics.violationsByType[violationType] || 0) + 1;
        
        // Update violations by severity
        newMetrics.violationsBySeverity[event.severity] = (newMetrics.violationsBySeverity[event.severity] || 0) + 1;
      }
      
      // Update compliance score history
      if (event.type === 'compliance_score_change') {
        newMetrics.complianceScoreHistory.push({
          timestamp: event.timestamp,
          score: typeof event.data.score === 'number' ? event.data.score : 0,
        });
        
        // Keep only last 100 score updates
        if (newMetrics.complianceScoreHistory.length > 100) {
          newMetrics.complianceScoreHistory = newMetrics.complianceScoreHistory.slice(-100);
        }
      }
      
      // Update feature usage
      if (event.type === 'accessibility_feature_used') {
        const feature = event.data.feature || 'unknown';
        newMetrics.featureUsage[feature] = (newMetrics.featureUsage[feature] || 0) + 1;
      }

      // Calculate error rate using running totals
      const previousErrorCount = Math.round((prev.errorRate / 100) * prev.totalEvents);
      const newErrorCount = previousErrorCount + (event.type === 'error_occurred' ? 1 : 0);
      newMetrics.errorRate = newMetrics.totalEvents > 0
        ? (newErrorCount / newMetrics.totalEvents) * 100
        : 0;
      
      return newMetrics;
    });
  }, []);

  // Add monitoring event
  const addEvent = useCallback((event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'>) => {
    if (!isMonitoring) return;

    const fullEvent: MonitoringEvent = {
      ...event,
      id: `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      sessionId: sessionIdRef.current,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    setEvents(prev => [...prev.slice(-999), fullEvent]); // Keep last 1000 events
    updateMetrics(fullEvent);

    // Store events in localStorage for persistence
    try {
      const storedEvents = JSON.parse(localStorage.getItem('accessibility-events') || '[]');
      storedEvents.push(fullEvent);
      localStorage.setItem('accessibility-events', JSON.stringify(storedEvents.slice(-1000))); // Keep last 1000
    } catch (error) {
      console.error('Failed to store accessibility event:', error);
    }
  }, [isMonitoring, updateMetrics]);

  // Track accessibility violations
  const trackViolation = useCallback((violation: {
    type: string;
    description: string;
    impact: string;
    wcagCriteria: string[];
    element?: HTMLElement;
  }) => {
    const accessibilityViolation: Omit<import('../../contexts/AccessibilityContext').AccessibilityViolation, 'timestamp'> = {
      message: violation.description,
      priority: 'polite',
      type: violation.type,
      severity: violation.impact,
    };
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'violation_detected',
      data: violation,
      severity: violation.impact === 'critical' ? 'critical' : 
               violation.impact === 'serious' ? 'high' :
               violation.impact === 'moderate' ? 'medium' : 'low',
    };
    
    addEvent(event);
    addViolation(accessibilityViolation);
  }, [addEvent, addViolation]);

  // Track compliance score changes
  const trackComplianceScore = useCallback((score: number, report?: WCAGComplianceReport) => {
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'compliance_score_change',
      data: { score, report },
      severity: score >= 90 ? 'low' : score >= 70 ? 'medium' : 'high',
    };
    
    addEvent(event);
    updateComplianceScore(score);
  }, [addEvent, updateComplianceScore]);

  // Track preference changes
  const trackPreferenceChange = useCallback((preference: string, oldValue: unknown, newValue: unknown) => {
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'preference_change',
      data: { preference, oldValue, newValue },
      severity: 'low',
    };
    
    addEvent(event);
  }, [addEvent]);

  // Track user interactions
  const trackUserInteraction = useCallback((action: string, details: Record<string, unknown> = {}) => {
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'user_interaction',
      data: { action, ...details },
      severity: 'low',
    };
    
    addEvent(event);
  }, [addEvent]);

  // Track feature usage
  const trackFeatureUsage = useCallback((feature: string, details: Record<string, unknown> = {}) => {
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'accessibility_feature_used',
      data: { feature, ...details },
      severity: 'low',
    };
    
    addEvent(event);
  }, [addEvent]);

  // Track errors
  const trackError = useCallback((error: Error, context?: string) => {
    const event: Omit<MonitoringEvent, 'id' | 'timestamp' | 'sessionId' | 'userAgent' | 'url'> = {
      type: 'error_occurred',
      data: { 
        message: error.message,
        stack: error.stack,
        context,
      },
      severity: 'high',
    };
    
    addEvent(event);
  }, [addEvent]);

  // Generate monitoring report
  const generateReport = useCallback((timeRange?: { start: Date; end: Date }) => {
    const filteredEvents = timeRange 
      ? events.filter(e => e.timestamp >= timeRange.start && e.timestamp <= timeRange.end)
      : events;

    const violations = filteredEvents.filter(e => e.type === 'violation_detected');
    const preferenceChanges = filteredEvents.filter(e => e.type === 'preference_change');
    const featureUsage = filteredEvents.filter(e => e.type === 'accessibility_feature_used');
    const errors = filteredEvents.filter(e => e.type === 'error_occurred');

    return {
      summary: {
        totalEvents: filteredEvents.length,
        timeRange: timeRange || {
          start: events.length > 0 ? events[0]?.timestamp ?? new Date() : new Date(),
          end: new Date(),
        },
        violations: violations.length,
        preferenceChanges: preferenceChanges.length,
        featureUsage: featureUsage.length,
        errors: errors.length,
        complianceScore: state.complianceScore,
      },
      violations: violations.map(v => ({
        type: v.data.type,
        description: v.data.description,
        impact: v.data.impact,
        wcagCriteria: v.data.wcagCriteria,
        timestamp: v.timestamp,
        severity: v.severity,
      })),
      topViolations: Object.entries(
        violations.reduce((acc, v) => {
          const type = typeof v.data.type === 'string' && v.data.type ? v.data.type : 'unknown';
          acc[type] = (acc[type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      ).sort(([, a], [, b]) => b - a).slice(0, 10),
      featureUsage: featureUsage.map(f => ({
        feature: f.data.feature,
        count: 1,
        timestamp: f.timestamp,
      })),
      preferences: preferenceChanges.map(p => ({
        preference: p.data.preference,
        oldValue: p.data.oldValue,
        newValue: p.data.newValue,
        timestamp: p.timestamp,
      })),
      errors: errors.map(e => ({
        message: e.data.message,
        context: e.data.context,
        timestamp: e.timestamp,
      })),
      metrics: {
        ...metrics,
        averageViolationsPerDay: calculateAverageViolationsPerDay(violations),
        mostUsedFeatures: getMostUsedFeatures(featureUsage),
        errorRate: (errors.length / filteredEvents.length) * 100,
      },
    };
  }, [events, state.complianceScore, metrics]);

  // Calculate average violations per day
  const calculateAverageViolationsPerDay = (violations: MonitoringEvent[]): number => {
    if (violations.length === 0) return 0;
    
    const dates = violations.map(v => v.timestamp.toDateString());
    const uniqueDates = [...new Set(dates)];
    
    return violations.length / uniqueDates.length;
  };

  // Get most used features
  const getMostUsedFeatures = (featureUsage: MonitoringEvent[]): Array<{ feature: string; count: number }> => {
    const usage = featureUsage.reduce((acc, f) => {
      const feature = typeof f.data.feature === 'string' && f.data.feature ? f.data.feature : 'unknown';
      acc[feature] = (acc[feature] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return Object.entries(usage)
      .map(([feature, count]) => ({ feature, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  };

  // Export monitoring data
  const exportData = useCallback(() => {
    const data = {
      events,
      metrics,
      report: generateReport(),
      exportedAt: new Date().toISOString(),
      version: '1.0.0',
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accessibility-monitoring-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [events, metrics, generateReport]);

  // Clear monitoring data
  const clearData = useCallback(() => {
    setEvents([]);
    setMetrics({
      totalEvents: 0,
      violationsByType: {},
      violationsBySeverity: {},
      complianceScoreHistory: [],
      featureUsage: {},
      errorRate: 0,
      averageResponseTime: 0,
      userSatisfactionScore: 0,
    });
    
    try {
      localStorage.removeItem('accessibility-events');
    } catch (error) {
      console.error('Failed to clear accessibility events:', error);
    }
  }, []);

  // Load stored events on mount
  useEffect(() => {
    try {
      const storedEvents = JSON.parse(localStorage.getItem('accessibility-events') || '[]');
      setEvents(storedEvents);
    } catch (error) {
      console.error('Failed to load accessibility events:', error);
    }
  }, []);

  // Auto-generate daily reports
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      const now = new Date();
      const lastReport = localStorage.getItem('last-daily-report');
      
      if (!lastReport || new Date(lastReport).toDateString() !== now.toDateString()) {
        const report = generateReport({
          start: new Date(now.getTime() - 24 * 60 * 60 * 1000), // 24 hours ago
          end: now,
        });
        
        console.log('Daily accessibility report:', report);
        localStorage.setItem('last-daily-report', now.toISOString());
        
        // Here you could send the report to a monitoring service
        // sendReportToService(report);
      }
    }, 60 * 60 * 1000); // Check every hour

    return () => clearInterval(interval);
  }, [isMonitoring, generateReport]);

  return {
    events,
    metrics,
    isMonitoring,
    trackViolation,
    trackComplianceScore,
    trackPreferenceChange,
    trackUserInteraction,
    trackFeatureUsage,
    trackError,
    generateReport,
    exportData,
    clearData,
    setIsMonitoring,
  };
}

// Accessibility monitoring dashboard component
export interface AccessibilityMonitoringDashboardProps {
  className?: string;
}

export function AccessibilityMonitoringDashboard({ className = '' }: AccessibilityMonitoringDashboardProps) {
  const {
    events,
    isMonitoring,
    generateReport,
    exportData,
    clearData,
    setIsMonitoring,
  } = useAccessibilityMonitoring();

  const [showDetails, setShowDetails] = useState(false);
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month' | 'all'>('day');

  const report = generateReport(getTimeRangeFilter());

  function getTimeRangeFilter() {
    const now = new Date();
    switch (timeRange) {
      case 'day':
        return { start: new Date(now.getTime() - 24 * 60 * 60 * 1000), end: now };
      case 'week':
        return { start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000), end: now };
      case 'month':
        return { start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000), end: now };
      default:
        return undefined;
    }
  }

  return React.createElement('div', {
    className: `accessibility-monitoring-dashboard ${className}`,
    role: 'region',
    'aria-label': 'Accessibility monitoring dashboard',
  }, [
    // Header
    React.createElement('div', { key: 'header', className: 'monitoring-header' }, [
      React.createElement('h2', null, 'Accessibility Monitoring'),
      
      // Monitoring toggle
      React.createElement('div', { className: 'monitoring-toggle' }, [
        React.createElement('label', null, [
          React.createElement('input', {
            type: 'checkbox',
            checked: isMonitoring,
            onChange: (e: React.ChangeEvent<HTMLInputElement>) => setIsMonitoring(e.target.checked),
          }),
          React.createElement('span', null, 'Enable Monitoring'),
        ]),
        
        React.createElement('span', {
          className: `status-indicator ${isMonitoring ? 'active' : 'inactive'}`,
          'aria-label': isMonitoring ? 'Monitoring is active' : 'Monitoring is inactive',
        }),
      ]),
    ]),
    
    // Summary stats
    React.createElement('div', { key: 'summary', className: 'monitoring-summary' }, [
      React.createElement('div', { className: 'summary-item' },
        React.createElement('span', { className: 'summary-label' }, 'Total Events: '),
        React.createElement('span', { className: 'summary-value' }, report.summary.totalEvents)
      ),
      React.createElement('div', { className: 'summary-item' },
        React.createElement('span', { className: 'summary-label' }, 'Violations: '),
        React.createElement('span', { className: 'summary-value violations' }, report.summary.violations)
      ),
      React.createElement('div', { className: 'summary-item' },
        React.createElement('span', { className: 'summary-label' }, 'Compliance Score: '),
        React.createElement('span', { className: 'summary-value score' }, `${report.summary.complianceScore}%`)
      ),
      React.createElement('div', { className: 'summary-item' },
        React.createElement('span', { className: 'summary-label' }, 'Error Rate: '),
        React.createElement('span', { className: 'summary-value' }, `${report.metrics.errorRate.toFixed(2)}%`)
      ),
    ]),
    
    // Controls
    React.createElement('div', { key: 'controls', className: 'monitoring-controls' }, [
      React.createElement('div', { className: 'time-range-selector' },
        React.createElement('label', { htmlFor: 'time-range' }, 'Time Range:'),
        React.createElement('select', {
          id: 'time-range',
          value: timeRange,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => {
            const nextValue = e.target.value;
            if (nextValue === 'day' || nextValue === 'week' || nextValue === 'month' || nextValue === 'all') {
              setTimeRange(nextValue);
            }
          },
        }, [
          React.createElement('option', { key: 'day', value: 'day' }, 'Last 24 Hours'),
          React.createElement('option', { key: 'week', value: 'week' }, 'Last Week'),
          React.createElement('option', { key: 'month', value: 'month' }, 'Last Month'),
          React.createElement('option', { key: 'all', value: 'all' }, 'All Time'),
        ])
      ),
      
      React.createElement('button', {
        onClick: () => setShowDetails(!showDetails),
        className: 'control-button',
        'aria-expanded': showDetails,
      }, showDetails ? 'Hide Details' : 'Show Details'),
      
      React.createElement('button', {
        onClick: exportData,
        className: 'control-button export',
      }, 'Export Data'),
      
      React.createElement('button', {
        onClick: clearData,
        className: 'control-button clear',
      }, 'Clear Data'),
    ]),
    
    // Detailed information
    showDetails && React.createElement('div', { key: 'details', className: 'monitoring-details' }, [
      // Top violations
      React.createElement('div', { className: 'detail-section' }, [
        React.createElement('h3', null, 'Top Violations'),
        React.createElement('ul', { className: 'violations-list' },
          report.topViolations.slice(0, 5).map(([type, count], index) =>
            React.createElement('li', { key: index }, [
              React.createElement('span', { className: 'violation-type' }, type),
              React.createElement('span', { className: 'violation-count' }, count),
            ])
          )
        ),
      ]),
      
      // Feature usage
      React.createElement('div', { className: 'detail-section' }, [
        React.createElement('h3', null, 'Feature Usage'),
        React.createElement('ul', { className: 'feature-usage-list' },
          report.metrics.mostUsedFeatures.slice(0, 5).map((feature, index) =>
            React.createElement('li', { key: index }, [
              React.createElement('span', { className: 'feature-name' }, feature.feature),
              React.createElement('span', { className: 'feature-count' }, feature.count),
            ])
          )
        ),
      ]),
      
      // Recent events
      React.createElement('div', { className: 'detail-section' }, [
        React.createElement('h3', null, 'Recent Events'),
        React.createElement('ul', { className: 'events-list' },
          events.slice(-10).reverse().map(event =>
            React.createElement('li', {
              key: event.id,
              className: `event-item ${event.type} ${event.severity}`,
            }, [
              React.createElement('span', { className: 'event-time' },
                event.timestamp.toLocaleTimeString()
              ),
              React.createElement('span', { className: 'event-type' }, event.type),
              React.createElement('span', { className: 'event-description' },
                event.data.description || event.data.message || event.type
              ),
            ])
          )
        ),
      ]),
    ]),
  ]);
}
