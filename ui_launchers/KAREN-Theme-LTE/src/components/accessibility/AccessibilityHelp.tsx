"use client"

import React, { useState, useEffect } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// Help topic interface
interface HelpTopic {
  id: string;
  title: string;
  category: 'getting-started' | 'keyboard' | 'screen-reader' | 'voice' | 'visual' | 'testing' | 'troubleshooting';
  content: string;
  relatedTopics?: string[];
  shortcuts?: Array<{ key: string; description: string }>;
  videoUrl?: string;
  transcript?: string;
}

// Help content data
const HELP_CONTENT: HelpTopic[] = [
  {
    id: 'getting-started',
    title: 'Getting Started with Accessibility',
    category: 'getting-started',
    content: `
      Welcome to the Karen AI accessibility system! This comprehensive suite of tools is designed to make the application accessible to all users, including those with disabilities.
      
      Key features include:
      • Keyboard navigation support
      • Screen reader compatibility
      • Voice control capabilities
      • High contrast and large text modes
      • Accessibility testing tools
      
      To get started, press Alt+A to open the accessibility menu, or navigate to the Accessibility section in your settings.
    `,
    relatedTopics: ['keyboard-navigation', 'screen-reader-basics', 'visual-adaptations'],
  },
  {
    id: 'keyboard-navigation',
    title: 'Keyboard Navigation',
    category: 'keyboard',
    content: `
      Navigate the entire application using your keyboard without needing a mouse.
      
      Basic Navigation:
      • Tab: Move to next focusable element
      • Shift+Tab: Move to previous focusable element
      • Enter/Space: Activate focused element
      • Arrow Keys: Navigate within menus, lists, and grids
      • Escape: Close dialogs or cancel actions
      
      Global Shortcuts:
      • Alt+S: Skip to main content
      • Alt+N: Navigate to navigation menu
      • Alt+F: Navigate to search field
      • Alt+H: Navigate to help section
      • Alt+A: Toggle accessibility menu
    `,
    shortcuts: [
      { key: 'Tab', description: 'Move to next element' },
      { key: 'Shift+Tab', description: 'Move to previous element' },
      { key: 'Enter/Space', description: 'Activate focused element' },
      { key: 'Arrow Keys', description: 'Navigate within components' },
      { key: 'Escape', description: 'Close dialogs/cancel' },
      { key: 'Alt+S', description: 'Skip to main content' },
      { key: 'Alt+N', description: 'Navigate to navigation' },
      { key: 'Alt+F', description: 'Navigate to search' },
      { key: 'Alt+H', description: 'Navigate to help' },
      { key: 'Alt+A', description: 'Toggle accessibility menu' },
    ],
    relatedTopics: ['focus-management', 'screen-reader-basics'],
  },
  {
    id: 'screen-reader-basics',
    title: 'Screen Reader Support',
    category: 'screen-reader',
    content: `
      This application is fully compatible with screen readers like JAWS, NVDA, and VoiceOver.
      
      Screen Reader Features:
      • All interactive elements have proper labels and descriptions
      • Page structure uses semantic HTML for easy navigation
      • Live regions announce dynamic content changes
      • Forms have proper labeling and error announcements
      • Data tables include headers and captions
      
      Navigation Tips:
      • Use heading navigation (H key in most screen readers) to jump between sections
      • Use landmark navigation to quickly find main content, navigation, or search
      • Use list navigation (L key) to navigate lists and menus
      • Use form field navigation (F key) to jump between form controls
    `,
    relatedTopics: ['keyboard-navigation', 'voice-control', 'testing-tools'],
  },
  {
    id: 'voice-control',
    title: 'Voice Control',
    category: 'voice',
    content: `
      Control the application using your voice with built-in speech recognition.
      
      Getting Started:
      1. Press Alt+V or click the microphone button to start voice control
      2. Allow microphone access when prompted
      3. Speak commands clearly and wait for confirmation
      
      Available Commands:
      • "Go home" - Navigate to the home page
      • "Go back" - Navigate to previous page
      • "Scroll up/down" - Scroll the page
      • "Click button" - Activate focused button
      • "Open link" - Follow focused link
      • "Submit form" - Submit the current form
      • "Toggle high contrast" - Enable/disable high contrast mode
      • "Voice help" - Hear all available commands
      
      Tips:
      • Speak clearly and at a moderate pace
      • Minimize background noise
      • Use the exact command phrases
      • Wait for the "Listening..." indicator before speaking
    `,
    relatedTopics: ['keyboard-navigation', 'visual-adaptations'],
  },
  {
    id: 'visual-adaptations',
    title: 'Visual Adaptations',
    category: 'visual',
    content: `
      Customize the visual appearance to match your needs and preferences.
      
      High Contrast Mode:
      • Increases color contrast for better visibility
      • Uses high-contrast color combinations
      • Helps users with low vision or color blindness
      • Toggle with Alt+H or in accessibility preferences
      
      Large Text Mode:
      • Increases text size by 25%
      • Maintains readable proportions and spacing
      • Helps users with low vision
      • Toggle with Alt+L or in accessibility preferences
      
      Reduced Motion:
      • Disables animations and transitions
      • Helps users with vestibular disorders
      • Reduces distraction for cognitive disabilities
      • Toggle with Alt+M or in accessibility preferences
      
      Text Scaling:
      • Choose from multiple text size levels
      • Ranges from 0.875x to 2.0x normal size
      • Adjusts all text proportionally
      • Found in accessibility preferences
    `,
    relatedTopics: ['color-contrast', 'getting-started'],
  },
  {
    id: 'color-contrast',
    title: 'Color Contrast Checker',
    category: 'visual',
    content: `
      Use the built-in color contrast checker to ensure your custom themes meet WCAG standards.
      
      WCAG Requirements:
      • AA Level: 4.5:1 for normal text, 3:1 for large text
      • AAA Level: 7:1 for normal text, 4.5:1 for large text
      • Large text is 18pt+ or 14pt+ bold
      
      How to Use:
      1. Open the color contrast checker from accessibility preferences
      2. Enter foreground and background colors
      3. Check if the contrast ratio meets requirements
      4. Adjust colors as needed
      
      Tips:
      • Avoid using color alone to convey information
      • Ensure sufficient contrast for all interactive elements
      • Test with different types of color blindness
      • Consider using high contrast mode for better visibility
    `,
    relatedTopics: ['visual-adaptations', 'testing-tools'],
  },
  {
    id: 'testing-tools',
    title: 'Accessibility Testing Tools',
    category: 'testing',
    content: `
      Built-in tools help you test and validate accessibility compliance.
      
      Available Tests:
      • Quick Test: Fast check for common issues
      • Comprehensive Test: Full WCAG 2.1 AA compliance check
      • Component Test: Test specific components or sections
      • Color Contrast: Verify color combinations meet standards
      
      Test Results:
      • Detailed violation reports with WCAG criteria references
      • Priority levels (critical, serious, moderate, minor)
      • Specific recommendations for fixes
      • Compliance score calculation
      
      Best Practices:
      • Test early and often during development
      • Test with real assistive technology
      • Test with keyboard only
      • Test with screen readers
      • Test with different zoom levels
      • Include users with disabilities in testing
    `,
    relatedTopics: ['troubleshooting', 'screen-reader-basics'],
  },
  {
    id: 'troubleshooting',
    title: 'Troubleshooting',
    category: 'troubleshooting',
    content: `
      Common issues and solutions for accessibility features.
      
      Voice Control Not Working:
      • Check microphone permissions in browser settings
      • Ensure microphone is not muted
      • Try a different browser (Chrome, Firefox, Edge recommended)
      • Check for conflicting microphone applications
      
      Keyboard Navigation Issues:
      • Ensure Tab order is logical
      • Check for custom tabindex values
      • Verify all interactive elements are focusable
      • Test with different keyboard layouts
      
      Screen Reader Problems:
      • Update screen reader software
      • Check browser compatibility with screen reader
      • Verify ARIA labels are present
      • Test with different screen readers
      
      Visual Adaptations Not Applying:
      • Clear browser cache and cookies
      • Check JavaScript is enabled
      • Try disabling browser extensions
      • Test in incognito/private mode
      
      Performance Issues:
      • Disable unused accessibility features
      • Reduce text scaling if set very high
      • Close other browser tabs
      • Check device specifications
    `,
    relatedTopics: ['getting-started', 'testing-tools'],
  },
];

