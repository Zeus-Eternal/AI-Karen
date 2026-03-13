/**
 * Accessibility Hooks for Easy Integration
 * Comprehensive hooks for integrating accessibility features into components
 */

'use client';

import { useEffect, useCallback, useRef, useState } from 'react';
import { useAccessibility as useAccessibilityContext } from '@/contexts/AccessibilityContext';

// Simple accessible component hook
export function useAccessibleComponent(): {
  elementRef: React.RefObject<HTMLElement>;
  isFocused: boolean;
  focus: () => void;
  announce: (message: string) => void;
} {
  const elementRef = useRef<HTMLElement>(null);
  const { announceToScreenReader } = useAccessibilityContext();
  const [isFocused, setIsFocused] = useState<boolean>(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleFocus = () => setIsFocused(true);
    const handleBlur = () => setIsFocused(false);

    element.addEventListener('focus', handleFocus);
    element.addEventListener('blur', handleBlur);

    return () => {
      element.removeEventListener('focus', handleFocus);
      element.removeEventListener('blur', handleBlur);
    };
  }, []);

  return {
    elementRef,
    isFocused,
    focus: () => {
      if (elementRef.current) {
        elementRef.current.focus();
      }
    },
    announce: (message: string) => {
      announceToScreenReader(message);
    },
  };
}

// Simple accessible form hook
export function useAccessibleForm(): {
  formRef: React.RefObject<HTMLFormElement>;
  errors: Record<string, string>;
  isSubmitting: boolean;
  validateForm: () => boolean;
  handleSubmit: (event?: React.FormEvent) => Promise<void>;
  clearErrors: () => void;
  setFieldError: (field: string, error: string) => void;
} {
  const formRef = useRef<HTMLFormElement>(null);
  const { announceToScreenReader } = useAccessibilityContext();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const validateForm = useCallback(() => {
    if (!formRef.current) return true;

    const form = formRef.current;
    const formData = new FormData(form);
    const newErrors: Record<string, string> = {};

    // Basic validation
    const formDataEntries: Array<[string, FormDataEntryValue]> = [];
    formData.forEach((value, key) => {
      formDataEntries.push([key, value]);
    });
    
    for (const [key, value] of formDataEntries) {
      const input = form.querySelector(`[name="${key}"]`) as HTMLInputElement;
      
      if (input && input.required && !value) {
        newErrors[key] = `${input.name} is required`;
      }
      
      if (input && input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value.toString())) {
          newErrors[key] = 'Please enter a valid email address';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, []);

  const handleSubmit = useCallback(async (event?: React.FormEvent): Promise<void> => {
    if (event) {
      event.preventDefault();
    }

    if (!formRef.current) return;

    const isValid = validateForm();
    if (!isValid) {
      announceToScreenReader('Please fix form errors before submitting');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const formData = new FormData(formRef.current);
      const formDataEntries: Array<[string, FormDataEntryValue]> = [];
      formData.forEach((value, key) => {
        formDataEntries.push([key, value]);
      });
      console.log('Form submitted:', Object.fromEntries(formDataEntries));
      
      announceToScreenReader('Form submitted successfully');
      formRef.current.reset();
      setErrors({});
    } catch (error) {
      console.error('Form submission error:', error);
      announceToScreenReader('Form submission failed');
    } finally {
      setIsSubmitting(false);
    }
  }, [validateForm, announceToScreenReader]);

  return {
    formRef,
    errors,
    isSubmitting,
    validateForm,
    handleSubmit,
    clearErrors: () => setErrors({}),
    setFieldError: (field: string, error: string) => {
      setErrors(prev => ({ ...prev, [field]: error }));
    },
  };
}

// Simple keyboard navigation hook
export function useKeyboardNavigation(): {
  focusNext: () => void;
  focusPrevious: () => void;
} {
  const { announceToScreenReader }: { announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void } = useAccessibilityContext();
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'Tab':
        // Handle tab navigation
        setTimeout(() => {
          const focusableElements = document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as NodeListOf<HTMLElement>;
          
          const currentIndex = Array.from(focusableElements).indexOf(document.activeElement as HTMLElement);
          const nextIndex = event.shiftKey 
            ? (currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1)
            : (currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0);
          
          if (focusableElements[nextIndex]) {
            focusableElements[nextIndex].focus();
          }
        }, 0);
        break;
        
      case 'Enter':
        // Handle enter key
        const activeElement = document.activeElement as HTMLElement;
        if (activeElement && (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button')) {
          activeElement.click();
        }
        break;
        
      case 'Escape':
        // Handle escape key
        announceToScreenReader('Action cancelled');
        break;
    }
  }, [announceToScreenReader]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  return {
    focusNext: () => {
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as NodeListOf<HTMLElement>;
      
      const currentIndex = Array.from(focusableElements).indexOf(document.activeElement as HTMLElement);
      const nextIndex = currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0;
      
      if (focusableElements[nextIndex]) {
        focusableElements[nextIndex].focus();
      }
    },
    focusPrevious: () => {
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as NodeListOf<HTMLElement>;
      
      const currentIndex = Array.from(focusableElements).indexOf(document.activeElement as HTMLElement);
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1;
      
      if (focusableElements[prevIndex]) {
        focusableElements[prevIndex].focus();
      }
    },
  };
}

// Simple screen reader hook
export function useScreenReader(): {
  isScreenReaderActive: boolean;
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
} {
  const { announceToScreenReader }: { announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void } = useAccessibilityContext();
  const [isScreenReaderActive, setIsScreenReaderActive] = useState<boolean>(false);

  useEffect(() => {
    // Detect screen reader
    const detectScreenReader = () => {
      // Basic detection
      if ('speechSynthesis' in window) {
        const synth = window.speechSynthesis;
        if (synth.getVoices().length > 0) {
          setIsScreenReaderActive(true);
        }
      }
    };

    detectScreenReader();
    
    // Listen for voice changes
    if ('speechSynthesis' in window) {
      window.speechSynthesis.addEventListener('voiceschanged', detectScreenReader);
    }

    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.removeEventListener('voiceschanged', detectScreenReader);
      }
    };
  }, []);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announceToScreenReader(message, priority);
  }, [announceToScreenReader]);

  return {
    isScreenReaderActive,
    announce,
  };
}

// Main accessibility hook that combines all features
export function useAccessibility() {
  const accessibilityContext = useAccessibilityContext();
  const accessibleComponent = useAccessibleComponent();
  const accessibleForm = useAccessibleForm();
  const keyboardNavigation = useKeyboardNavigation();
  const screenReader = useScreenReader();

  return {
    // All context properties
    ...accessibilityContext,
    
    // Component features
    ...accessibleComponent,
    
    // Form features
    ...accessibleForm,
    
    // Keyboard navigation
    ...keyboardNavigation,
    
    // Screen reader
    ...screenReader,
    
    // Utility functions
    // Utility functions would be implemented here
  };
}
export default useAccessibility;
