"use client";
export function useExtensionControls(extensionId: string) {
  const runControl = async (action: string, params?: Record<string, any>) => {
    console.log("run", extensionId, action, params);
  };
  return { runControl };
}
