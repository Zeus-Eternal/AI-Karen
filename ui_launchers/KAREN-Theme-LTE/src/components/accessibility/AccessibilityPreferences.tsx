"use client"

import React, { useState, useEffect } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';
import { useVisualAdaptations } from '@/lib/accessibility/visual-adaptations';
import { useVoiceControl } from '@/lib/accessibility/voice-control';
import { VisualPreferences } from '@/lib/accessibility/visual-adaptations';

// Accessibility preferences component
export function AccessibilityPreferences() {
  const { state, updatePreferences, resetPreferences } = useAccessibility();
  const { toggleHighContrast, toggleLargeText, toggleReducedMotion, setTextScale } = useVisualAdaptations();
  const { voiceState, toggleListening, addCommand, removeCommand } = useVoiceControl();
  
  const [activeTab, setActiveTab] = useState<'visual' | 'keyboard' | 'voice' | 'testing'>('visual');
  const [customCommands, setCustomCommands] = useState<string[]>([]);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Load custom commands from localStorage
  useEffect(() => {
    if (isClient && typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('custom-voice-commands');
        if (saved) {
          setCustomCommands(JSON.parse(saved));
        }
      } catch (error) {
        console.error('Failed to load custom voice commands:', error);
      }
    }
  }, [isClient]);

  // Save custom commands to localStorage
  useEffect(() => {
    if (isClient && typeof window !== 'undefined') {
      try {
        localStorage.setItem('custom-voice-commands', JSON.stringify(customCommands));
      } catch (error) {
        console.error('Failed to save custom voice commands:', error);
      }
    }
  }, [customCommands, isClient]);

  const handlePreferenceChange = (key: keyof typeof state.preferences, value: any) => {
    updatePreferences({ [key]: value });
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all accessibility preferences to default?')) {
      resetPreferences();
      setCustomCommands([]);
    }
  };

  const exportPreferences = () => {
    if (!isClient) return;
    
    const preferences = {
      ...state.preferences,
      customCommands,
    };
    
    const blob = new Blob([JSON.stringify(preferences, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'accessibility-preferences.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const importPreferences = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const preferences = JSON.parse(e.target?.result as string);
        updatePreferences(preferences);
        if (preferences.customCommands) {
          setCustomCommands(preferences.customCommands);
        }
      } catch (error) {
        alert('Failed to import preferences. Please check the file format.');
      }
    };
    reader.readAsText(file);
  };

  return React.createElement('div', {
    className: 'accessibility-preferences',
    role: 'region',
    'aria-label': 'Accessibility preferences',
  }, [
    // Header
    React.createElement('div', { key: 'header', className: 'preferences-header' }, [
      React.createElement('h2', null, 'Accessibility Preferences'),
      React.createElement('p', { className: 'preferences-description' },
        'Customize your accessibility experience with these preferences.'
      ),
    ]),

    // Tab navigation
    React.createElement('div', { key: 'tabs', className: 'preference-tabs', role: 'tablist' }, [
      React.createElement('button', {
        key: 'visual',
        role: 'tab',
        'aria-selected': activeTab === 'visual',
        'aria-controls': 'visual-panel',
        onClick: () => setActiveTab('visual'),
        className: `tab-button ${activeTab === 'visual' ? 'active' : ''}`,
      }, 'Visual'),
      
      React.createElement('button', {
        key: 'keyboard',
        role: 'tab',
        'aria-selected': activeTab === 'keyboard',
        'aria-controls': 'keyboard-panel',
        onClick: () => setActiveTab('keyboard'),
        className: `tab-button ${activeTab === 'keyboard' ? 'active' : ''}`,
      }, 'Keyboard'),
      
      React.createElement('button', {
        key: 'voice',
        role: 'tab',
        'aria-selected': activeTab === 'voice',
        'aria-controls': 'voice-panel',
        onClick: () => setActiveTab('voice'),
        className: `tab-button ${activeTab === 'voice' ? 'active' : ''}`,
      }, 'Voice'),
      
      React.createElement('button', {
        key: 'testing',
        role: 'tab',
        'aria-selected': activeTab === 'testing',
        'aria-controls': 'testing-panel',
        onClick: () => setActiveTab('testing'),
        className: `tab-button ${activeTab === 'testing' ? 'active' : ''}`,
      }, 'Testing'),
    ]),

    // Tab panels
    React.createElement('div', { key: 'panels', className: 'preference-panels' }, [
      // Visual preferences panel
      activeTab === 'visual' && React.createElement('div', {
        key: 'visual-panel',
        id: 'visual-panel',
        role: 'tabpanel',
        'aria-labelledby': 'visual-tab',
        className: 'preference-panel',
      }, [
        React.createElement(VisualPreferences, { key: 'visual-prefs' }),
      ]),

      // Keyboard preferences panel
      activeTab === 'keyboard' && React.createElement('div', {
        key: 'keyboard-panel',
        id: 'keyboard-panel',
        role: 'tabpanel',
        'aria-labelledby': 'keyboard-tab',
        className: 'preference-panel',
      }, [
        React.createElement('h3', null, 'Keyboard Navigation'),
        
        React.createElement('div', { className: 'preference-group' }, [
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.keyboardNavigation,
              onChange: (e) => handlePreferenceChange('keyboardNavigation', e.target.checked),
            }),
            React.createElement('span', null, 'Enable keyboard navigation'),
          ]),
          
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.skipLinks,
              onChange: (e) => handlePreferenceChange('skipLinks', e.target.checked),
            }),
            React.createElement('span', null, 'Show skip links'),
          ]),
          
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.focusVisible,
              onChange: (e) => handlePreferenceChange('focusVisible', e.target.checked),
            }),
            React.createElement('span', null, 'Show focus indicators'),
          ]),
        ]),
        
        React.createElement('div', { className: 'keyboard-shortcuts' }, [
          React.createElement('h4', null, 'Keyboard Shortcuts'),
          React.createElement('ul', { className: 'shortcut-list' }, [
            React.createElement('li', { key: 'alt-a' }, 'Alt + A: Toggle accessibility menu'),
            React.createElement('li', { key: 'alt-h' }, 'Alt + H: Toggle high contrast'),
            React.createElement('li', { key: 'alt-l' }, 'Alt + L: Toggle large text'),
            React.createElement('li', { key: 'alt-m' }, 'Alt + M: Toggle reduced motion'),
            React.createElement('li', { key: 'alt-v' }, 'Alt + V: Toggle voice control'),
            React.createElement('li', { key: 'alt-s' }, 'Alt + S: Skip to main content'),
            React.createElement('li', { key: 'alt-n' }, 'Alt + N: Navigate to navigation'),
            React.createElement('li', { key: 'alt-f' }, 'Alt + F: Navigate to search'),
          ]),
        ]),
      ]),

      // Voice preferences panel
      activeTab === 'voice' && React.createElement('div', {
        key: 'voice-panel',
        id: 'voice-panel',
        role: 'tabpanel',
        'aria-labelledby': 'voice-tab',
        className: 'preference-panel',
      }, [
        React.createElement('h3', null, 'Voice Control'),
        
        React.createElement('div', { className: 'preference-group' }, [
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.voiceControl,
              onChange: (e) => handlePreferenceChange('voiceControl', e.target.checked),
            }),
            React.createElement('span', null, 'Enable voice control'),
          ]),
          
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.voiceCommands,
              onChange: (e) => handlePreferenceChange('voiceCommands', e.target.checked),
            }),
            React.createElement('span', null, 'Enable voice commands'),
          ]),
        ]),
        
        React.createElement('div', { className: 'voice-status' }, [
          React.createElement('h4', null, 'Voice Control Status'),
          React.createElement('div', { className: 'status-indicator' }, [
            React.createElement('span', {
              className: `status-dot ${voiceState.isListening ? 'active' : 'inactive'}`,
              'aria-label': voiceState.isListening ? 'Voice control is listening' : 'Voice control is not listening',
            }),
            React.createElement('span', { className: 'status-text' },
              voiceState.isListening ? 'Listening...' : 'Not listening'
            ),
          ]),
          
          React.createElement('button', {
            onClick: toggleListening,
            className: 'voice-toggle-button',
            'aria-pressed': voiceState.isListening,
          }, voiceState.isListening ? 'Stop Listening' : 'Start Listening'),
          
          voiceState.error && React.createElement('div', {
            className: 'voice-error',
            role: 'alert',
          }, voiceState.error),
        ]),
        
        React.createElement('div', { className: 'voice-commands-list' }, [
          React.createElement('h4', null, 'Available Voice Commands'),
          React.createElement('ul', { className: 'commands-list' },
            voiceState.availableCommands.map(command =>
              React.createElement('li', {
                key: command.id,
                className: `command-item ${command.enabled ? 'enabled' : 'disabled'}`,
              }, [
                React.createElement('div', { className: 'command-info' }, [
                  React.createElement('span', { className: 'command-name' }, command.description),
                  React.createElement('span', { className: 'command-category' }, command.category),
                ]),
                React.createElement('div', { className: 'command-phrases' },
                  command.phrases.map((phrase, index) =>
                    React.createElement('code', { key: index }, phrase)
                  )
                ),
              ])
            )
          ),
        ]),
      ]),

      // Testing preferences panel
      activeTab === 'testing' && React.createElement('div', {
        key: 'testing-panel',
        id: 'testing-panel',
        role: 'tabpanel',
        'aria-labelledby': 'testing-tab',
        className: 'preference-panel',
      }, [
        React.createElement('h3', null, 'Accessibility Testing'),
        
        React.createElement('div', { className: 'preference-group' }, [
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.accessibilityTesting,
              onChange: (e) => handlePreferenceChange('accessibilityTesting', e.target.checked),
            }),
            React.createElement('span', null, 'Enable accessibility testing'),
          ]),
          
          React.createElement('label', { className: 'preference-item' }, [
            React.createElement('input', {
              type: 'checkbox',
              checked: state.preferences.showAccessibilityMenu,
              onChange: (e) => handlePreferenceChange('showAccessibilityMenu', e.target.checked),
            }),
            React.createElement('span', null, 'Show accessibility menu'),
          ]),
        ]),
        
        React.createElement('div', { className: 'testing-tools' }, [
          React.createElement('h4', null, 'Testing Tools'),
          React.createElement('p', null,
            'Use the accessibility testing dashboard to run comprehensive tests and identify issues.'
          ),
          React.createElement('button', {
            onClick: () => {
              // This would open the testing dashboard
              console.log('Opening accessibility testing dashboard...');
            },
            className: 'testing-button',
          }, 'Open Testing Dashboard'),
        ]),
      ]),
    ]),

    // Actions
    React.createElement('div', { key: 'actions', className: 'preference-actions' }, [
      React.createElement('div', { className: 'action-group' }, [
        React.createElement('button', {
          onClick: exportPreferences,
          className: 'action-button export',
        }, 'Export Preferences'),
        
        React.createElement('label', { className: 'action-button import' }, [
          React.createElement('span', null, 'Import Preferences'),
          React.createElement('input', {
            type: 'file',
            accept: '.json',
            onChange: importPreferences,
            style: { display: 'none' },
          }),
        ]),
      ]),
      
      React.createElement('button', {
        onClick: handleReset,
        className: 'action-button reset',
      }, 'Reset to Default'),
    ]),
  ]);
}

export default AccessibilityPreferences;