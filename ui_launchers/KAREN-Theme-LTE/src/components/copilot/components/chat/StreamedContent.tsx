import React, { useRef, useEffect } from 'react';
import { StreamingResponse } from '../utils/streaming-utils';

interface StreamedContentProps {
  response: StreamingResponse | null;
  isLoading?: boolean;
  error?: Error | null;
  theme?: any;
  className?: string;
  showTypingIndicator?: boolean;
  typingIndicator?: React.ReactNode;
}

export const StreamedContent: React.FC<StreamedContentProps> = ({
  response,
  isLoading = false,
  error,
  theme,
  className = '',
  showTypingIndicator = true,
  typingIndicator
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when content updates
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [response?.content]);

  if (error) {
    return (
      <div className={`copilot-streamed-error ${className}`} style={{ color: theme?.colors?.error }}>
        Error: {error.message}
      </div>
    );
  }

  return (
    <div className={`copilot-streamed-content ${className}`} style={{ position: 'relative' }} role="region" aria-live="polite">
      <div
        ref={contentRef}
        className="copilot-streamed-text"
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: '1.5'
        }}
        aria-label="Streamed content"
      >
        {response?.content || ''}
      </div>
      
      {isLoading && showTypingIndicator && (
        <div
          className="copilot-typing-indicator"
          style={{ display: 'flex', alignItems: 'center', marginTop: '8px' }}
          role="status"
          aria-label="Assistant is typing"
          aria-busy="true"
        >
          {typingIndicator || (
            <>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, marginRight: '4px', animation: 'pulse 1.4s infinite' }} aria-hidden="true"></span>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, marginRight: '4px', animation: 'pulse 1.4s infinite 0.2s' }} aria-hidden="true"></span>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme?.colors?.primary, animation: 'pulse 1.4s infinite 0.4s' }} aria-hidden="true"></span>
            </>
          )}
        </div>
      )}
      
      <style jsx>{`
        @keyframes pulse {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
};

export default StreamedContent;