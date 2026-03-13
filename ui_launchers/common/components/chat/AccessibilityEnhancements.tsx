import React, { useEffect, useRef, useState, KeyboardEvent } from 'react';

// Type definitions
interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface AccessibilityAnnouncement {
  message: string;
  politeness: 'polite' | 'assertive';
  timeout?: number;
}

interface AccessibilityEnhancementsProps {
  theme: Theme;
  announcements?: AccessibilityAnnouncement[];
  onAnnouncementComplete?: (announcement: AccessibilityAnnouncement) => void;
  onKeyboardShortcut?: (shortcut: string) => void;
  children?: React.ReactNode;
  className?: string;
}

// Default theme
const defaultTheme: Theme = {
  colors: {
    primary: '#3b82f6',
    secondary: '#64748b',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#10b981',
    info: '#3b82f6'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      xxl: '1.5rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
  }
};

// Keyboard shortcuts
const keyboardShortcuts = [
  {
    key: '/',
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    description: 'Focus on message input',
    action: 'focusInput'
  },
  {
    key: 'h',
    ctrlKey: true,
    shiftKey: false,
    altKey: false,
    description: 'Toggle conversation history',
    action: 'toggleHistory'
  },
  {
    key: 'v',
    ctrlKey: true,
    shiftKey: false,
    altKey: false,
    description: 'Toggle voice input',
    action: 'toggleVoice'
  },
  {
    key: 'Escape',
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    description: 'Close modals or cancel actions',
    action: 'escape'
  },
  {
    key: 'ArrowUp',
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    description: 'Navigate to previous message',
    action: 'previousMessage'
  },
  {
    key: 'ArrowDown',
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    description: 'Navigate to next message',
    action: 'nextMessage'
  },
  {
    key: 'Enter',
    ctrlKey: false,
    shiftKey: false,
    altKey: false,
    description: 'Send message',
    action: 'sendMessage'
  },
  {
    key: 'Enter',
    ctrlKey: false,
    shiftKey: true,
    altKey: false,
    description: 'Add new line to message',
    action: 'newLine'
  }
];

// Hook for managing focus
export const useFocusManager = () => {
  const [focusedElement, setFocusedElement] = useState<string | null>(null);
  
  const focusElement = (elementId: string) => {
    const element = document.getElementById(elementId);
    if (element) {
      element.focus();
      setFocusedElement(elementId);
    }
  };
  
  const announceFocusChange = (elementId: string) => {
    setFocusedElement(elementId);
  };
  
  return {
    focusedElement,
    focusElement,
    announceFocusChange
  };
};

// Hook for managing announcements
export const useAnnouncer = () => {
  const [announcements, setAnnouncements] = useState<AccessibilityAnnouncement[]>([]);
  
  const announce = (message: string, politeness: 'polite' | 'assertive' = 'polite', timeout?: number) => {
    const newAnnouncement: AccessibilityAnnouncement = {
      message,
      politeness,
      timeout
    };
    
    setAnnouncements(prev => [...prev, newAnnouncement]);
    
    if (timeout) {
      setTimeout(() => {
        setAnnouncements(prev => prev.filter(a => a !== newAnnouncement));
      }, timeout);
    }
  };
  
  const clearAnnouncements = () => {
    setAnnouncements([]);
  };
  
  return {
    announcements,
    announce,
    clearAnnouncements
  };
};

// Hook for keyboard navigation
export const useKeyboardNavigation = (
  shortcuts: Array<{
    key: string;
    ctrlKey?: boolean;
    shiftKey?: boolean;
    altKey?: boolean;
    action: string;
  }>,
  onShortcut?: (shortcut: string) => void
) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatch = e.key === shortcut.key;
        const ctrlMatch = !!shortcut.ctrlKey === e.ctrlKey;
        const shiftMatch = !!shortcut.shiftKey === e.shiftKey;
        const altMatch = !!shortcut.altKey === e.altKey;
        
        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          e.preventDefault();
          if (onShortcut) {
            onShortcut(shortcut.action);
          }
          break;
        }
      }
    };
    
    const handleKeyDownWrapper = (e: globalThis.KeyboardEvent) => {
      handleKeyDown(e as unknown as KeyboardEvent<Element>);
    };
    
    document.addEventListener('keydown', handleKeyDownWrapper);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDownWrapper);
    };
  }, [shortcuts, onShortcut]);
};

