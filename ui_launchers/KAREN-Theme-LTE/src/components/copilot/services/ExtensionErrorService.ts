import { 
  ExtensionError, 
  ExtensionErrorCode,
  ExtensionHealthStatus 
} from '../types/extension';
import ExtensionService from './ExtensionService';

/**
 * Extension error with additional metadata
 */
export interface ExtensionErrorInfo {
  /** Error details */
  error: ExtensionError;
  
  /** Extension ID */
  extensionId: string;
  
  /** Error timestamp */
  timestamp: Date;
  
  /** Error severity */
  severity: ExtensionErrorSeverity;
  
  /** Whether the error has been resolved */
  resolved: boolean;
  
  /** Error context */
  context?: Record<string, unknown>;
}

interface ExtensionErrorEvent {
  type: string;
  timestamp: Date;
  [key: string]: unknown;
}

type ExtensionErrorEventListener = (event: ExtensionErrorEvent) => void;
type ExtensionErrorEventPayload = Record<string, unknown>;

/**
 * Extension error severity levels
 */
export enum ExtensionErrorSeverity {
  /** Low severity error */
  LOW = 'low',
  
  /** Medium severity error */
  MEDIUM = 'medium',
  
  /** High severity error */
  HIGH = 'high',
  
  /** Critical error */
  CRITICAL = 'critical'
}

/**
 * Service for managing extension errors
 */
class ExtensionErrorService {
  private static instance: ExtensionErrorService;
  private extensionService: ExtensionService;
  private errors: Map<string, ExtensionErrorInfo[]> = new Map();
  private errorListeners: Map<string, ExtensionErrorEventListener[]> = new Map();

  private constructor() {
    this.extensionService = ExtensionService.getInstance();
  }

  public static getInstance(): ExtensionErrorService {
    if (!ExtensionErrorService.instance) {
      ExtensionErrorService.instance = new ExtensionErrorService();
    }
    return ExtensionErrorService.instance;
  }

  /**
   * Report an error for an extension
   */
  public reportError(
    extensionId: string, 
    errorCode: ExtensionErrorCode, 
    message: string, 
    details?: unknown,
    context?: Record<string, unknown>
  ): void {
    try {
      console.error(`Reporting error for extension ${extensionId}: ${message}`);
      
      // Create error object
      const error: ExtensionError = {
        code: errorCode,
        message,
        details,
        stack: new Error().stack
      };
      
      // Determine severity based on error code
      const severity = this.getErrorSeverity(errorCode);
      
      // Create error info
      const errorInfo: ExtensionErrorInfo = {
        error,
        extensionId,
        timestamp: new Date(),
        severity,
        resolved: false,
        context
      };
      
      // Add to errors map
      const extensionErrors = this.errors.get(extensionId) || [];
      extensionErrors.push(errorInfo);
      this.errors.set(extensionId, extensionErrors);
      
      // Emit error reported event
      this.emitErrorEvent('error_reported', {
        extensionId,
        errorInfo
      });
      
      // Update extension health status if needed
      this.updateExtensionHealth(extensionId, severity);
      
    } catch (err) {
      console.error(`Failed to report error for extension ${extensionId}:`, err);
    }
  }

  /**
   * Get errors for an extension
   */
  public getErrors(extensionId: string, includeResolved: boolean = false): ExtensionErrorInfo[] {
    const extensionErrors = this.errors.get(extensionId) || [];
    
    if (includeResolved) {
      return extensionErrors;
    }
    
    return extensionErrors.filter(error => !error.resolved);
  }

  /**
   * Get all errors across all extensions
   */
  public getAllErrors(includeResolved: boolean = false): ExtensionErrorInfo[] {
    const allErrors: ExtensionErrorInfo[] = [];
    
    for (const errors of this.errors.values()) {
      if (includeResolved) {
        allErrors.push(...errors);
      } else {
        allErrors.push(...errors.filter(error => !error.resolved));
      }
    }
    
    // Sort by timestamp (newest first)
    allErrors.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    return allErrors;
  }

  /**
   * Get errors by severity
   */
  public getErrorsBySeverity(severity: ExtensionErrorSeverity, includeResolved: boolean = false): ExtensionErrorInfo[] {
    const allErrors = this.getAllErrors(includeResolved);
    return allErrors.filter(error => error.severity === severity);
  }

  /**
   * Get unresolved errors for an extension
   */
  public getUnresolvedErrors(extensionId: string): ExtensionErrorInfo[] {
    return this.getErrors(extensionId, false);
  }

  /**
   * Resolve an error
   */
  public resolveError(extensionId: string, errorIndex: number): boolean {
    try {
      const extensionErrors = this.errors.get(extensionId);
      
      if (!extensionErrors || errorIndex < 0 || errorIndex >= extensionErrors.length) {
        console.warn(`Error index ${errorIndex} not found for extension ${extensionId}`);
        return false;
      }
      
      const errorInfo = extensionErrors[errorIndex];
      
      if (!errorInfo || errorInfo.resolved) {
        console.warn(`Error ${errorIndex} for extension ${extensionId} is already resolved`);
        return true;
      }
      
      // Mark as resolved
      errorInfo.resolved = true;
      
      // Emit error resolved event
      this.emitErrorEvent('error_resolved', {
        extensionId,
        errorInfo
      });
      
      console.log(`Error ${errorIndex} resolved for extension ${extensionId}`);
      return true;
    } catch (err) {
      console.error(`Failed to resolve error ${errorIndex} for extension ${extensionId}:`, err);
      return false;
    }
  }

