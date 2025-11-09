"use client";

import React from "react";

import type { CopilotAction } from "./types";

// Temporary stub for build - original backed up as ChatInterface.tsx.build-backup
function ChatInterface() {
  return (
    <div>
      <h2>ChatInterface</h2>
      <p>This component is temporarily disabled for production build.</p>
    </div>
  );
}

// Export any commonly used exports to prevent import errors
export const DEFAULT_COPILOT_ACTIONS: CopilotAction[] = [];

export { ChatInterface };
export default ChatInterface;
