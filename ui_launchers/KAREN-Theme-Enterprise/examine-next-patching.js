#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Next.js Patching Code Analysis ===');
console.log('Examining the exact code that\'s failing...\n');

const nextPatchFile = path.join(__dirname, 'node_modules/next/dist/lib/patch-incorrect-lockfile.js');

try {
  if (!fs.existsSync(nextPatchFile)) {
    console.error('❌ Next.js patch file not found');
    process.exit(1);
  }
  
  const patchCode = fs.readFileSync(nextPatchFile, 'utf8');
  
  // Extract the fetchPkgInfo function
  const fetchPkgInfoMatch = patchCode.match(/function fetchPkgInfo[\s\S]*?^}/m);
  if (fetchPkgInfoMatch) {
    console.log('📋 Found fetchPkgInfo function:');
    console.log('----------------------------------------');
    console.log(fetchPkgInfoMatch[0]);
    console.log('----------------------------------------\n');
  }
  
  // Find line 73 where the error occurs
  const lines = patchCode.split('\n');
  console.log(`📍 Line 73 (error location): ${lines[72]}`);
  console.log(`📍 Line 74: ${lines[73]}`);
  console.log(`📍 Line 75: ${lines[74]}\n`);
  
  // Look for what's being passed to fetchPkgInfo
  const patchIncorrectLockfileMatch = patchCode.match(/function patchIncorrectLockfile[\s\S]*?^}/m);
  if (patchIncorrectLockfileMatch) {
    const patchFunction = patchIncorrectLockfileMatch[0];
    
    // Find the Promise.all call that's mentioned in the error
    const promiseAllMatch = patchFunction.match(/Promise\.all\([\s\S]*?\)/m);
    if (promiseAllMatch) {
      console.log('🔍 Promise.all call that\'s failing:');
      console.log('----------------------------------------');
      console.log(promiseAllMatch[0]);
      console.log('----------------------------------------\n');
    }
    
    // Look for swcDependencies array
    const swcDepsMatch = patchFunction.match(/const swcDependencies = \[[\s\S]*?\];/m);
    if (swcDepsMatch) {
      console.log('🎯 SWC dependencies being patched:');
      console.log('----------------------------------------');
      console.log(swcDepsMatch[0]);
      console.log('----------------------------------------\n');
    }
  }
  
} catch (error) {
  console.error('❌ Error analyzing Next.js patch code:', error.message);
  process.exit(1);
}