import React, { useState, useEffect } from 'react';
import { ErrorDisplayProps } from './types';

/**
 * Error Display Component for CoPilot Frontend
 * 
 * This component provides user-friendly error display with:
 * - Different display variants (modal, toast, inline)
 * - Technical details toggle
 * - Retry and recovery actions
 * - Error reporting
 * - Stack trace display
 */
const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onClose,
  onRetry,
  onReport,
  showDetails = false,
  showStackTrace = false,
  compact = false,
  variant = 'default',
  className = ''
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [isReporting, setIsReporting] = useState(false);

  useEffect(() => {
    // Auto-hide notification after delay for non-critical errors
    if (error.severity !== 'critical' && error.severity !== 'fatal') {
      const timer = setTimeout(() => {
        if (onClose) onClose();
      }, 8000); // 8 seconds

      return () => clearTimeout(timer);
    }
    return undefined;
  }, [error.severity, onClose]);

  const getSeverityColor = (severity: string): string => {
    const colorMap = {
      'low': '#3b82f6',      // Blue
      'medium': '#f59e0b',   // Orange
      'high': '#ef4444',     // Red
      'critical': '#dc2626',  // Dark red
      'fatal': '#991b1b'      // Darker red
    };
    return colorMap[severity as keyof typeof colorMap] || '#6c757d';
  };

  const getSeverityIcon = (severity: string): string => {
    const iconMap = {
      'low': 'ℹ️',
      'medium': '⚠️',
      'high': '❌',
      'critical': '🚨',
      'fatal': '💀'
    };
    return iconMap[severity as keyof typeof iconMap] || '❌';
  };

  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'modal':
        return {
          position: 'fixed',
          top: '0',
          left: '0',
          right: '0',
          bottom: '0',
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        };
      case 'toast':
        return {
          position: 'fixed',
          top: '20px',
          right: '20px',
          backgroundColor: '#fff',
          border: `1px solid ${getSeverityColor(error.severity)}`,
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 9999,
          maxWidth: '400px'
        };
      case 'inline':
        return {
          border: `1px solid ${getSeverityColor(error.severity)}`,
          borderRadius: '6px',
          padding: '12px',
          margin: '10px 0',
          backgroundColor: '#fef2f2'
        };
      default:
        return {
          border: `1px solid ${getSeverityColor(error.severity)}`,
          borderRadius: '8px',
          padding: '16px',
          margin: '20px 0',
          backgroundColor: '#fff',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        };
    }
  };

  const handleRetry = async () => {
    if (onRetry) {
      await onRetry();
    }
  };

  const handleReport = async () => {
    if (onReport) {
      setIsReporting(true);
      try {
        await onReport();
      } finally {
        setIsReporting(false);
      }
    }
  };

  const renderErrorContent = (): React.ReactNode => {
    if (compact) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: getSeverityColor(error.severity) }}>
            {getSeverityIcon(error.severity)}
          </span>
          <span>{error.title}</span>
        </div>
      );
    }

    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
          <span style={{ 
            fontSize: '24px', 
            marginRight: '12px',
            color: getSeverityColor(error.severity)
          }}>
            {getSeverityIcon(error.severity)}
          </span>
          <h3 style={{ 
            margin: 0, 
            color: getSeverityColor(error.severity),
            fontSize: '18px'
          }}>
            {error.title}
          </h3>
        </div>
        
        <p style={{ 
          margin: '0 0 12px 0', 
          lineHeight: '1.5',
          color: '#4b5563'
        }}>
          {error.message}
        </p>

        {error.resolutionSteps && error.resolutionSteps.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ 
              margin: '0 0 8px 0', 
              color: '#374151',
              fontSize: '16px'
            }}>
              What you can do:
            </h4>
            <ol style={{ 
              margin: 0, 
              paddingLeft: '20px',
              color: '#6b7280'
            }}>
              {error.resolutionSteps.map((step, index) => (
                <li key={index} style={{ marginBottom: '6px' }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
          {error.retryPossible && (
            <button
              onClick={handleRetry}
              style={{
                padding: '10px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Try Again
            </button>
          )}

          <button
            onClick={handleReport}
            disabled={isReporting}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: isReporting ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              opacity: isReporting ? 0.6 : 1
            }}
          >
            {isReporting ? 'Reporting...' : 'Report Issue'}
          </button>

          {onClose && (
            <button
              onClick={onClose}
              style={{
                padding: '10px 20px',
                backgroundColor: 'transparent',
                color: '#6b7280',
                border: '1px solid #6b7280',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Dismiss
            </button>
          )}
        </div>

        {(showDetails || showStackTrace) && (
          <div style={{ marginTop: '20px' }}>
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              style={{
                padding: '8px 16px',
                backgroundColor: 'transparent',
                color: '#6b7280',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {showTechnicalDetails ? 'Hide' : 'Show'} Technical Details
            </button>
          </div>
        )}

        {showTechnicalDetails && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: '6px'
          }}>
            {error.technicalDetails && (
              <div style={{ marginBottom: '12px' }}>
                <h5 style={{ margin: '0 0 8px 0', color: '#374151' }}>
                  Technical Details:
                </h5>
                <pre style={{
                  backgroundColor: '#1f2937',
                  color: '#f9fafb',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap'
                }}>
                  {error.technicalDetails}
                </pre>
              </div>
            )}

            {showStackTrace && error.stackTrace && (
              <div>
                <h5 style={{ margin: '0 0 8px 0', color: '#374151' }}>
                  Stack Trace:
                </h5>
                <pre style={{
                  backgroundColor: '#1f2937',
                  color: '#f9fafb',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '10px',
                  maxHeight: '200px'
                }}>
                  {error.stackTrace}
                </pre>
              </div>
            )}

            {error.context && Object.keys(error.context).length > 0 && (
              <div>
                <h5 style={{ margin: '0 0 8px 0', color: '#374151' }}>
                  Context Information:
                </h5>
                <div style={{ backgroundColor: '#f3f4f6', padding: '12px', borderRadius: '4px' }}>
                  {Object.entries(error.context).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '8px' }}>
                      <strong style={{ color: '#374151' }}>{key}:</strong>
                      <span style={{ marginLeft: '8px', color: '#6b7280' }}>
                        {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderCloseButton = (): React.ReactNode => {
    if (variant === 'toast') {
      return (
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'none',
            border: 'none',
            fontSize: '18px',
            cursor: 'pointer',
            color: '#6b7280'
          }}
        >
          ×
        </button>
      );
    }
    return null;
  };

  if (variant === 'modal') {
    return (
      <div style={getVariantStyles()}>
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '500px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
          position: 'relative'
        }}>
          {renderCloseButton()}
          {renderErrorContent()}
        </div>
      </div>
    );
  }

  if (variant === 'toast') {
    return (
      <div style={getVariantStyles()}>
        <div style={{ padding: '16px' }}>
          {renderCloseButton()}
          {renderErrorContent()}
        </div>
      </div>
    );
  }

  return (
    <div className={`error-display ${className}`} style={getVariantStyles()}>
      {renderErrorContent()}
    </div>
  );
};

export default ErrorDisplay;
