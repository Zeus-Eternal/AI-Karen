import React from 'react';
import ErrorHandlingService from '../services/ErrorHandlingService';
import ErrorLoggingService from '../services/ErrorLoggingService';
import UserErrorMessageService from '../services/UserErrorMessageService';
import ErrorNotificationService from '../services/ErrorNotificationService';
import { ErrorInfo, ErrorCategory, ErrorSeverity } from '../services/ErrorHandlingService';
import { LogEntry, LogLevel, LogCategory, ErrorMetrics, PerformanceMetrics } from '../services/ErrorLoggingService';
import { NotificationData, NotificationType, NotificationPosition, NotificationTheme } from '../services/ErrorNotificationService';

/**
 * Error monitoring dashboard props
 */
export interface ErrorMonitoringDashboardProps {
  /** Whether dashboard is visible */
  visible?: boolean;
  
  /** Dashboard title */
  title?: string;
  
  /** Whether to show refresh button */
  showRefreshButton?: boolean;
  
  /** Whether to show clear button */
  showClearButton?: boolean;
  
  /** Whether to show export button */
  showExportButton?: boolean;
  
  /** Callback function to call when dashboard is closed */
  onClose?: () => void;
  
  /** Custom CSS class */
  className?: string;
}

/**
 * Error monitoring dashboard state
 */
export interface ErrorMonitoringDashboardState {
  /** Active tab */
  activeTab: 'errors' | 'logs' | 'notifications' | 'metrics';
  
  /** Error filter */
  errorFilter: {
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    resolved?: boolean;
    search?: string;
  };
  
  /** Log filter */
  logFilter: {
    level?: LogLevel;
    category?: LogCategory;
    component?: string;
    search?: string;
  };
  
  /** Notification filter */
  notificationFilter: {
    type?: NotificationType;
    severity?: ErrorSeverity;
    search?: string;
  };
  
  /** Selected error */
  selectedError: ErrorInfo | null;
  
  /** Selected log */
  selectedLog: LogEntry | null;
  
  /** Selected notification */
  selectedNotification: NotificationData | null;
  
  /** Loading state */
  loading: boolean;
}

/**
 * Error monitoring dashboard component
 */
export class ErrorMonitoringDashboard extends React.Component<ErrorMonitoringDashboardProps, ErrorMonitoringDashboardState> {
  private errorHandlingService: ErrorHandlingService;
  private errorLoggingService: ErrorLoggingService;
  private userErrorMessageService: UserErrorMessageService;
  private errorNotificationService: ErrorNotificationService;
  
  constructor(props: ErrorMonitoringDashboardProps) {
    super(props);
    
    this.state = {
      activeTab: 'errors',
      errorFilter: {},
      logFilter: {},
      notificationFilter: {},
      selectedError: null,
      selectedLog: null,
      selectedNotification: null,
      loading: false
    };
    
    this.errorHandlingService = ErrorHandlingService.getInstance();
    this.errorLoggingService = ErrorLoggingService.getInstance();
    this.userErrorMessageService = UserErrorMessageService.getInstance();
    this.errorNotificationService = ErrorNotificationService.getInstance();
  }
  
