import React from 'react';
import ErrorBoundary from './ErrorBoundary';
import { ErrorBoundaryProps } from './types';

/**
 * Chat-specific wrapper around the shared error boundary.
 * Preserves the existing prop contract while providing a chat-oriented default component label.
 */
export const ChatErrorBoundary: React.FC<ErrorBoundaryProps> = ({
  component = 'ChatComponent',
  ...props
}) => {
  return <ErrorBoundary component={component} {...props} />;
};

export default ChatErrorBoundary;
