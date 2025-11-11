"use client";

import { useMemo } from "react";

import { useKarenAlerts } from "@/hooks/use-karen-alerts";

type KarenToasterAPI = ReturnType<typeof useKarenAlerts> & {
  celebrate: (title: string, message: string) => void;
  warn: (title: string, message: string) => void;
  notify: (title: string, message: string) => void;
  alert: (title: string, message: string) => void;
  whisper: (title: string, message: string) => void;
  shout: (title: string, message: string) => void;
};

export function useKarenToaster(): KarenToasterAPI {
  const alertsApi = useKarenAlerts();

  return useMemo(() => {
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
    } = alertsApi;

    return {
      ...alertsApi,
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
  }, [alertsApi]);
}

export default useKarenToaster;
