/**
 * Karen Alerts Types
 * Type definitions for Karen alert system
 */

export interface KarenAlert {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp?: Date;
  duration?: number;
  emoji?: string;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
  persistent?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface AlertSettings {
  maxAlerts: number;
  defaultDuration: number;
  enableSound: boolean;
  enableDesktopNotifications: boolean;
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  grouping: boolean;
}

export interface AlertHistory {
  alerts: KarenAlert[];
  totalShown: number;
  totalDismissed: number;
  averageDisplayTime: number;
}

export interface AlertMetrics {
  totalAlerts: number;
  alertsByType: Record<string, number>;
  averageDismissalTime: number;
  mostCommonType: string;
}

export interface AlertResult {
  success: boolean;
  alertId?: string;
  message?: string;
}