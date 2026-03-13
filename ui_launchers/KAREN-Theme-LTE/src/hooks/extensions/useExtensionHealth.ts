"use client";
import { useState } from "react";

export interface ExtensionHealth {
  status: string;
}

export function useExtensionHealth(_extensionId: string) {
  void _extensionId;
  const [health, setHealth] = useState<ExtensionHealth | null>(null);

  // Placeholder implementation
  return { health, refresh: async () => setHealth({ status: "unknown" }) };
}
