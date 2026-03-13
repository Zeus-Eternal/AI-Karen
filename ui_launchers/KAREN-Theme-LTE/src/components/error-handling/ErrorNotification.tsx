import React, { useState, useEffect } from 'react';
import { NotificationAction, ErrorNotificationProps } from './types';

/**
 * Error Notification Component for CoPilot Frontend
 * 
 * This component provides comprehensive error notification display with:
 * - Multiple notification types (info, warning, error, success)
 * - Auto-hide functionality
 * - Action buttons
 * - Positioning options
 * - Persistent notifications
 */
const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  notification,
  onClose,
  onAction,
  autoHide = 8000,
  position = 'top-right',
  variant = 'default',
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (autoHide && notification.type !== 'error' && notification.type !== 'critical') {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose(notification.id);
      }, autoHide);

      return () => clearTimeout(timer);
    }
    return undefined;
  }, [autoHide, notification.type, onClose, notification.id]);

  const getTypeStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '12px 16px',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      maxWidth: '400px',
      position: 'relative' as const,
      transition: 'all 0.3s ease'
    };

    switch (variant) {
      case 'success':
        return {
          ...baseStyles,
          backgroundColor: '#10b981',
          color: 'white',
          border: '1px solid #059669'
        };
      case 'warning':
        return {
          ...baseStyles,
          backgroundColor: '#f59e0b',
          color: 'white',
          border: '1px solid #d97706'
        };
      case 'error':
        return {
          ...baseStyles,
          backgroundColor: '#ef4444',
          color: 'white',
          border: '1px solid #dc2626'
        };
      case 'info':
      default:
        return {
          ...baseStyles,
          backgroundColor: '#3b82f6',
          color: 'white',
          border: '1px solid #2563eb'
        };
    }
  };

  const getPositionStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed' as const,
      zIndex: 9999,
      transition: 'all 0.3s ease'
    };

    switch (position) {
      case 'top-right':
        return {
          ...baseStyles,
          top: '20px',
          right: '20px'
        };
      case 'top-left':
        return {
          ...baseStyles,
          top: '20px',
          left: '20px'
        };
      case 'bottom-right':
        return {
          ...baseStyles,
          bottom: '20px',
          right: '20px'
        };
      case 'bottom-left':
        return {
          ...baseStyles,
          bottom: '20px',
          left: '20px'
        };
      case 'top-center':
        return {
          ...baseStyles,
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)'
        };
      case 'bottom-center':
        return {
          ...baseStyles,
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)'
        };
      default:
        return {
          ...baseStyles,
          top: '20px',
          right: '20px'
        };
    }
  };

  const getTypeIcon = (): string => {
    const iconMap: Record<string, string> = {
      'info': 'ℹ️',
      'warning': '⚠️',
      'error': '❌',
      'critical': '🚨',
      'fatal': '💀',
      'success': '✅'
    };
    return iconMap[notification.type as string] || 'ℹ️';
  };

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) onClose(notification.id);
  };

  const handleAction = (action: NotificationAction) => {
    if (onAction) onAction(action);
    if (action.action) {
      action.action();
    }
  };

  const renderActions = (): React.ReactNode => {
    if (!notification.actions || notification.actions.length === 0) {
      return null;
    }

    return (
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginTop: '12px',
        flexWrap: 'wrap' 
      }}>
        {notification.actions.map((action, index) => (
          <button
            key={action.id || index}
            onClick={() => handleAction(action)}
            style={{
              padding: '6px 12px',
              backgroundColor: action.primary ? '#ffffff' : 'transparent',
              color: action.primary ? '#3b82f6' : '#ffffff',
              border: action.primary ? '1px solid #3b82f6' : '1px solid #ffffff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = action.primary ? '#2563eb' : 'rgba(255, 255, 255, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = action.primary ? '#ffffff' : 'transparent';
            }}
          >
            {action.label}
          </button>
        ))}
      </div>
    );
  };

  const renderProgressBar = (): React.ReactNode => {
    if (!notification.metadata || !notification.metadata.progress) {
      return null;
    }

    const progress = notification.metadata.progress;
    const percentage = progress.percentage || 0;

    return (
      <div style={{ marginTop: '12px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '4px',
          fontSize: '12px'
        }}>
          <span>{progress.label || 'Progress'}</span>
          <span>{Math.round(percentage)}%</span>
        </div>
        <div style={{
          width: '100%',
          height: '4px',
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: '#3b82f6',
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>
    );
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div 
      className={`error-notification ${className}`}
      style={{
        ...getPositionStyles(),
        opacity: isHovered ? 1 : 0.9,
        transform: isHovered ? 'scale(1.02)' : 'scale(1)'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div style={getTypeStyles()}>
        <span style={{ fontSize: '18px', marginRight: '8px' }}>
          {getTypeIcon()}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            {notification.title}
          </div>
          <div style={{ fontSize: '14px', lineHeight: '1.4' }}>
            {notification.message}
          </div>
          
          {renderActions()}
          {renderProgressBar()}
          
          {notification.timestamp && (
            <div style={{
              fontSize: '11px',
              color: 'rgba(255, 255, 255, 0.7)',
              marginTop: '8px'
            }}>
              {new Date(notification.timestamp).toLocaleString('en-US', {
                timeZone: 'UTC'
              })}
            </div>
          )}
        </div>
        
        <button
          onClick={handleClose}
          style={{
            position: 'absolute' as const,
            top: '8px',
            right: '8px',
            background: 'none',
            border: 'none',
            fontSize: '16px',
            cursor: 'pointer',
            color: 'rgba(255, 255, 255, 0.7)',
            padding: '4px',
            borderRadius: '50%',
            lineHeight: '1'
          }}
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;
