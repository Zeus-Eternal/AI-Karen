"use client";
import { useState } from "react";

export type ExtensionSettings = Record<string, unknown>;

export function useExtensionSettings(_extensionId: string) {
  const [settings, setSettings] = useState<ExtensionSettings>({});

  // Placeholder save
  const save = async (values: ExtensionSettings) => {
    setSettings(values);
  };

  return { settings, save };
}