// Component for screen reader announcements
export const Announcer: React.FC<{
  announcements: AccessibilityAnnouncement[];
  onAnnouncementComplete?: (announcement: AccessibilityAnnouncement) => void;
}> = ({ announcements, onAnnouncementComplete }) => {
  return (
    <div className="sr-only">
      {announcements.map((announcement, index) => (
        <div
          key={index}
          aria-live={announcement.politeness}
          aria-atomic="true"
          onAnimationEnd={() => {
            if (onAnnouncementComplete) {
              onAnnouncementComplete(announcement);
            }
          }}
        >
          {announcement.message}
        </div>
      ))}
    </div>
  );
};

// Component for keyboard shortcuts help modal
export const KeyboardShortcutsHelp: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  shortcuts: typeof keyboardShortcuts;
  theme: Theme;
}> = ({ isOpen, onClose, shortcuts, theme }) => {
  if (!isOpen) return null;
  
  return (
    <div 
      className="karen-keyboard-shortcuts-modal"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="keyboard-shortcuts-title"
    >
      <div 
        className="karen-keyboard-shortcuts-content"
        style={{
          backgroundColor: theme.colors.background,
          borderRadius: theme.borderRadius,
          boxShadow: theme.shadows.lg,
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
          padding: theme.spacing.lg
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div 
          className="karen-keyboard-shortcuts-header"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: theme.spacing.lg
          }}
        >
          <h2 
            id="keyboard-shortcuts-title"
            className="karen-keyboard-shortcuts-title"
            style={{
              margin: 0,
              fontSize: theme.typography.fontSize.xl,
              fontWeight: theme.typography.fontWeight.bold
            }}
          >
            Keyboard Shortcuts
          </h2>
          <button
            onClick={onClose}
            className="karen-keyboard-shortcuts-close"
            aria-label="Close keyboard shortcuts"
            style={{
              backgroundColor: 'transparent',
              color: theme.colors.text,
              border: 'none',
              borderRadius: theme.borderRadius,
              padding: theme.spacing.sm,
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
          >
            ✕
          </button>
        </div>
        
        <div 
          className="karen-keyboard-shortcuts-list"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.md
          }}
        >
          {shortcuts.map((shortcut, index) => (
            <div 
              key={index}
              className="karen-keyboard-shortcut-item"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: theme.spacing.sm,
                backgroundColor: theme.colors.surface,
                borderRadius: theme.borderRadius,
                border: `1px solid ${theme.colors.border}`
              }}
            >
              <div 
                className="karen-keyboard-shortcut-description"
                style={{
                  fontSize: theme.typography.fontSize.base
                }}
              >
                {shortcut.description}
              </div>
              <div 
                className="karen-keyboard-shortcut-keys"
                style={{
                  display: 'flex',
                  gap: theme.spacing.xs,
                  alignItems: 'center'
                }}
              >
                {shortcut.ctrlKey && (
                  <kbd 
                    className="karen-keyboard-shortcut-key"
                    style={{
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      backgroundColor: theme.colors.background,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '4px',
                      fontSize: theme.typography.fontSize.sm,
                      fontWeight: theme.typography.fontWeight.medium
                    }}
                  >
                    Ctrl
                  </kbd>
                )}
                {shortcut.shiftKey && (
                  <kbd 
                    className="karen-keyboard-shortcut-key"
                    style={{
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      backgroundColor: theme.colors.background,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '4px',
                      fontSize: theme.typography.fontSize.sm,
                      fontWeight: theme.typography.fontWeight.medium
                    }}
                  >
                    Shift
                  </kbd>
                )}
                {shortcut.altKey && (
                  <kbd 
                    className="karen-keyboard-shortcut-key"
                    style={{
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      backgroundColor: theme.colors.background,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '4px',
                      fontSize: theme.typography.fontSize.sm,
                      fontWeight: theme.typography.fontWeight.medium
                    }}
                  >
                    Alt
                  </kbd>
                )}
                <kbd 
                  className="karen-keyboard-shortcut-key"
                  style={{
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    backgroundColor: theme.colors.background,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: '4px',
                    fontSize: theme.typography.fontSize.sm,
                    fontWeight: theme.typography.fontWeight.medium
                  }}
                >
                  {shortcut.key}
                </kbd>
              </div>
            </div>
          ))}
        </div>
        
        <div 
          className="karen-keyboard-shortcuts-footer"
          style={{
            marginTop: theme.spacing.lg,
            textAlign: 'center',
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.textSecondary
          }}
        >
          Press <strong>Escape</strong> to close this dialog
        </div>
      </div>
    </div>
  );
};

