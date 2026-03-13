#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Lockfile Diagnostic Tool ===');
console.log('Analyzing package-lock.json for SWC dependency issues...\n');

const lockfilePath = path.join(__dirname, 'package-lock.json');

try {
  // Check if lockfile exists
  if (!fs.existsSync(lockfilePath)) {
    console.error('❌ package-lock.json not found');
    process.exit(1);
  }

  // Read and parse lockfile
  const lockfileContent = fs.readFileSync(lockfilePath, 'utf8');
  const lockfile = JSON.parse(lockfileContent);
  
  console.log('✅ Lockfile parsed successfully');
  console.log(`📊 Lockfile size: ${fs.statSync(lockfilePath).size} bytes`);
  console.log(`📦 Total packages: ${Object.keys(lockfile.packages || {}).length}\n`);
  
  // Check Next.js package
  const nextPkg = lockfile.packages?.next || lockfile.packages?.['node_modules/next'];
  if (nextPkg) {
    console.log(`✅ Found Next.js: ${nextPkg.version}`);
    console.log(`   Dependencies: ${Object.keys(nextPkg.dependencies || {}).length}`);
    console.log(`   Has @swc/helpers in dependencies: ${!!nextPkg.dependencies?.['@swc/helpers']}`);
  } else {
    console.error('❌ Next.js package not found in lockfile');
  }
  
  // Check SWC helpers package
  const swcHelpersPkg = lockfile.packages?.['@swc/helpers'] || lockfile.packages?.['node_modules/@swc/helpers'];
  if (swcHelpersPkg) {
    console.log(`✅ Found @swc/helpers: ${swcHelpersPkg.version}`);
    console.log(`   OS field: ${swcHelpersPkg.os || 'MISSING'}`);
    console.log(`   CPU field: ${swcHelpersPkg.cpu || 'MISSING'}`);
    console.log(`   Libc field: ${swcHelpersPkg.libc || 'MISSING'}`);
  } else {
    console.error('❌ @swc/helpers package not found in lockfile');
  }
  
  // Look for any packages with missing OS field
  console.log('\n🔍 Checking for packages with missing OS field...');
  let packagesWithMissingOs = 0;
  
  for (const [pkgName, pkgInfo] of Object.entries(lockfile.packages || {})) {
    if (pkgInfo.version && !pkgInfo.os && pkgName.includes('swc')) {
      console.log(`⚠️  ${pkgName}: missing OS field`);
      packagesWithMissingOs++;
    }
  }
  
  if (packagesWithMissingOs > 0) {
    console.log(`\n❌ Found ${packagesWithMissingOs} SWC packages with missing OS field`);
    console.log('This is likely causing the "Cannot read properties of undefined (reading \'os\')" error');
  } else {
    console.log('\n✅ All SWC packages have OS field');
  }
  
  // Check lockfile format version
  console.log(`\n📋 Lockfile version: ${lockfile.lockfileVersion || 'unknown'}`);
  
} catch (error) {
  console.error('❌ Error analyzing lockfile:', error.message);
  console.error(error.stack);
  process.exit(1);
}