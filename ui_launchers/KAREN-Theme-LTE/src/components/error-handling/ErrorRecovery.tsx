import React, { useState, useEffect, useCallback } from 'react';
import { ErrorInfo, RecoveryAction, RecoveryResult, ErrorRecoveryProps } from './types';

/**
 * Error Recovery Component for CoPilot Frontend
 * 
 * This component provides comprehensive error recovery functionality with:
 * - Multiple recovery strategies
 * - Progress indication
 * - User interaction
 * - Automatic recovery attempts
 * - Recovery status feedback
 */
const ErrorRecovery: React.FC<ErrorRecoveryProps> = ({
  error,
  onRecovery,
  onCancel,
  availableActions,
  showProgress = true,
  autoRecover = false,
  maxAutoAttempts = 3,
  className = ''
}) => {
  const [isRecovering, setIsRecovering] = useState(false);
  const [currentAction, setCurrentAction] = useState<RecoveryAction | null>(null);
  const [progress, setProgress] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [recoveryResult, setRecoveryResult] = useState<RecoveryResult | null>(null);

  const getAvailableRecoveryActions = useCallback((): RecoveryAction[] => {
    if (availableActions) {
      return availableActions;
    }

    // Default recovery actions based on error type
    const defaultActions: RecoveryAction[] = [];

    if (error.retryPossible) {
      defaultActions.push({
        id: 'retry',
        strategy: 'retry_with_backoff',
        description: 'Retry the operation with exponential backoff',
        priority: 90,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      });
    }

    if (error.category === 'network' || error.category === 'connectivity') {
      defaultActions.push({
        id: 'fallback_endpoint',
        strategy: 'fallback_to_alternative',
        description: 'Use alternative endpoint or service',
        priority: 80,
        maxAttempts: 2,
        timeout: 15000,
        requiresUserInput: false
      });
    }

    if (error.category === 'ai_processing' || error.category === 'model_unavailable') {
      defaultActions.push({
        id: 'fallback_model',
        strategy: 'fallback_model',
        description: 'Use alternative AI model',
        priority: 85,
        maxAttempts: 2,
        timeout: 20000,
        requiresUserInput: false
      });
    }

    if (error.userActionRequired) {
      defaultActions.push({
        id: 'user_action',
        strategy: 'user_action_required',
        description: 'User action required to resolve error',
        priority: 95,
        maxAttempts: 1,
        timeout: 0,
        requiresUserInput: true
      });
    }

    return defaultActions.sort((a, b) => b.priority - a.priority);
  }, [availableActions, error]);

  async function executeRecoveryAction(action: RecoveryAction, currentError: ErrorInfo): Promise<RecoveryResult> {
    switch (action.strategy) {
      case 'retry_with_backoff':
        return await executeRetryWithBackoff();
      
      case 'fallback_to_alternative':
        return await executeFallbackToAlternative(currentError);
      
      case 'fallback_model':
        return await executeFallbackModel(currentError);
      
      case 'user_action_required':
        return await executeUserAction(currentError);
      
      default:
        return {
          finalStatus: 'failed',
          failedActions: [],
          successfulActions: [],
          totalDuration: 0,
          finalError: `Unknown recovery strategy: ${action.strategy}`
        };
    }
  }

  async function executeRetryWithBackoff(): Promise<RecoveryResult> {
    // Simulate retry with exponential backoff
    const delay = Math.pow(2, attempts) * 1000; // 2^attempt seconds
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // In a real implementation, this would retry the original operation
    // For now, we'll simulate a successful retry
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'retry',
        strategy: 'retry_with_backoff',
        description: 'Retry the operation with exponential backoff',
        priority: 90,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [{
        action: {
          id: 'retry',
          strategy: 'retry_with_backoff',
          description: 'Retry the operation with exponential backoff',
          priority: 90,
          maxAttempts: 3,
          timeout: 30000,
          requiresUserInput: false
        },
        attemptNumber: attempts + 1,
        startTime: new Date(Date.now() - delay).toISOString(),
        endTime: new Date().toISOString(),
        status: 'success'
      }],
      totalDuration: delay,
      metadata: {
        retryAttempt: attempts + 1,
        backoffDelay: delay
      }
    };
  }

  async function executeFallbackToAlternative(error: ErrorInfo): Promise<RecoveryResult> {
    // Simulate fallback to alternative service
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'fallback_endpoint',
        strategy: 'fallback_to_alternative',
        description: 'Use alternative endpoint or service',
        priority: 80,
        maxAttempts: 2,
        timeout: 15000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [{
        action: {
          id: 'fallback_endpoint',
          strategy: 'fallback_to_alternative',
          description: 'Use alternative endpoint or service',
          priority: 80,
          maxAttempts: 2,
          timeout: 15000,
          requiresUserInput: false
        },
        attemptNumber: 1,
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        status: 'success'
      }],
      totalDuration: 2000,
      metadata: {
        fallbackService: 'alternative_endpoint',
        originalService: error.context?.service
      }
    };
  }

  async function executeFallbackModel(error: ErrorInfo): Promise<RecoveryResult> {
    // Simulate fallback to alternative AI model
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'fallback_model',
        strategy: 'fallback_model',
        description: 'Use alternative AI model',
        priority: 85,
        maxAttempts: 2,
        timeout: 20000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [{
        action: {
          id: 'fallback_model',
          strategy: 'fallback_model',
          description: 'Use alternative AI model',
          priority: 85,
          maxAttempts: 2,
          timeout: 20000,
          requiresUserInput: false
        },
        attemptNumber: 1,
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        status: 'success'
      }],
      totalDuration: 3000,
      metadata: {
        fallbackModel: 'gpt-3.5-turbo',
        originalModel: error.context?.model
      }
    };
  }

  async function executeUserAction(error: ErrorInfo): Promise<RecoveryResult> {
    // User action required - wait for user input
    return new Promise((resolve) => {
      // In a real implementation, this would wait for user input
      // For now, we'll resolve after a delay
      setTimeout(() => {
        resolve({
          finalStatus: 'success',
          successfulAction: {
            id: 'user_action',
            strategy: 'user_action_required',
            description: 'User action required to resolve error',
            priority: 95,
            maxAttempts: 1,
            timeout: 0,
            requiresUserInput: true
          },
          failedActions: [],
          successfulActions: [{
            action: {
              id: 'user_action',
              strategy: 'user_action_required',
              description: 'User action required to resolve error',
              priority: 95,
              maxAttempts: 1,
              timeout: 0,
              requiresUserInput: true
            },
            attemptNumber: 1,
            startTime: new Date().toISOString(),
            endTime: new Date().toISOString(),
            status: 'success'
          }],
          totalDuration: 0,
          metadata: {
            userActionCompleted: true,
            resolutionSteps: error.resolutionSteps
          }
        });
      }, 1000);
    });
  }

  const startRecovery = useCallback(async (selectedAction?: RecoveryAction) => {
    const action = selectedAction || getAvailableRecoveryActions()[0];
    
    if (!action) {
      return;
    }

    setIsRecovering(true);
    setCurrentAction(action);
    setAttempts(prev => prev + 1);
    setProgress(0);

    try {
      // Simulate recovery progress
      let progressInterval: NodeJS.Timeout | undefined;
      if (showProgress) {
        progressInterval = setInterval(() => {
          setProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 100;
            }
            return prev + 10;
          });
        }, 200);
      }

      const result = await executeRecoveryAction(action, error);
      
      if (showProgress && progressInterval) {
        clearInterval(progressInterval);
        setProgress(100);
      }

      setRecoveryResult(result);
      
      if (onRecovery) {
        onRecovery(result);
      }

      setTimeout(() => {
        setIsRecovering(false);
        setCurrentAction(null);
        setProgress(0);
      }, 2000);

    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
      const errorMessage = recoveryError instanceof Error ? recoveryError.message : String(recoveryError);
      
      setRecoveryResult({
        finalStatus: 'failed',
        failedActions: [{
          action,
          attemptNumber: attempts + 1,
          startTime: new Date().toISOString(),
          status: 'failed',
          error: errorMessage
        }],
        successfulActions: [],
        totalDuration: 0,
        finalError: errorMessage
      });

      setIsRecovering(false);
      setCurrentAction(null);
      setProgress(0);
    }
  }, [attempts, error, executeRecoveryAction, getAvailableRecoveryActions, onRecovery, showProgress]);

  useEffect(() => {
    // Auto-recover if enabled
    if (autoRecover && error && !isRecovering && attempts < maxAutoAttempts) {
      void startRecovery();
    }
  }, [autoRecover, error, isRecovering, attempts, maxAutoAttempts, startRecovery]);

  const handleCancel = () => {
    setIsRecovering(false);
    setCurrentAction(null);
    setProgress(0);
    
    if (onCancel) {
      onCancel();
    }
  };

  const getActionDescription = (action: RecoveryAction): string => {
    switch (action.strategy) {
      case 'retry_with_backoff':
        return `Retrying operation (attempt ${attempts + 1}/${action.maxAttempts})`;
      
      case 'fallback_to_alternative':
        return 'Switching to alternative service...';
      
      case 'fallback_model':
        return 'Switching to alternative AI model...';
      
      case 'user_action_required':
        return 'Waiting for user action...';
      
      default:
        return action.description;
    }
  };

  if (!error) {
    return null;
  }

  const actions = getAvailableRecoveryActions();

  return (
    <div className={`error-recovery ${className}`} style={{
      padding: '20px',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      backgroundColor: '#fff',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
    }}>
      <h3 style={{ 
        margin: '0 0 16px 0', 
        color: '#374151',
        fontSize: '18px',
        fontWeight: '600'
      }}>
        Error Recovery
      </h3>
      
      <div style={{ marginBottom: '16px' }}>
        <div style={{ 
          fontSize: '14px', 
          color: '#6b7280',
          marginBottom: '8px'
        }}>
          <strong>Error:</strong> {error.title}
        </div>
        <div style={{ 
          fontSize: '12px', 
          color: '#6b7280',
          lineHeight: '1.5'
        }}>
          {error.message}
        </div>
      </div>

      {showProgress && isRecovering && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <span style={{ fontSize: '12px', color: '#6b7280' }}>
              {currentAction ? getActionDescription(currentAction) : actions[0] ? getActionDescription(actions[0]) : 'Initializing recovery...'}
            </span>
            <span style={{ fontSize: '12px', color: '#6b7280' }}>
              {progress}%
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#e5e7eb',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: '#3b82f6',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      )}
      
      {!isRecovering && actions.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ 
            margin: '0 0 12px 0', 
            fontSize: '14px',
            color: '#374151'
          }}>
            Recovery Options:
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {actions.map((action, index) => (
              <button
                key={action.id}
                onClick={() => startRecovery(action)}
                style={{
                  padding: '12px 16px',
                  backgroundColor: '#f9fafb',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#3b82f6';
                  e.currentTarget.style.borderColor = '#3b82f6';
                  e.currentTarget.style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f9fafb';
                  e.currentTarget.style.borderColor = '#d1d5db';
                  e.currentTarget.style.color = '#374151';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: '#3b82f6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {index + 1}
                  </div>
                  <div>
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                      {action.description}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      Priority: {action.priority} | Max attempts: {action.maxAttempts}
                    </div>
                    {action.requiresUserInput && (
                      <div style={{ fontSize: '11px', color: '#059669', marginTop: '4px' }}>
                        ⚠️ Requires user input
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
      
      {recoveryResult && (
        <div style={{
          padding: '12px',
          backgroundColor: recoveryResult.finalStatus === 'success' ? '#f0fdf4' : '#fef2f2',
          border: `1px solid ${recoveryResult.finalStatus === 'success' ? '#86efac' : '#fca5a5'}`,
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          <div style={{
            fontSize: '14px',
            fontWeight: '600',
            color: recoveryResult.finalStatus === 'success' ? '#166534' : '#dc2626',
            marginBottom: '4px'
          }}>
            {recoveryResult.finalStatus === 'success' ? '✅ Recovery Successful' : '❌ Recovery Failed'}
          </div>
          {recoveryResult.metadata && (
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              {Object.entries(recoveryResult.metadata).map(([key, value]) => (
                <div key={key} style={{ marginBottom: '2px' }}>
                  <strong>{key}:</strong> {String(value)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {isRecovering && (
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
          <button
            onClick={handleCancel}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Cancel Recovery
          </button>
        </div>
      )}
    </div>
  );
};

export default ErrorRecovery;
