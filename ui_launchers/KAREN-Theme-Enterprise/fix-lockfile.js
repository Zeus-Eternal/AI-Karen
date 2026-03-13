#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Lockfile Fix Tool ===');
console.log('Fixing missing OS field in SWC packages...\n');

const lockfilePath = path.join(__dirname, 'package-lock.json');
const backupPath = path.join(__dirname, 'package-lock.json.backup');

try {
  // Create backup
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(lockfilePath, backupPath);
    console.log('✅ Created backup: package-lock.json.backup');
  }
  
  // Read and parse lockfile
  const lockfileContent = fs.readFileSync(lockfilePath, 'utf8');
  const lockfile = JSON.parse(lockfileContent);
  
  // Fix packages with missing OS field
  const packagesToFix = [
    'node_modules/@swc/counter',
    'node_modules/@swc/helpers',
    'node_modules/next/node_modules/@swc/helpers'
  ];
  
  let fixedCount = 0;
  
  for (const pkgPath of packagesToFix) {
    if (lockfile.packages?.[pkgPath]) {
      const pkg = lockfile.packages[pkgPath];
      
      if (!pkg.os) {
        pkg.os = ['darwin', 'linux', 'win32'];
        console.log(`✅ Fixed OS field for ${pkgPath}`);
        fixedCount++;
      }
      
      if (!pkg.cpu) {
        pkg.cpu = ['arm64', 'x64'];
        console.log(`✅ Fixed CPU field for ${pkgPath}`);
      }
      
      if (!pkg.libc) {
        pkg.libc = ['glibc'];
        console.log(`✅ Fixed libc field for ${pkgPath}`);
      }
    }
  }
  
  if (fixedCount > 0) {
    // Write fixed lockfile
    const fixedContent = JSON.stringify(lockfile, null, 2);
    fs.writeFileSync(lockfilePath, fixedContent, 'utf8');
    
    console.log(`\n✅ Successfully fixed ${fixedCount} packages in lockfile`);
    console.log('🔧 The lockfile has been updated with missing OS/CPU/libc fields');
    console.log('\n📋 Next steps:');
    console.log('1. Restart your development server');
    console.log('2. If issues persist, run: npm install');
    console.log('3. For Docker: docker compose down && docker compose up web');
  } else {
    console.log('ℹ️  No packages needed fixing');
  }
  
} catch (error) {
  console.error('❌ Error fixing lockfile:', error.message);
  
  // Restore from backup if available
  if (fs.existsSync(backupPath)) {
    console.log('🔄 Restoring from backup...');
    fs.copyFileSync(backupPath, lockfilePath);
    console.log('✅ Restored original lockfile');
  }
  
  process.exit(1);
}