/**
 * ESLint Accessibility Configuration
 * 
 * This configuration extends the main ESLint config with accessibility-specific rules
 * to catch common accessibility issues during development.
 */

module.exports = {
  extends: [
    'plugin:jsx-a11y/recommended'
  ],
  plugins: [
    'jsx-a11y'
  ],
  rules: {
    // JSX Accessibility Rules
    'jsx-a11y/accessible-emoji': 'error',
    'jsx-a11y/alt-text': 'error',
    'jsx-a11y/anchor-has-content': 'error',
    'jsx-a11y/anchor-is-valid': 'error',
    'jsx-a11y/aria-activedescendant-has-tabindex': 'error',
    'jsx-a11y/aria-props': 'error',
    'jsx-a11y/aria-proptypes': 'error',
    'jsx-a11y/aria-role': 'error',
    'jsx-a11y/aria-unsupported-elements': 'error',
    'jsx-a11y/autocomplete-valid': 'error',
    'jsx-a11y/click-events-have-key-events': 'error',
    'jsx-a11y/control-has-associated-label': 'error',
    'jsx-a11y/heading-has-content': 'error',
    'jsx-a11y/html-has-lang': 'error',
    'jsx-a11y/iframe-has-title': 'error',
    'jsx-a11y/img-redundant-alt': 'error',
    'jsx-a11y/label-has-associated-control': 'error',
    'jsx-a11y/lang': 'error',
    'jsx-a11y/media-has-caption': 'error',
    'jsx-a11y/mouse-events-have-key-events': 'error',
    'jsx-a11y/no-access-key': 'error',
    'jsx-a11y/no-distracting-elements': 'error',
    'jsx-a11y/no-interactive-element-to-noninteractive-role': 'error',
    'jsx-a11y/no-noninteractive-element-interactions': 'error',
    'jsx-a11y/no-noninteractive-element-to-interactive-role': 'error',
    'jsx-a11y/no-noninteractive-tabindex': 'error',
    'jsx-a11y/no-onchange': 'error',
    'jsx-a11y/no-redundant-roles': 'error',
    'jsx-a11y/no-static-element-interactions': 'error',
    'jsx-a11y/role-has-required-aria-props': 'error',
    'jsx-a11y/role-supports-aria-props': 'error',
    'jsx-a11y/scope': 'error',
    'jsx-a11y/tabindex-no-positive': 'error',

    // Custom accessibility rules
    'jsx-a11y/label-has-for': ['error', {
      'required': {
        'some': ['nesting', 'id']
      }
    }],
    
    // Additional accessibility rules
    'jsx-a11y/anchor-ambiguous-text': 'warn',
    'jsx-a11y/prefer-tag-over-role': 'warn',
    
    // Focus management
    'jsx-a11y/no-autofocus': ['error', { 
      ignoreNonDOM: true 
    }],
    
    // Interactive elements
    'jsx-a11y/interactive-supports-focus': ['error', {
      tabbable: [
        'button',
        'checkbox',
        'link',
        'searchbox',
        'spinbutton',
        'switch',
        'textbox'
      ]
    }],
    
    // Keyboard navigation
    
    // Semantic HTML
    
    // Media accessibility
    
    // Table accessibility
    'jsx-a11y/table-has-caption': 'warn'
  },
  
  settings: {
    'jsx-a11y': {
      polymorphicPropName: 'as',
      components: {
        // Map custom components to their semantic equivalents
        'Button': 'button',
        'Link': 'a',
        'Input': 'input',
        'TextArea': 'textarea',
        'Select': 'select',
        'Card': 'div',
        'Modal': 'dialog',
        'Form': 'form',
        'GridContainer': 'div',
        'FlexContainer': 'div',
        'ResponsiveContainer': 'div',
        'InteractiveButton': 'button',
        'InteractiveInput': 'input',
        'AriaEnhancedButton': 'button',
        'AriaEnhancedInput': 'input',
        'AriaEnhancedForm': 'form'
      }
    }
  },
  
  overrides: [
    {
      // Storybook files can have some relaxed rules
      files: ['**/*.stories.@(ts|tsx|js|jsx)'],
      rules: {
        'jsx-a11y/no-autofocus': 'off',
        'jsx-a11y/tabindex-no-positive': 'warn'
      }
    },
    {
      // Test files can have some relaxed rules
      files: ['**/*.test.@(ts|tsx|js|jsx)', '**/__tests__/**/*'],
      rules: {
        'jsx-a11y/no-autofocus': 'off',
        'jsx-a11y/click-events-have-key-events': 'warn',
        'jsx-a11y/no-static-element-interactions': 'warn'
      }
    }
  ]
};