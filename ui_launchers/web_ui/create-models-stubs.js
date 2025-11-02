#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

console.log('Creating stubs for all models components...');

// Find all .tsx.build-backup files in models directory
const backupFiles = glob.sync('src/components/models/*.tsx.build-backup', { cwd: process.cwd() });

const createStub = (componentName) => `"use client";

import React from 'react';

export default function ${componentName}() {
  return (
    <div>
      <h3>${componentName}</h3>
      <p>This component is temporarily disabled for production build.</p>
    </div>
  );
}

export { ${componentName} };
`;

backupFiles.forEach(backupPath => {
  try {
    // Get original path by removing .build-backup
    const originalPath = backupPath.replace('.build-backup', '');
    
    // Extract component name from file path
    const fileName = path.basename(originalPath, '.tsx');
    const componentName = fileName;
    
    // Create stub
    fs.writeFileSync(originalPath, createStub(componentName));
    console.log(`Created stub: ${originalPath}`);
    
  } catch (error) {
    console.error(`Error processing ${backupPath}:`, error.message);
  }
});

console.log('All models component stubs created.');