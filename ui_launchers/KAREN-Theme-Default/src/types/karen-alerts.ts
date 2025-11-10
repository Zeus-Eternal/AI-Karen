/**
 * Enhanced Alert Type Definitions for Karen's Graceful Alert System
 * 
 * This file contains all the TypeScript interfaces and type definitions
 * for Karen's comprehensive alert system that replaces browser native alerts
 * with user-friendly, contextually appropriate notifications.
 */

import * as React from "react";

/**
 * Core alert types that categorize different kinds of alerts
 */
export type AlertType = 
  | 'system'        // System-level messages and updates
  | 'performance'   // Performance monitoring alerts
  | 'health'        // Health monitoring alerts
  | 'user-action'   // User action confirmations and feedback
  | 'validation'    // Form validation and input errors
  | 'success'       // Success confirmations
  | 'info';         // General informational messages

/**
 * Karen-specific alert variants that define visual styling and tone
 */
export type AlertVariant = 
  | 'karen-success'    // Green with celebration - for positive outcomes
  | 'karen-info'       // Blue with friendly tone - for informational messages
  | 'karen-warning'    // Amber with helpful guidance - for cautionary messages
  | 'karen-error'      // Red but still friendly - for error messages
  | 'karen-system';    // Purple for system messages - for system-level notifications

/**
 * Priority levels that determine alert display behavior and urgency
 */
export type AlertPriority = 'low' | 'normal' | 'high' | 'critical';

/**
 * Interactive action button interface for alerts
 */
export interface AlertAction {
  /** Display label for the action button */
  label: string;
  /** Function to execute when action is clicked */
  action: () => void | Promise<void>;
  /** Visual variant of the action button */
  variant?: 'default' | 'destructive' | 'outline';
  /** Optional icon to display with the action */
  icon?: React.ReactNode;
  /** Accessible description when rendered as a toast action */
  altText?: string;
}

/**
 * Core Karen Alert interface with all required properties
 */
export interface KarenAlert {
  /** Unique identifier for the alert */
  id: string;
  /** Type categorization of the alert */
  type: AlertType;
  /** Visual variant that determines styling and tone */
  variant: AlertVariant;
  /** Main title/heading of the alert */
  title: string;
  /** Primary message content */
  message: string;
  /** Optional emoji to enhance the message tone */
  emoji?: string;
  /** Priority level affecting display behavior */
  priority: AlertPriority;
  /** Custom duration in milliseconds (overrides default for variant) */
  duration?: number;
  /** Interactive action buttons */
  actions?: AlertAction[];
  /** Expandable content for detailed information */
  expandableContent?: React.ReactNode;
  /** Additional metadata for tracking and context */
  metadata?: Record<string, any>;
  /** Timestamp when alert was created */
  timestamp: number;
  /** Source component or service that triggered the alert */
  source: string;
}

/**
 * User preferences and configuration for alert behavior
 */
export interface AlertSettings {
  /** Duration settings for different alert types */
  durations: {
    success: number;
    info: number;
    warning: number;
    error: number;
    system: number;
  };
  
  /** General behavior settings */
  maxConcurrentAlerts: number;
  enableSounds: boolean;
  enableAnimations: boolean;
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  
  /** Category-specific toggles */
  categories: {
    performance: boolean;
    health: boolean;
    system: boolean;
    validation: boolean;
  };
  
  /** Accessibility preferences */
  announceAlerts: boolean;
  highContrastMode: boolean;
  reducedMotion: boolean;
}

/**
 * Alert history management interface
 */
export interface AlertHistory {
  /** Array of stored alerts */
  alerts: StoredAlert[];
  /** Maximum number of alerts to keep in history */
  maxHistory: number;
  /** Number of days to retain alert history */
  retentionDays: number;
}

/**
 * Stored alert with additional tracking information
 */
export interface StoredAlert extends KarenAlert {
  /** Whether the alert was dismissed by user */
  dismissed: boolean;
  /** Timestamp when alert was dismissed */
  dismissedAt?: number;
  /** Number of times user interacted with the alert */
  interactionCount: number;
  /** Timestamp of last user interaction */
  lastInteraction?: number;
}

/**
 * Alert system metrics and analytics
 */
export interface AlertMetrics {
  /** Total number of alerts shown */
  totalShown: number;
  /** Total number of alerts dismissed */
  totalDismissed: number;
  /** Average time alerts are viewed before dismissal */
  averageViewTime: number;
  /** Percentage of alerts where actions were clicked */
  actionClickRate: number;
  /** Breakdown of alerts by category */
  categoryBreakdown: Record<AlertType, number>;
  /** Optional user satisfaction score */
  userSatisfactionScore?: number;
}

/**
 * Settings storage interface with versioning and migration support
 */
export interface AlertSettingsStorage {
  /** Version identifier for settings schema */
  version: string;
  /** The actual alert settings */
  settings: AlertSettings;
  /** Timestamp when settings were last updated */
  lastUpdated: number;
  /** Array of migration identifiers that have been applied */
  migrationApplied?: string[];
}

/**
 * Result interface for alert operations
 */
export interface AlertResult {
  /** Whether the operation was successful */
  success: boolean;
  /** Optional error message if operation failed */
  error?: string;
  /** The alert ID that was processed */
  alertId: string;
  /** Any additional result data */
  data?: any;
}

/**
 * Error recovery configuration for graceful degradation
 */
export interface ErrorRecoveryConfig {
  /** Maximum number of retry attempts */
  maxRetries: number;
  /** Delay between retry attempts in milliseconds */
  retryDelay: number;
  /** Fallback behavior when alert system fails */
  fallbackBehavior: 'console' | 'silent' | 'basic-alert';
  /** Whether to report errors for debugging */
  errorReporting: boolean;
}

/**
 * Default alert settings for initialization
 */
export const DEFAULT_ALERT_SETTINGS: AlertSettings = {
  durations: {
    success: 4000,
    info: 6000,
    warning: 8000,
    error: 10000,
    system: 6000,
  },
  maxConcurrentAlerts: 3,
  enableSounds: false,
  enableAnimations: true,
  position: 'top-right',
  categories: {
    performance: true,
    health: true,
    system: true,
    validation: true,
  },
  announceAlerts: true,
  highContrastMode: false,
  reducedMotion: false,
};

/**
 * Default error recovery configuration
 */
export const DEFAULT_ERROR_RECOVERY_CONFIG: ErrorRecoveryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  fallbackBehavior: 'console',
  errorReporting: true,
};