import React, { createContext, useState, useCallback, ReactNode } from 'react';
import { ErrorInfo } from '../components/error-handling/types';

export interface ErrorContextType {
  errors: ErrorInfo[];
  addError: (error: ErrorInfo) => void;
  removeError: (errorId: string) => void;
  clearErrors: () => void;
  activeError: ErrorInfo | null;
  setActiveError: (error: ErrorInfo | null) => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [errors, setErrors] = useState<ErrorInfo[]>([]);
  const [activeError, setActiveError] = useState<ErrorInfo | null>(null);

  const addError = useCallback((error: ErrorInfo) => {
    setErrors(prev => {
      const newErrors = [...prev, error];
      return newErrors;
    });
    if (!activeError || error.severity > activeError.severity) {
      setActiveError(error);
    }
  }, [activeError]);

  const removeError = useCallback((errorId: string) => {
    setErrors(prev => {
      const remainingErrors = prev.filter(error => error.id !== errorId);
      if (activeError?.id === errorId) {
        const newActiveError = remainingErrors.length > 0 ? remainingErrors[remainingErrors.length - 1]! : null;
        setActiveError(newActiveError);
      }
      return remainingErrors;
    });
  }, [activeError]);

  const clearErrors = useCallback(() => {
    setErrors([]);
    setActiveError(null);
  }, []);

  const contextValue: ErrorContextType = {
    errors,
    addError,
    removeError,
    clearErrors,
    activeError,
    setActiveError,
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
};

export { ErrorContext };
