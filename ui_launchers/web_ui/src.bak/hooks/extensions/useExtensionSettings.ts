"use client";
import { useState } from "react";

export type ExtensionSettings = Record<string, any>;

export function useExtensionSettings(extensionId: string) {
  const [settings, setSettings] = useState<ExtensionSettings>({});

  // Placeholder save
  const save = async (values: ExtensionSettings) => {
    setSettings(values);
  };

  return { settings, save };
}
