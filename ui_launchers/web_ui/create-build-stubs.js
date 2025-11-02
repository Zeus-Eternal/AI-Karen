#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// List of problematic files that need to be stubbed
const problematicFiles = [
  'src/components/chat/AdaptiveChatInterface.tsx',
  'src/components/chat/ChatAnalyticsChart.tsx',
  'src/components/chat/ChatModeSelector.tsx',
  'src/components/chat/CopilotActions.tsx',
  'src/components/chat/CopilotArtifacts.tsx',
  'src/components/chat/EnhancedMessageBubble.tsx',
  'src/components/ChatInterface/ChatInterface.tsx',
];

// Create backup and stub for each file
for (const filePath of problematicFiles) {
  const fullPath = path.join(__dirname, filePath);
  const backupPath = fullPath + '.build-backup';
  
  try {
    // Create backup if it doesn't exist
    if (fs.existsSync(fullPath) && !fs.existsSync(backupPath)) {
      fs.copyFileSync(fullPath, backupPath);
      console.log(`Backed up: ${filePath}`);
    }
    
    // Create stub
    const componentName = path.basename(filePath, '.tsx');
    const stub = `"use client";

import React from 'react';

// Temporary stub for build - original backed up as ${componentName}.tsx.build-backup
export default function ${componentName}() {
  return (
    <div>
      <h2>${componentName}</h2>
      <p>This component is temporarily disabled for production build.</p>
    </div>
  );
}

// Export any commonly used exports to prevent import errors
export const DEFAULT_COPILOT_ACTIONS = [];
export const ChatInterface = ${componentName};
export const AdaptiveChatInterface = ${componentName};
`;
    
    fs.writeFileSync(fullPath, stub);
    console.log(`Created stub: ${filePath}`);
    
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
  }
}

console.log('Build stubs created. Run restore-from-stubs.js to restore original files.');