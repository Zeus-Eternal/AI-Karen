import React, { useState, useEffect, useCallback } from 'react';
import { ErrorReport, ErrorReportingProps } from './types';
import { generateId } from '@/lib/id-generator';

interface AuthContextLike {
  userId?: string;
}

interface PerformanceMemory {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

interface NetworkConnectionLike {
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
}

interface PluginLike {
  name: string;
  description: string;
  filename: string;
  version?: string;
}

interface NavigationTimingEntryLike {
  domContentLoadedEventEnd: number;
  loadEventEnd: number;
  redirectCount: number;
  transferSize: number;
  navigationStart?: number;
  startTime?: number;
}

interface SystemInfo {
  timestamp: string;
  memory?: PerformanceMemory;
  connection?: NetworkConnectionLike;
  plugins?: PluginLike[];
  performance?: {
    domContentLoaded: number;
    loadComplete: number;
    redirectCount: number;
    transferSize: number;
  };
}

const getPerformanceMemory = (): PerformanceMemory | undefined => {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return undefined;
  }

  return (performance as Performance & { memory?: PerformanceMemory }).memory;
};

const getNavigatorConnection = (): NetworkConnectionLike | undefined => {
  if (typeof navigator === 'undefined') {
    return undefined;
  }

  return (navigator as Navigator & { connection?: NetworkConnectionLike }).connection;
};

const getNavigationEntry = (): NavigationTimingEntryLike | undefined => {
  if (typeof performance === 'undefined' || !('getEntriesByType' in performance)) {
    return undefined;
  }

  const entries = performance.getEntriesByType('navigation') as PerformanceEntry[];
  return entries[0] as NavigationTimingEntryLike | undefined;
};

/**
 * Error Reporting Component for CoPilot Frontend
 * 
 * This component provides comprehensive error reporting functionality with:
 * - User feedback collection
 * - System information gathering
 * - Automatic report submission
 * - Report status tracking
 * - Debug information inclusion
 */
