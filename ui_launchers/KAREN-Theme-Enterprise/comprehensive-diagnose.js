#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Comprehensive Lockfile Diagnostic Tool ===');
console.log('Analyzing ALL packages for missing OS/CPU/libc fields...\n');

const lockfilePath = path.join(__dirname, 'package-lock.json');

try {
  // Read and parse lockfile
  const lockfileContent = fs.readFileSync(lockfilePath, 'utf8');
  const lockfile = JSON.parse(lockfileContent);
  
  console.log('✅ Lockfile parsed successfully');
  console.log(`📊 Lockfile size: ${fs.statSync(lockfilePath).size} bytes`);
  console.log(`📦 Total packages: ${Object.keys(lockfile.packages || {}).length}\n`);
  
  // Find all packages with missing OS field
  let packagesWithMissingOs = [];
  let packagesWithMissingCpu = [];
  let packagesWithMissingLibc = [];
  
  for (const [pkgName, pkgInfo] of Object.entries(lockfile.packages || {})) {
    if (pkgInfo.version) {
      if (!pkgInfo.os) {
        packagesWithMissingOs.push(pkgName);
      }
      if (!pkgInfo.cpu) {
        packagesWithMissingCpu.push(pkgName);
      }
      if (!pkgInfo.libc) {
        packagesWithMissingLibc.push(pkgName);
      }
    }
  }
  
  console.log(`🔍 Analysis Results:`);
  console.log(`   Packages missing OS field: ${packagesWithMissingOs.length}`);
  console.log(`   Packages missing CPU field: ${packagesWithMissingCpu.length}`);
  console.log(`   Packages missing libc field: ${packagesWithMissingLibc.length}\n`);
  
  if (packagesWithMissingOs.length > 0) {
    console.log('❌ Packages with missing OS field:');
    packagesWithMissingOs.slice(0, 10).forEach(pkg => {
      console.log(`   - ${pkg}`);
    });
    if (packagesWithMissingOs.length > 10) {
      console.log(`   ... and ${packagesWithMissingOs.length - 10} more`);
    }
  }
  
  // Look specifically for SWC-related packages
  const swcPackages = packagesWithMissingOs.filter(pkg => pkg.includes('swc'));
  if (swcPackages.length > 0) {
    console.log('\n⚠️  SWC packages with missing OS field:');
    swcPackages.forEach(pkg => {
      console.log(`   - ${pkg}`);
    });
  }
  
  // Check Next.js patching logic target packages
  const patchingTargets = [
    '@swc/helpers',
    '@swc/counter',
    '@swc/core',
    '@swc/types'
  ];
  
  console.log('\n🎯 Checking Next.js patching targets:');
  patchingTargets.forEach(target => {
    const found = Object.keys(lockfile.packages || {}).filter(pkg => pkg.includes(target));
    found.forEach(pkg => {
      const pkgInfo = lockfile.packages[pkg];
      const status = pkgInfo.os ? '✅' : '❌';
      console.log(`   ${status} ${pkg} - OS: ${pkgInfo.os || 'MISSING'}`);
    });
  });
  
} catch (error) {
  console.error('❌ Error analyzing lockfile:', error.message);
  process.exit(1);
}