// Accessibility help component
export function AccessibilityHelp() {
  const { state, announceToScreenReader } = useAccessibility();
  const [selectedTopic, setSelectedTopic] = useState<HelpTopic | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTopics, setFilteredTopics] = useState<HelpTopic[]>(HELP_CONTENT);
  const [showTranscript, setShowTranscript] = useState(false);

  // Filter topics based on search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTopics(HELP_CONTENT);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = HELP_CONTENT.filter(topic =>
      topic.title.toLowerCase().includes(query) ||
      topic.content.toLowerCase().includes(query) ||
      topic.category.toLowerCase().includes(query)
    );
    
    setFilteredTopics(filtered);
  }, [searchQuery]);

  // Handle topic selection
  const handleTopicSelect = (topic: HelpTopic) => {
    setSelectedTopic(topic);
    setShowTranscript(false);
    announceToScreenReader(`Loading help for: ${topic.title}`);
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setSelectedTopic(null);
      setShowTranscript(false);
    }
  };

  // Render shortcuts list
  const renderShortcuts = (shortcuts?: Array<{ key: string; description: string }>) => {
    if (!shortcuts) return null;

    return React.createElement('div', { className: 'shortcuts-list' }, [
      React.createElement('h4', null, 'Keyboard Shortcuts'),
      React.createElement('ul', null,
        shortcuts.map((shortcut, index) =>
          React.createElement('li', { key: index }, [
            React.createElement('kbd', { className: 'shortcut-key' }, shortcut.key),
            React.createElement('span', { className: 'shortcut-description' }, shortcut.description),
          ])
        )
      ),
    ]);
  };

  // Render related topics
  const renderRelatedTopics = (relatedTopicIds?: string[]) => {
    if (!relatedTopicIds) return null;

    const relatedTopics = relatedTopicIds
      .map(id => HELP_CONTENT.find(topic => topic.id === id))
      .filter(Boolean) as HelpTopic[];

    if (relatedTopics.length === 0) return null;

    return React.createElement('div', { className: 'related-topics' }, [
      React.createElement('h4', null, 'Related Topics'),
      React.createElement('ul', null,
        relatedTopics.map(topic =>
          React.createElement('li', { key: topic.id },
            React.createElement('button', {
              className: 'related-topic-button',
              onClick: () => handleTopicSelect(topic),
            }, topic.title)
          )
        )
      ),
    ]);
  };

  return React.createElement('div', {
    className: 'accessibility-help',
    role: 'region',
    'aria-label': 'Accessibility help and guidance',
    onKeyDown: handleKeyDown,
  }, [
    // Header
    React.createElement('div', { className: 'help-header' }, [
      React.createElement('h2', null, 'Accessibility Help'),
      
      // Search
      React.createElement('div', { className: 'help-search' }, [
        React.createElement('label', { htmlFor: 'help-search' }, 'Search Help:'),
        React.createElement('input', {
          id: 'help-search',
          type: 'text',
          value: searchQuery,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value),
          placeholder: 'Search for help topics...',
          'aria-describedby': 'search-results-info',
        }),
        React.createElement('div', {
          id: 'search-results-info',
          className: 'search-info',
          'aria-live': 'polite',
        }, `${filteredTopics.length} topic${filteredTopics.length !== 1 ? 's' : ''} found`),
      ]),
    ]),

    // Main content area
    React.createElement('div', { className: 'help-content' }, [
      // Topic list
      !selectedTopic && React.createElement('div', { className: 'topic-list' }, [
        React.createElement('h3', null, 'Help Topics'),
        React.createElement('div', { className: 'topic-categories' },
          Object.entries(
            HELP_CONTENT.reduce((acc, topic) => {
              if (!acc[topic.category]) acc[topic.category] = [];
              (acc[topic.category] ??= []).push(topic);
              return acc;
            }, {} as Record<string, HelpTopic[]>)
          ).map(([category, topics]) =>
            React.createElement('div', { key: category, className: 'category-section' }, [
              React.createElement('h4', { className: 'category-title' },
                category.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
              ),
              React.createElement('ul', { className: 'category-topics' },
                topics.map(topic =>
                  React.createElement('li', { key: topic.id },
                    React.createElement('button', {
                      className: 'topic-button',
                      onClick: () => handleTopicSelect(topic),
                      'aria-describedby': `topic-desc-${topic.id}`,
                    }, [
                      React.createElement('span', { className: 'topic-title' }, topic.title),
                      React.createElement('span', {
                        id: `topic-desc-${topic.id}`,
                        className: 'topic-description',
                      }, topic.content.slice(0, 100) + '...'),
                    ])
                  )
                )
              )
            ])
          )
        ),
      ]),

      // Selected topic content
      selectedTopic && React.createElement('div', {
        className: 'topic-content',
        role: 'article',
        'aria-label': selectedTopic.title,
      }, [
        React.createElement('button', {
          className: 'back-button',
          onClick: () => setSelectedTopic(null),
          'aria-label': 'Back to topic list',
        }, '← Back to Topics'),
        
        React.createElement('h3', null, selectedTopic.title),
        
        React.createElement('div', {
          className: 'topic-text',
          dangerouslySetInnerHTML: { __html: selectedTopic.content.replace(/\n/g, '<br>') },
        }),
        
        // Shortcuts
        renderShortcuts(selectedTopic.shortcuts),
        
        // Video content
        selectedTopic.videoUrl && React.createElement('div', { className: 'video-section' }, [
          React.createElement('h4', null, 'Video Tutorial'),
          React.createElement('div', { className: 'video-container' }, [
            React.createElement('video', {
              controls: true,
              className: 'help-video',
              'aria-label': `Video tutorial for ${selectedTopic.title}`,
            }, [
              React.createElement('source', { src: selectedTopic.videoUrl, type: 'video/mp4' }),
              React.createElement('p', null, 'Your browser does not support the video tag.'),
            ]),
            
            // Transcript toggle
            React.createElement('button', {
              className: 'transcript-toggle',
              onClick: () => setShowTranscript(!showTranscript),
              'aria-expanded': showTranscript,
              'aria-controls': 'video-transcript',
            }, showTranscript ? 'Hide Transcript' : 'Show Transcript'),
          ]),
          
          // Transcript
          showTranscript && selectedTopic.transcript && React.createElement('div', {
            id: 'video-transcript',
            className: 'video-transcript',
          }, [
            React.createElement('h4', null, 'Video Transcript'),
            React.createElement('p', null, selectedTopic.transcript),
          ]),
        ]),
        
        // Related topics
        renderRelatedTopics(selectedTopic.relatedTopics),
      ]),
    ]),
  ]);
}

export default AccessibilityHelp;