const ErrorReporting: React.FC<ErrorReportingProps> = ({
  error,
  onSubmit,
  onCancel,
  includeUserFeedback = true,
  includeSystemInfo = true,
  autoSubmit = false,
  className = ''
}) => {
  const [userFeedback, setUserFeedback] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reportStatus, setReportStatus] = useState<'pending' | 'submitted' | 'acknowledged' | 'resolved'>('pending');
  const [includeDebugInfo, setIncludeDebugInfo] = useState(false);
  const isClient = typeof window !== 'undefined';

  const getSystemInfo = useCallback((): SystemInfo => {
    if (!isClient) {
      return { timestamp: new Date().toISOString() };
    }

    const memory = getPerformanceMemory();
    const connection = getNavigatorConnection();
    const plugins = Array.from(navigator.plugins ?? []).map((plugin) => ({
      name: plugin.name,
      description: plugin.description,
      filename: plugin.filename,
      version: 'version' in plugin ? String(plugin.version) : 'Unknown'
    }));

    const info: SystemInfo = {
      timestamp: new Date().toISOString(),
      memory,
      connection,
      plugins: plugins.length > 0 ? plugins : undefined
    };

    const navigation = getNavigationEntry();
    if (navigation) {
      const startTime = navigation.navigationStart ?? navigation.startTime ?? 0;
      info.performance = {
        domContentLoaded: navigation.domContentLoadedEventEnd - startTime,
        loadComplete: navigation.loadEventEnd - startTime,
        redirectCount: navigation.redirectCount,
        transferSize: navigation.transferSize
      };
    }

    return info;
  }, [isClient]);

  const generateReportId = useCallback((): string => {
    return `report_${generateId('error')}`;
  }, []);

  const getUserId = useCallback((): string | undefined => {
    // Get user ID from auth context or local storage
    if (isClient && typeof window !== 'undefined') {
      const authContext = (window as Window & { authContext?: AuthContextLike }).authContext;
      return authContext?.userId || localStorage.getItem('userId') || undefined;
    }
    return undefined;
  }, [isClient]);

  const getSessionId = useCallback((): string | undefined => {
    // Get session ID from session storage
    if (isClient && typeof window !== 'undefined') {
      return sessionStorage.getItem('sessionId') || undefined;
    }
    return undefined;
  }, [isClient]);

  const handleSubmit = useCallback(async () => {
    if (!error) return;

    setIsSubmitting(true);

    const errorReport: ErrorReport = {
      id: generateReportId(),
      errorId: error.id,
      userId: getUserId(),
      sessionId: getSessionId(),
      component: error.component,
      operation: error.operation,
      errorInfo: error,
      userFeedback: includeUserFeedback ? userFeedback : undefined,
      userEmail: includeUserFeedback ? userEmail : undefined,
      timestamp: new Date().toISOString(),
      status: 'pending',
      metadata: {
        userAgent: isClient && typeof window !== 'undefined' ? window.navigator.userAgent : 'Unknown',
        url: isClient && typeof window !== 'undefined' ? window.location.href : 'Unknown',
        screenResolution: isClient && typeof window !== 'undefined' ? `${window.screen.width}x${window.screen.height}` : 'Unknown',
        timezone: isClient ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC',
        language: isClient && typeof window !== 'undefined' ? window.navigator.language : 'Unknown',
        includeDebugInfo,
        systemInfo: includeSystemInfo ? getSystemInfo() : undefined
      }
    };

    try {
      if (onSubmit) {
        await onSubmit(errorReport);
      } else {
        // Default submission
        await submitErrorReport(errorReport);
      }
      
      setReportStatus('submitted');
      
      // Simulate acknowledgement after delay
      setTimeout(() => {
        setReportStatus('acknowledged');
      }, 2000);
      
    } catch (submissionError) {
      console.error('Failed to submit error report:', submissionError);
      setReportStatus('pending');
    } finally {
      setIsSubmitting(false);
    }
  }, [error, generateReportId, getSessionId, getSystemInfo, getUserId, includeDebugInfo, includeSystemInfo, includeUserFeedback, isClient, onSubmit, userEmail, userFeedback]);

  useEffect(() => {
    // Auto-submit if enabled
    if (autoSubmit && error) {
      void handleSubmit();
    }
  }, [autoSubmit, error, handleSubmit]);

  const getStatusMessage = (): string => {
    switch (reportStatus) {
      case 'pending':
        return 'Ready to submit error report';
      case 'submitted':
        return 'Error report submitted successfully';
      case 'acknowledged':
        return 'Error report received and is being reviewed';
      case 'resolved':
        return 'Error has been resolved';
      default:
        return '';
    }
  };

  const getStatusColor = (): string => {
    switch (reportStatus) {
      case 'pending':
        return '#6b7280';
      case 'submitted':
        return '#28a745';
      case 'acknowledged':
        return '#17a2b8';
      case 'resolved':
        return '#10b981';
      default:
        return '#6c757d';
    }
  };

  if (!error) {
    return null;
  }

  return (
    <div className={`error-reporting ${className}`} style={{
      padding: '20px',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      backgroundColor: '#fff',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      maxWidth: '600px'
    }}>
      <h3 style={{
        margin: '0 0 16px 0',
        color: '#374151',
        fontSize: '18px',
        fontWeight: '600'
      }}>
        Report Error
      </h3>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          padding: '16px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fca5a5',
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          <h4 style={{
            margin: '0 0 8px 0',
            color: '#dc2626',
            fontSize: '16px'
          }}>
            {error.title}
          </h4>
          <p style={{
            margin: '0 0 12px 0',
            color: '#4b5563',
            lineHeight: '1.5'
          }}>
            {error.message}
          </p>
          
          {error.resolutionSteps && error.resolutionSteps.length > 0 && (
            <div>
              <h5 style={{
                margin: '0 0 8px 0',
                color: '#374151',
                fontSize: '14px'
              }}>
                What you can try:
              </h5>
              <ol style={{
                margin: '0',
                paddingLeft: '20px',
                color: '#6b7280'
              }}>
                {error.resolutionSteps.map((step, index) => (
                  <li key={index} style={{ marginBottom: '4px' }}>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {includeUserFeedback && (
          <div style={{ marginBottom: '16px' }}>
            <h5 style={{
              margin: '0 0 8px 0',
              color: '#374151',
              fontSize: '14px'
            }}>
              Additional Information (Optional)
            </h5>
            
            <div style={{ marginBottom: '12px' }}>
              <label style={{
                display: 'block',
                marginBottom: '4px',
                color: '#374151',
                fontSize: '12px',
                fontWeight: '500'
              }}>
                What were you trying to do?
              </label>
              <textarea
                value={userFeedback}
                onChange={(e) => setUserFeedback(e.target.value)}
                placeholder="Describe what you were trying to do when the error occurred..."
                style={{
                  width: '100%',
                  minHeight: '80px',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <label style={{
                display: 'block',
                marginBottom: '4px',
                color: '#374151',
                fontSize: '12px',
                fontWeight: '500'
              }}>
                Email (optional, for follow-up)
              </label>
              <input
                type="email"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                placeholder="your.email@example.com"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
          </div>
        )}

        <div style={{ marginBottom: '16px' }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            color: '#6b7280',
            fontSize: '12px'
          }}
          onClick={() => setIncludeDebugInfo(!includeDebugInfo)}
        >
            <input
              type="checkbox"
              checked={includeDebugInfo}
              onChange={(e) => setIncludeDebugInfo(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            Include technical information in report
          </label>
        </div>

        {includeDebugInfo && error.technicalDetails && (
          <details style={{ marginBottom: '16px' }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              Technical Details
            </summary>
            <div style={{
              padding: '12px',
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '4px'
            }}>
              <pre style={{
                margin: '0',
                fontSize: '11px',
                color: '#1f2937',
                whiteSpace: 'pre-wrap',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
                {error.technicalDetails}
              </pre>
              {error.stackTrace && (
                <div style={{ marginTop: '12px' }}>
                  <strong style={{ color: '#374151' }}>Stack Trace:</strong>
                  <pre style={{
                    margin: '4px 0 0 0',
                    fontSize: '10px',
                    color: '#4b5563',
                    whiteSpace: 'pre-wrap',
                    overflow: 'auto',
                    maxHeight: '150px'
                  }}>
                    {error.stackTrace}
                  </pre>
                </div>
              )}
            </div>
          </details>
        )}
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px'
      }}>
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: getStatusColor()
            }}
          />
          <span>{getStatusMessage()}</span>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || reportStatus !== 'pending'}
            style={{
              padding: '10px 20px',
              backgroundColor: isSubmitting ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Report'}
          </button>
          
          {onCancel && (
            <button
              onClick={onCancel}
              style={{
                padding: '10px 20px',
                backgroundColor: 'transparent',
                color: '#6b7280',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const submitErrorReport = async (report: ErrorReport): Promise<void> => {
  try {
    const response = await fetch('/api/error-reports', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(report)
    });

    if (!response.ok) {
      throw new Error(`Failed to submit error report: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Error report submitted successfully:', result);
    
  } catch (error) {
    console.error('Error submitting report:', error);
    throw error;
  }
};

export default ErrorReporting;