// Main accessibility enhancements component
export const AccessibilityEnhancements: React.FC<AccessibilityEnhancementsProps> = ({
  theme = defaultTheme,
  announcements = [],
  onAnnouncementComplete,
  onKeyboardShortcut,
  children,
  className = ''
}) => {
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  const { announce, clearAnnouncements } = useAnnouncer();
  const { focusElement } = useFocusManager();
  
  // Handle keyboard shortcuts
  useKeyboardNavigation(keyboardShortcuts, (action) => {
    switch (action) {
      case 'focusInput':
        focusElement('karen-message-input');
        announce('Focused on message input');
        break;
      case 'toggleHistory':
        // This would be handled by the parent component
        announce('Toggled conversation history');
        break;
      case 'toggleVoice':
        // This would be handled by the parent component
        announce('Toggled voice input');
        break;
      case 'escape':
        if (showShortcutsHelp) {
          setShowShortcutsHelp(false);
          announce('Closed keyboard shortcuts help');
        }
        break;
      case 'showShortcuts':
        setShowShortcutsHelp(true);
        announce('Opened keyboard shortcuts help');
        break;
      default:
        break;
    }
    
    if (onKeyboardShortcut) {
      onKeyboardShortcut(action);
    }
  });
  
  return (
    <div 
      className={`karen-accessibility-enhancements ${className}`}
      style={{
        position: 'relative'
      }}
    >
      {/* Screen reader only content */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        <Announcer 
          announcements={announcements} 
          onAnnouncementComplete={onAnnouncementComplete} 
        />
      </div>
      
      {/* Skip to content link for keyboard users */}
      <a
        href="#karen-chat-content"
        className="karen-skip-link"
        style={{
          position: 'absolute',
          top: '-40px',
          left: 0,
          backgroundColor: theme.colors.primary,
          color: 'white',
          padding: `${theme.spacing.sm} ${theme.spacing.md}`,
          textDecoration: 'none',
          borderRadius: `0 0 ${theme.borderRadius} 0`,
          zIndex: 100,
          transition: 'top 0.3s ease'
        }}
        onFocus={(e) => {
          e.currentTarget.style.top = '0';
        }}
        onBlur={(e) => {
          e.currentTarget.style.top = '-40px';
        }}
      >
        Skip to main content
      </a>
      
      {/* Keyboard shortcuts help button */}
      <button
        onClick={() => setShowShortcutsHelp(true)}
        className="karen-keyboard-shortcuts-help-button"
        aria-label="Show keyboard shortcuts help"
        style={{
          position: 'fixed',
          bottom: theme.spacing.lg,
          right: theme.spacing.lg,
          backgroundColor: theme.colors.primary,
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '48px',
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: theme.shadows.md,
          zIndex: 100
        }}
        title="Keyboard shortcuts (?)"
      >
        ?
      </button>
      
      {/* Keyboard shortcuts help modal */}
      <KeyboardShortcutsHelp
        isOpen={showShortcutsHelp}
        onClose={() => setShowShortcutsHelp(false)}
        shortcuts={keyboardShortcuts}
        theme={theme}
      />
      
      {/* Main content */}
      <div id="karen-chat-content" tabIndex={-1}>
        {children}
      </div>
    </div>
  );
};

export default AccessibilityEnhancements;