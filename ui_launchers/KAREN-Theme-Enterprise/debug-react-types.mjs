/**
 * Diagnostic script to validate React type issues
 */

import fs from 'fs';
import path from 'path';

console.log('=== React Type Definition Diagnostic ===\n');

// Check 1: React version and types
try {
  const packageJson = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
  console.log('✓ React version:', packageJson.dependencies?.react || 'Not found');
  console.log('✓ @types/react version:', packageJson.devDependencies?.['@types/react'] || 'Not found');
  console.log('✓ Next.js version:', packageJson.dependencies?.next || 'Not found');
} catch (e) {
  console.log('✗ Failed to read package.json:', e.message);
}

// Check 2: Custom React types file
try {
  const reactTypesPath = './src/types/react.d.ts';
  if (fs.existsSync(reactTypesPath)) {
    const content = fs.readFileSync(reactTypesPath, 'utf8');
    console.log('\n✓ Custom React types file exists');
    console.log('✓ File size:', content.length, 'characters');
    
    // Check for problematic patterns
    if (content.includes('/// <reference path="global.d.ts" />')) {
      console.log('⚠ Found reference to global.d.ts');
    }
    if (content.includes('export interface HTMLAttributes')) {
      console.log('⚠ Found HTMLAttributes export (may conflict with React types)');
    }
  } else {
    console.log('\n✗ Custom React types file not found');
  }
} catch (e) {
  console.log('\n✗ Error checking custom React types:', e.message);
}

// Check 3: TypeScript configuration
try {
  const tsconfigPath = './tsconfig.json';
  const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
  console.log('\n✓ TypeScript configuration found');
  console.log('✓ Types array:', tsconfig.compilerOptions?.types || 'Not specified');
  
  if (tsconfig.compilerOptions?.types?.includes('./src/types/react')) {
    console.log('⚠ Custom React types included in tsconfig.types');
  }
  if (tsconfig.compilerOptions?.skipLibCheck === true) {
    console.log('⚠ skipLibCheck is enabled (may mask type issues)');
  }
  if (tsconfig.compilerOptions?.strict === false) {
    console.log('⚠ Strict mode is disabled');
  }
} catch (e) {
  console.log('\n✗ Error reading tsconfig.json:', e.message);
}

// Check 4: Problematic import patterns
const filesToCheck = [
  './src/providers/theme-provider.tsx',
  './src/services/enhanced-websocket-service.ts',
  './src/test-utils/test-providers.tsx',
  './src/test-utils/test-setup.ts',
  './src/utils/aria.ts',
  './src/utils/retry-mechanisms.ts'
];

console.log('\n=== Checking Import Patterns ===');
filesToCheck.forEach(file => {
  try {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const filename = path.basename(file);
      
      // Check for problematic patterns
      if (content.includes('const { ReactNode } = React;')) {
        console.log(`⚠ ${filename}: Destructuring ReactNode from React namespace`);
      }
      if (content.includes('const { FC, ReactNode, createElement, Fragment } = React;')) {
        console.log(`⚠ ${filename}: Destructuring multiple React exports`);
      }
      if (content.includes('const { useState, useCallback, useEffect, DependencyList } = React;')) {
        console.log(`⚠ ${filename}: Destructuring DependencyList from React`);
      }
      if (content.includes('type AriaAttributes = React.AriaAttributes;')) {
        console.log(`⚠ ${filename}: Type alias for React.AriaAttributes`);
      }
      if (content.includes('React.useReducer')) {
        console.log(`⚠ ${filename}: Using React.useReducer (may indicate import issue)`);
      }
    }
  } catch (e) {
    console.log(`✗ Error checking ${file}:`, e.message);
  }
});

console.log('\n=== Diagnosis Summary ===');
console.log('The main issues appear to be:');
console.log('1. Custom React types file that may conflict with @types/react');
console.log('2. Inconsistent import patterns (destructuring vs namespace access)');
console.log('3. TypeScript configuration that may not properly resolve React types');
console.log('4. Missing or incorrect type exports from custom React types');