  /**
   * Refresh dashboard data
   */
  private refreshData = async (): Promise<void> => {
    this.setState({ loading: true });
    
    try {
      // Simulate API call to refresh data
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.MEDIUM,
        { component: 'ErrorMonitoringDashboard', function: 'refreshData' },
        undefined,
        { showNotification: true, message: 'Failed to refresh dashboard data' }
      );
    } finally {
      this.setState({ loading: false });
    }
  };
  
  /**
   * Clear all data
   */
  private clearAllData = (): void => {
    if (window.confirm('Are you sure you want to clear all error data?')) {
      this.errorHandlingService.clearAllErrors();
      this.errorLoggingService.clearLogs();
      this.errorLoggingService.clearAnalyticsEvents();
      this.errorNotificationService.removeAllNotifications();
      
      this.setState({
        selectedError: null,
        selectedLog: null,
        selectedNotification: null
      });
    }
  };
  
  /**
   * Export data
   */
  private exportData = (): void => {
    try {
      const errors = this.errorHandlingService.getAllErrors(true);
      const logs = this.errorLoggingService.getLogs();
      const analytics = this.errorLoggingService.getAnalyticsEvents();
      
      const data = {
        errors,
        logs,
        analytics,
        exportedAt: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `error-monitoring-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.MEDIUM,
        { component: 'ErrorMonitoringDashboard', function: 'exportData' },
        undefined,
        { showNotification: true, message: 'Failed to export data' }
      );
    }
  };
  
  /**
   * Handle error filter change
   */
  private handleErrorFilterChange = (filter: Partial<ErrorMonitoringDashboardState['errorFilter']>): void => {
    this.setState({
      errorFilter: { ...this.state.errorFilter, ...filter }
    });
  };
  
  /**
   * Handle log filter change
   */
  private handleLogFilterChange = (filter: Partial<ErrorMonitoringDashboardState['logFilter']>): void => {
    this.setState({
      logFilter: { ...this.state.logFilter, ...filter }
    });
  };
  
  /**
   * Handle notification filter change
   */
  private handleNotificationFilterChange = (filter: Partial<ErrorMonitoringDashboardState['notificationFilter']>): void => {
    this.setState({
      notificationFilter: { ...this.state.notificationFilter, ...filter }
    });
  };
  
  /**
   * Handle error selection
   */
  private handleErrorSelect = (error: ErrorInfo): void => {
    this.setState({ selectedError: error });
  };
  
  /**
   * Handle log selection
   */
  private handleLogSelect = (log: LogEntry): void => {
    this.setState({ selectedLog: log });
  };
  
  /**
   * Handle notification selection
   */
  private handleNotificationSelect = (notification: NotificationData): void => {
    this.setState({ selectedNotification: notification });
  };
  
  /**
   * Resolve error
   */
  private resolveError = (errorId: string): void => {
    this.errorHandlingService.resolveError(errorId);
    
    // Clear selection if resolved error is selected
    if (this.state.selectedError?.id === errorId) {
      this.setState({ selectedError: null });
    }
  };
  
  /**
   * Close notification
   */
  private closeNotification = (notificationId: string): void => {
    this.errorNotificationService.closeNotification(notificationId);
    
    // Clear selection if closed notification is selected
    if (this.state.selectedNotification?.id === notificationId) {
      this.setState({ selectedNotification: null });
    }
  };
  
  /**
   * Get filtered errors
   */
  private getFilteredErrors = (): ErrorInfo[] => {
    let errors = this.errorHandlingService.getAllErrors();
    
    const { category, severity, resolved, search } = this.state.errorFilter;
    
    if (category) {
      errors = errors.filter(error => error.category === category);
    }
    
    if (severity) {
      errors = errors.filter(error => error.severity === severity);
    }
    
    if (resolved !== undefined) {
      errors = errors.filter(error => error.resolved === resolved);
    }
    
    if (search) {
      const searchLower = search.toLowerCase();
      errors = errors.filter(error => 
        error.message.toLowerCase().includes(searchLower) ||
        error.code.toLowerCase().includes(searchLower) ||
        (error.context?.component && error.context.component.toLowerCase().includes(searchLower))
      );
    }
    
    return errors;
  };
  
  /**
   * Get filtered logs
   */
  private getFilteredLogs = (): LogEntry[] => {
    let logs = this.errorLoggingService.getLogs();
    
    const { level, category, component, search } = this.state.logFilter;
    
    if (level) {
      logs = logs.filter(log => log.level === level);
    }
    
    if (category) {
      logs = logs.filter(log => log.category === category);
    }
    
    if (component) {
      logs = logs.filter(log => log.component === component);
    }
    
    if (search) {
      const searchLower = search.toLowerCase();
      logs = logs.filter(log => 
        log.message.toLowerCase().includes(searchLower) ||
        (log.component && log.component.toLowerCase().includes(searchLower))
      );
    }
    
    return logs;
  };
  
  /**
   * Get filtered notifications
   */
  private getFilteredNotifications = (): NotificationData[] => {
    let notifications = this.errorNotificationService.getAllNotifications();
    
    const { type, severity, search } = this.state.notificationFilter;
    
    if (type) {
      notifications = notifications.filter(notification => notification.type === type);
    }
    
    if (severity) {
      notifications = notifications.filter(notification => notification.severity === severity);
    }
    
    if (search) {
      const searchLower = search.toLowerCase();
      notifications = notifications.filter(notification => 
        notification.title.toLowerCase().includes(searchLower) ||
        notification.message.toLowerCase().includes(searchLower)
      );
    }
    
    return notifications;
  };
  
  /**
   * Get error statistics
   */
  private getErrorStatistics = () => {
    return this.errorHandlingService.getErrorStatistics();
  };
  
  /**
   * Get error metrics
   */
  private getErrorMetrics = (): ErrorMetrics => {
    return this.errorLoggingService.getErrorMetrics();
  };
  
  /**
   * Get performance metrics
   */
  private getPerformanceMetrics = (): PerformanceMetrics => {
    return this.errorLoggingService.getPerformanceMetrics();
  };
  
  render(): JSX.Element | null {
    const { visible = true, title = 'Error Monitoring Dashboard', showRefreshButton = true, showClearButton = true, showExportButton = true, onClose, className } = this.props;
    const { activeTab, errorFilter, logFilter, notificationFilter, selectedError, selectedLog, selectedNotification, loading } = this.state;
    
    if (!visible) {
      return null;
    }
    
    const filteredErrors = this.getFilteredErrors();
    const filteredLogs = this.getFilteredLogs();
    const filteredNotifications = this.getFilteredNotifications();
    const errorStats = this.getErrorStatistics();
    const errorMetrics = this.getErrorMetrics();
    const performanceMetrics = this.getPerformanceMetrics();
    
    return (
      <div className={`error-monitoring-dashboard ${className || ''}`}>
        <div className="error-monitoring-header">
          <h2 className="error-monitoring-title">{title}</h2>
          <div className="error-monitoring-actions">
            {showRefreshButton && (
              <button 
                className="error-monitoring-button"
                onClick={this.refreshData}
                disabled={loading}
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            )}
            {showClearButton && (
              <button 
                className="error-monitoring-button"
                onClick={this.clearAllData}
              >
                Clear All
              </button>
            )}
            {showExportButton && (
              <button 
                className="error-monitoring-button"
                onClick={this.exportData}
              >
                Export
              </button>
            )}
            {onClose && (
              <button 
                className="error-monitoring-button error-monitoring-close"
                onClick={onClose}
              >
                Close
              </button>
            )}
          </div>
        </div>
        
        <div className="error-monitoring-tabs">
          <button 
            className={`error-monitoring-tab ${activeTab === 'errors' ? 'active' : ''}`}
            onClick={() => this.setState({ activeTab: 'errors' })}
          >
            Errors ({filteredErrors.length})
          </button>
          <button 
            className={`error-monitoring-tab ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => this.setState({ activeTab: 'logs' })}
          >
            Logs ({filteredLogs.length})
          </button>
          <button 
            className={`error-monitoring-tab ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => this.setState({ activeTab: 'notifications' })}
          >
            Notifications ({filteredNotifications.length})
          </button>
          <button 
            className={`error-monitoring-tab ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => this.setState({ activeTab: 'metrics' })}
          >
            Metrics
          </button>
        </div>
        
        <div className="error-monitoring-content">
          {activeTab === 'errors' && (
            <div className="error-monitoring-tab-content">
              <div className="error-monitoring-filters">
                <select 
                  value={errorFilter.category || ''}
                  onChange={(e) => this.handleErrorFilterChange({ 
                    category: e.target.value as ErrorCategory || undefined 
                  })}
                >
                  <option value="">All Categories</option>
                  {Object.values(ErrorCategory).map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
                
                <select 
                  value={errorFilter.severity || ''}
                  onChange={(e) => this.handleErrorFilterChange({ 
                    severity: e.target.value as ErrorSeverity || undefined 
                  })}
                >
                  <option value="">All Severities</option>
                  {Object.values(ErrorSeverity).map(severity => (
                    <option key={severity} value={severity}>{severity}</option>
                  ))}
                </select>
                
                <select 
                  value={errorFilter.resolved === undefined ? '' : errorFilter.resolved ? 'true' : 'false'}
                  onChange={(e) => this.handleErrorFilterChange({ 
                    resolved: e.target.value === '' ? undefined : e.target.value === 'true' 
                  })}
                >
                  <option value="">All Statuses</option>
                  <option value="false">Unresolved</option>
                  <option value="true">Resolved</option>
                </select>
                
                <input 
                  type="text" 
                  placeholder="Search errors..." 
                  value={errorFilter.search || ''}
                  onChange={(e) => this.handleErrorFilterChange({ 
                    search: e.target.value 
                  })}
                />
              </div>
              
              <div className="error-monitoring-list">
                {filteredErrors.length === 0 ? (
                  <div className="error-monitoring-empty">No errors found</div>
                ) : (
                  filteredErrors.map(error => (
                    <div 
                      key={error.id} 
                      className={`error-monitoring-item ${selectedError?.id === error.id ? 'selected' : ''} ${error.resolved ? 'resolved' : ''}`}
                      onClick={() => this.handleErrorSelect(error)}
                    >
                      <div className="error-monitoring-item-header">
                        <span className="error-monitoring-item-code">{error.code}</span>
                        <span className={`error-monitoring-item-severity error-severity-${error.severity}`}>{error.severity}</span>
                        <span className={`error-monitoring-item-category error-category-${error.category}`}>{error.category}</span>
                        <span className="error-monitoring-item-time">
                          {error.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <div className="error-monitoring-item-message">{error.message}</div>
                      <div className="error-monitoring-item-actions">
                        {!error.resolved && (
                          <button 
                            className="error-monitoring-item-button"
                            onClick={(e) => {
                              e.stopPropagation();
                              this.resolveError(error.id);
                            }}
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'logs' && (
            <div className="error-monitoring-tab-content">
              <div className="error-monitoring-filters">
                <select 
                  value={logFilter.level || ''}
                  onChange={(e) => this.handleLogFilterChange({ 
                    level: e.target.value as LogLevel || undefined 
                  })}
                >
                  <option value="">All Levels</option>
                  {Object.values(LogLevel).map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
                
                <select 
                  value={logFilter.category || ''}
                  onChange={(e) => this.handleLogFilterChange({ 
                    category: e.target.value as LogCategory || undefined 
                  })}
                >
                  <option value="">All Categories</option>
                  {Object.values(LogCategory).map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
                
                <input 
                  type="text" 
                  placeholder="Search logs..." 
                  value={logFilter.search || ''}
                  onChange={(e) => this.handleLogFilterChange({ 
                    search: e.target.value 
                  })}
                />
              </div>
              
              <div className="error-monitoring-list">
                {filteredLogs.length === 0 ? (
                  <div className="error-monitoring-empty">No logs found</div>
                ) : (
                  filteredLogs.map(log => (
                    <div 
                      key={log.id} 
                      className={`error-monitoring-item log-level-${log.level} ${selectedLog?.id === log.id ? 'selected' : ''}`}
                      onClick={() => this.handleLogSelect(log)}
                    >
                      <div className="error-monitoring-item-header">
                        <span className={`error-monitoring-item-level log-level-${log.level}`}>{log.level}</span>
                        <span className={`error-monitoring-item-category log-category-${log.category}`}>{log.category}</span>
                        <span className="error-monitoring-item-time">
                          {log.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <div className="error-monitoring-item-message">{log.message}</div>
                      {log.component && (
                        <div className="error-monitoring-item-component">{log.component}</div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'notifications' && (
            <div className="error-monitoring-tab-content">
              <div className="error-monitoring-filters">
                <select 
                  value={notificationFilter.type || ''}
                  onChange={(e) => this.handleNotificationFilterChange({ 
                    type: e.target.value as NotificationType || undefined 
                  })}
                >
                  <option value="">All Types</option>
                  {Object.values(NotificationType).map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                
                <select 
                  value={notificationFilter.severity || ''}
                  onChange={(e) => this.handleNotificationFilterChange({ 
                    severity: e.target.value as ErrorSeverity || undefined 
                  })}
                >
                  <option value="">All Severities</option>
                  {Object.values(ErrorSeverity).map(severity => (
                    <option key={severity} value={severity}>{severity}</option>
                  ))}
                </select>
                
                <input 
                  type="text" 
                  placeholder="Search notifications..." 
                  value={notificationFilter.search || ''}
                  onChange={(e) => this.handleNotificationFilterChange({ 
                    search: e.target.value 
                  })}
                />
              </div>
              
              <div className="error-monitoring-list">
                {filteredNotifications.length === 0 ? (
                  <div className="error-monitoring-empty">No notifications found</div>
                ) : (
                  filteredNotifications.map(notification => (
                    <div 
                      key={notification.id} 
                      className={`error-monitoring-item notification-type-${notification.type} ${selectedNotification?.id === notification.id ? 'selected' : ''}`}
                      onClick={() => this.handleNotificationSelect(notification)}
                    >
                      <div className="error-monitoring-item-header">
                        <span className="error-monitoring-item-title">{notification.title}</span>
                        <span className={`error-monitoring-item-severity error-severity-${notification.severity}`}>{notification.severity}</span>
                        <span className={`error-monitoring-item-type notification-type-${notification.type}`}>{notification.type}</span>
                        <span className="error-monitoring-item-time">
                          {notification.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <div className="error-monitoring-item-message">{notification.message}</div>
                      <div className="error-monitoring-item-actions">
                        <button 
                          className="error-monitoring-item-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            this.closeNotification(notification.id);
                          }}
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'metrics' && (
            <div className="error-monitoring-tab-content">
              <div className="error-monitoring-metrics">
                <div className="error-monitoring-metrics-section">
                  <h3>Error Statistics</h3>
                  <div className="error-monitoring-metrics-grid">
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Total Errors</div>
                      <div className="error-monitoring-metric-value">{errorStats.totalErrors}</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Resolved Errors</div>
                      <div className="error-monitoring-metric-value">{errorStats.resolvedErrors}</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Unresolved Errors</div>
                      <div className="error-monitoring-metric-value">{errorStats.unresolvedErrors}</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Error Rate</div>
                      <div className="error-monitoring-metric-value">{errorMetrics.errorRate.toFixed(2)}/hour</div>
                    </div>
                  </div>
                </div>
                
                <div className="error-monitoring-metrics-section">
                  <h3>Errors by Category</h3>
                  <div className="error-monitoring-metrics-chart">
                    {Object.entries(errorStats.errorsByCategory).map(([category, count]) => (
                      <div key={category} className="error-monitoring-metrics-bar">
                        <div className="error-monitoring-metrics-bar-label">{category}</div>
                        <div className="error-monitoring-metrics-bar-container">
                          <div 
                            className="error-monitoring-metrics-bar-fill error-category-${category}" 
                            style={{ width: `${(count / Math.max(...Object.values(errorStats.errorsByCategory))) * 100}%` }}
                          />
                        </div>
                        <div className="error-monitoring-metrics-bar-value">{count}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="error-monitoring-metrics-section">
                  <h3>Performance Metrics</h3>
                  <div className="error-monitoring-metrics-grid">
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Avg Response Time</div>
                      <div className="error-monitoring-metric-value">{performanceMetrics.averageResponseTime.toFixed(2)}ms</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Success Rate</div>
                      <div className="error-monitoring-metric-value">{(performanceMetrics.successRate * 100).toFixed(2)}%</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Request Count</div>
                      <div className="error-monitoring-metric-value">{performanceMetrics.requestCount}</div>
                    </div>
                    <div className="error-monitoring-metric">
                      <div className="error-monitoring-metric-label">Error Count</div>
                      <div className="error-monitoring-metric-value">{performanceMetrics.errorCount}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {selectedError && (
          <div className="error-monitoring-detail">
            <div className="error-monitoring-detail-header">
              <h3>Error Details</h3>
              <button 
                className="error-monitoring-detail-close"
                onClick={() => this.setState({ selectedError: null })}
              >
                ×
              </button>
            </div>
            <div className="error-monitoring-detail-content">
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">ID:</div>
                <div className="error-monitoring-detail-value">{selectedError.id}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Code:</div>
                <div className="error-monitoring-detail-value">{selectedError.code}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Message:</div>
                <div className="error-monitoring-detail-value">{selectedError.message}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Category:</div>
                <div className="error-monitoring-detail-value">{selectedError.category}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Severity:</div>
                <div className="error-monitoring-detail-value">{selectedError.severity}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Status:</div>
                <div className={`error-monitoring-detail-value ${selectedError.resolved ? 'resolved' : 'unresolved'}`}>
                  {selectedError.resolved ? 'Resolved' : 'Unresolved'}
                </div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Count:</div>
                <div className="error-monitoring-detail-value">{selectedError.count}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">First Occurrence:</div>
                <div className="error-monitoring-detail-value">{selectedError.firstOccurrence.toLocaleString()}</div>
              </div>
              <div className="error-monitoring-detail-row">
                <div className="error-monitoring-detail-label">Last Occurrence:</div>
                <div className="error-monitoring-detail-value">{selectedError.lastOccurrence.toLocaleString()}</div>
              </div>
              {selectedError.context && (
                <div className="error-monitoring-detail-section">
                  <h4>Context</h4>
                  <pre className="error-monitoring-detail-context">
                    {JSON.stringify(selectedError.context, null, 2)}
                  </pre>
                </div>
              )}
              {selectedError.stack && (
                <div className="error-monitoring-detail-section">
                  <h4>Stack Trace</h4>
                  <pre className="error-monitoring-detail-stack">
                    {selectedError.stack}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }
}

export default ErrorMonitoringDashboard;