  /**
   * Resolve all errors for an extension
   */
  public resolveAllErrors(extensionId: string): number {
    try {
      const extensionErrors = this.errors.get(extensionId);
      
      if (!extensionErrors) {
        return 0;
      }
      
      let resolvedCount = 0;
      
      for (const errorInfo of extensionErrors) {
        if (!errorInfo.resolved) {
          errorInfo.resolved = true;
          resolvedCount++;
          
          // Emit error resolved event
          this.emitErrorEvent('error_resolved', {
            extensionId,
            errorInfo
          });
        }
      }
      
      console.log(`Resolved ${resolvedCount} errors for extension ${extensionId}`);
      return resolvedCount;
    } catch (err) {
      console.error(`Failed to resolve all errors for extension ${extensionId}:`, err);
      return 0;
    }
  }

  /**
   * Clear all errors for an extension
   */
  public clearErrors(extensionId: string): boolean {
    try {
      this.errors.delete(extensionId);
      
      // Emit errors cleared event
      this.emitErrorEvent('errors_cleared', {
        extensionId
      });
      
      console.log(`Cleared all errors for extension ${extensionId}`);
      return true;
    } catch (err) {
      console.error(`Failed to clear errors for extension ${extensionId}:`, err);
      return false;
    }
  }

  /**
   * Add error event listener
   */
  public addErrorEventListener(eventType: string, listener: ExtensionErrorEventListener): void {
    if (!this.errorListeners.has(eventType)) {
      this.errorListeners.set(eventType, []);
    }
    this.errorListeners.get(eventType)?.push(listener);
  }

  /**
   * Remove error event listener
   */
  public removeErrorEventListener(eventType: string, listener: ExtensionErrorEventListener): void {
    const listeners = this.errorListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Get error severity based on error code
   */
  private getErrorSeverity(errorCode: ExtensionErrorCode): ExtensionErrorSeverity {
    switch (errorCode) {
      case ExtensionErrorCode.GENERAL_ERROR:
        return ExtensionErrorSeverity.MEDIUM;
        
      case ExtensionErrorCode.INVALID_REQUEST:
        return ExtensionErrorSeverity.LOW;
        
      case ExtensionErrorCode.PERMISSION_DENIED:
        return ExtensionErrorSeverity.MEDIUM;
        
      case ExtensionErrorCode.NOT_FOUND:
        return ExtensionErrorSeverity.LOW;
        
      case ExtensionErrorCode.VALIDATION_ERROR:
        return ExtensionErrorSeverity.LOW;
        
      case ExtensionErrorCode.EXECUTION_ERROR:
        return ExtensionErrorSeverity.HIGH;
        
      case ExtensionErrorCode.TIMEOUT_ERROR:
        return ExtensionErrorSeverity.MEDIUM;
        
      case ExtensionErrorCode.CONFIGURATION_ERROR:
        return ExtensionErrorSeverity.HIGH;
        
      default:
        return ExtensionErrorSeverity.MEDIUM;
    }
  }

  /**
   * Update extension health status based on error severity
   */
  private updateExtensionHealth(extensionId: string, severity: ExtensionErrorSeverity): void {
    try {
      // Get current extension status
      const status = this.extensionService.getExtensionStatus(extensionId);
      
      if (!status) {
        return;
      }
      
      // Update health based on severity
      switch (severity) {
        case ExtensionErrorSeverity.LOW:
          // Low severity errors don't affect health
          break;
          
        case ExtensionErrorSeverity.MEDIUM:
          // Medium severity errors set health to warning if it was healthy
          if (status.health === ExtensionHealthStatus.HEALTHY) {
            status.health = ExtensionHealthStatus.WARNING;
          }
          break;
          
        case ExtensionErrorSeverity.HIGH:
          // High severity errors set health to error
          status.health = ExtensionHealthStatus.ERROR;
          break;
          
        case ExtensionErrorSeverity.CRITICAL:
          // Critical errors set health to error
          status.health = ExtensionHealthStatus.ERROR;
          break;
      }
      
    } catch (err) {
      console.error(`Failed to update extension health for ${extensionId}:`, err);
    }
  }

  /**
   * Emit error event
   */
  private emitErrorEvent(eventType: string, data: ExtensionErrorEventPayload): void {
    const listeners = this.errorListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in error event listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Get error statistics for an extension
   */
  public getErrorStats(extensionId: string): {
    total: number;
    resolved: number;
    unresolved: number;
    bySeverity: Record<ExtensionErrorSeverity, number>;
    byCode: Record<ExtensionErrorCode, number>;
  } {
    const extensionErrors = this.errors.get(extensionId) || [];
    
    const stats = {
      total: extensionErrors.length,
      resolved: 0,
      unresolved: 0,
      bySeverity: {
        [ExtensionErrorSeverity.LOW]: 0,
        [ExtensionErrorSeverity.MEDIUM]: 0,
        [ExtensionErrorSeverity.HIGH]: 0,
        [ExtensionErrorSeverity.CRITICAL]: 0
      } as Record<ExtensionErrorSeverity, number>,
      byCode: {} as Record<ExtensionErrorCode, number>
    };
    
    for (const error of extensionErrors) {
      if (error.resolved) {
        stats.resolved++;
      } else {
        stats.unresolved++;
      }
      
      stats.bySeverity[error.severity]++;
      stats.byCode[error.error.code] = (stats.byCode[error.error.code] || 0) + 1;
    }
    
    return stats;
  }
}

export default ExtensionErrorService;
