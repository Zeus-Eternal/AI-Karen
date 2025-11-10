"use client";

import * as React from "react";

import { useKarenAlerts } from "@/hooks/use-karen-alerts";
import type { AlertAction } from "@/types/karen-alerts";

import {
  KarenToast,
  KarenToastProvider,
  KarenToastViewport,
} from "@/components/ui/karen-toast";

export function KarenToaster() {
  const { activeAlerts, settings, dismissAlert } = useKarenAlerts();

  const handleActionClick = React.useCallback(
    (alertId: string) => (_action: AlertAction) => {
      void dismissAlert(alertId);
    },
    [dismissAlert]
  );

  return (
    <KarenToastProvider swipeDirection="right">
      <KarenToastViewport position={settings.position} />
      {activeAlerts.map((alert) => (
        <KarenToast
          key={alert.id}
          alert={alert}
          variant={alert.variant}
          showProgress={settings.enableAnimations}
          duration={alert.duration ?? settings.durations.info}
          onOpenChange={(open) => {
            if (!open) {
              void dismissAlert(alert.id);
            }
          }}
          onActionClick={handleActionClick(alert.id)}
        />
      ))}
    </KarenToastProvider>
  );
}

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
    updateSettings,
  } = useKarenAlerts();

  return {
    showAlert,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissAlert,
    dismissAllAlerts,
    settings,
    updateSettings,
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
        duration: 3000,
      }),
    shout: (title: string, message: string) =>
      showError(title, message, {
        emoji: "📢",
        priority: "high",
        duration: 8000,
      }),
  };
}
