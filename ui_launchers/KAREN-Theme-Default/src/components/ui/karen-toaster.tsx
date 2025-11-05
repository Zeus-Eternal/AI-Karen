"use client"

import * as React from "react";
import { useKarenAlerts } from "@/hooks/use-karen-alerts";
import { } from "./karen-toast"

/**
 * Karen Toaster component that integrates with the AlertManager
 * and displays alerts using the enhanced KarenToast component
 */
export function KarenToaster() {
  const { activeAlerts, settings } = useKarenAlerts();

  return (
    <KarenToastProvider swipeDirection="right">
      <KarenToastViewport position={settings.position} />
      {activeAlerts.map((alert) => (
        <KarenToast
          key={alert.id}
          alert={alert}
          variant={alert.variant}
          showProgress={settings.enableAnimations}
          duration={alert.duration || 5000}
        />
      ))}
    </KarenToastProvider>
  );
}

/**
 * Hook to integrate Karen toaster with existing toast system
 */
export function useKarenToaster() {
  const { 
    showAlert, 
    showSuccess, 
    showError, 
    showWarning, 
    showInfo,
    dismissAlert,
    dismissAllAlerts,
    settings,
    updateSettings
  } = useKarenAlerts();

  return {
    // Alert methods
    showAlert,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissAlert,
    dismissAllAlerts,
    
    // Settings
    settings,
    updateSettings,
    
    // Convenience methods with Karen personality
    celebrate: (title: string, message: string) => 
      showSuccess(title, message, { emoji: "🎉" }),
    
    warn: (title: string, message: string) => 
      showWarning(title, message, { emoji: "⚠️" }),
    
    notify: (title: string, message: string) => 
      showInfo(title, message, { emoji: "💡" }),
    
    alert: (title: string, message: string) => 
      showError(title, message, { emoji: "🚨" }),
    
    whisper: (title: string, message: string) => 
      showInfo(title, message, { 
        emoji: "🤫", 
        priority: "low",
        duration: 3000 
      }),
    
    shout: (title: string, message: string) => 
      showError(title, message, { 
        emoji: "📢", 
        priority: "high",
        duration: 8000 
      }),
  };
}