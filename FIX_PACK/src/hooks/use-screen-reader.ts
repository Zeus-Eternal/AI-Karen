import { useCallback, useEffect, useRef } from 'react';
import { useTelemetry } from './use-telemetry';

export interface ScreenReaderOptions {
  announceOnMount?: string;
  announceOnUnmount?: string;
  politeness?: 'polite' | 'assertive';
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
}

export interface LiveRegionManager {
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  announceWithDelay: (message: string, delay?: number, priority?: 'polite' | 'assertive') => void;
  clear: () => void;
  setStatus: (status: string) => void;
  announceProgress: (current: number, total: number, label?: string) => void;
}

export const useScreenReader = (options: ScreenReaderOptions = {}): LiveRegionManager => {
  const { track } = useTelemetry();
  const liveRegionRef = useRef<HTMLDivElement | null>(null);
  const statusRegionRef = useRef<HTMLDivElement | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  // Create live regions if they don't exist
  useEffect(() => {
    if (!liveRegionRef.current) {
      const liveRegion = document.createElement('div');
      liveRegion.setAttribute('aria-live', options.politeness || 'polite');
      liveRegion.setAttribute('aria-atomic', options.atomic ? 'true' : 'false');
      liveRegion.setAttribute('aria-relevant', options.relevant || 'additions text');
      liveRegion.className = 'sr-only';
      liveRegion.id = 'live-region-announcements';
      document.body.appendChild(liveRegion);
      liveRegionRef.current = liveRegion;
    }

    if (!statusRegionRef.current) {
      const statusRegion = document.createElement('div');
      statusRegion.setAttribute('role', 'status');
      statusRegion.setAttribute('aria-live', 'polite');
      statusRegion.setAttribute('aria-atomic', 'true');
      statusRegion.className = 'sr-only';
      statusRegion.id = 'live-region-status';
      document.body.appendChild(statusRegion);
      statusRegionRef.current = statusRegion;
    }

    // Announce on mount
    if (options.announceOnMount) {
      const timer = setTimeout(() => {
        announce(options.announceOnMount!);
      }, 100);
      return () => clearTimeout(timer);
    }

    return () => {
      // Announce on unmount
      if (options.announceOnUnmount) {
        announce(options.announceOnUnmount);
      }
    };
  }, [options.announceOnMount, options.announceOnUnmount, options.politeness, options.atomic, options.relevant]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      // Clean up live regions when component unmounts
      if (liveRegionRef.current && document.body.contains(liveRegionRef.current)) {
        document.body.removeChild(liveRegionRef.current);
      }
      if (statusRegionRef.current && document.body.contains(statusRegionRef.current)) {
        document.body.removeChild(statusRegionRef.current);
      }
    };
  }, []);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!message.trim()) return;

    const region = liveRegionRef.current;
    if (!region) return;

    // Clear any pending announcements
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Update aria-live attribute if needed
    if (region.getAttribute('aria-live') !== priority) {
      region.setAttribute('aria-live', priority);
    }

    // Clear the region first to ensure the announcement is heard
    region.textContent = '';
    
    // Add the message after a brief delay
    timeoutRef.current = setTimeout(() => {
      region.textContent = message;
      track('screen_reader_announcement', { 
        message: message.substring(0, 100), 
        priority,
        length: message.length 
      });
    }, 10);
  }, [track]);

  const announceWithDelay = useCallback((
    message: string, 
    delay: number = 1000, 
    priority: 'polite' | 'assertive' = 'polite'
  ) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      announce(message, priority);
    }, delay);
  }, [announce]);

  const clear = useCallback(() => {
    if (liveRegionRef.current) {
      liveRegionRef.current.textContent = '';
    }
    if (statusRegionRef.current) {
      statusRegionRef.current.textContent = '';
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  const setStatus = useCallback((status: string) => {
    if (!statusRegionRef.current) return;
    
    statusRegionRef.current.textContent = status;
    track('screen_reader_status', { status: status.substring(0, 100) });
  }, [track]);

  const announceProgress = useCallback((
    current: number, 
    total: number, 
    label: string = 'Progress'
  ) => {
    const percentage = Math.round((current / total) * 100);
    const message = `${label}: ${current} of ${total}, ${percentage} percent complete`;
    setStatus(message);
  }, [setStatus]);

  return {
    announce,
    announceWithDelay,
    clear,
    setStatus,
    announceProgress
  };
};

// Utility functions for common screen reader patterns
export const createAriaLabel = (
  baseLabel: string, 
  context?: { 
    state?: string;
    position?: { current: number; total: number };
    description?: string;
  }
): string => {
  let label = baseLabel;
  
  if (context?.state) {
    label += `, ${context.state}`;
  }
  
  if (context?.position) {
    label += `, ${context.position.current} of ${context.position.total}`;
  }
  
  if (context?.description) {
    label += `, ${context.description}`;
  }
  
  return label;
};

export const createAriaDescribedBy = (...ids: (string | undefined | null)[]): string => {
  return ids.filter(Boolean).join(' ');
};

// Common ARIA patterns for chat interface
export const chatAriaPatterns = {
  messageList: {
    role: 'log',
    'aria-live': 'polite',
    'aria-atomic': 'false',
    'aria-relevant': 'additions',
    'aria-label': 'Conversation messages'
  },
  
  message: (role: 'user' | 'assistant', timestamp: string, index: number, total: number) => ({
    role: 'article',
    'aria-label': createAriaLabel(`${role} message`, {
      position: { current: index + 1, total },
      description: `sent at ${timestamp}`
    })
  }),
  
  composer: {
    role: 'region',
    'aria-label': 'Message composer'
  },
  
  streamingMessage: {
    'aria-live': 'polite',
    'aria-atomic': 'false',
    'aria-relevant': 'additions text',
    'aria-label': 'Assistant is typing'
  },
  
  quickActions: {
    role: 'toolbar',
    'aria-label': 'Quick actions'
  },
  
  messageActions: {
    role: 'group',
    'aria-label': 'Message actions'
  }
};