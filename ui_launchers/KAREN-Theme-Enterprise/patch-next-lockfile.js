#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Next.js Lockfile Patch Tool ===');
console.log('Patching Next.js lockfile patching to handle missing versions...\n');

const nextPatchFile = path.join(__dirname, 'node_modules/next/dist/lib/patch-incorrect-lockfile.js');
const backupPath = path.join(__dirname, 'node_modules/next/dist/lib/patch-incorrect-lockfile.js.backup');

try {
  // Create backup
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(nextPatchFile, backupPath);
    console.log('✅ Created backup: patch-incorrect-lockfile.js.backup');
  }
  
  // Read the original file
  const originalContent = fs.readFileSync(nextPatchFile, 'utf8');
  
  // Find and replace the problematic fetchPkgInfo function
  const originalFunction = `function fetchPkgInfo(pkg) {
    if (!registry) registry = (0, _getregistry.getRegistry)();
    const res = await fetch(\`\${registry}\${pkg}\`);
    if (!res.ok) {
        throw new Error(\`Failed to fetch registry info for \${pkg}, got status \${res.status}\`);
    }
    const data = await res.json();
    const versionData = data.versions[_packagejson.default.version];
    return {
        os: versionData.os,
        cpu: versionData.cpu,
        engines: versionData.engines,
        tarball: versionData.dist.tarball,
        integrity: versionData.dist.integrity
    };
}`;
  
  const patchedFunction = `function fetchPkgInfo(pkg) {
    if (!registry) registry = (0, _getregistry.getRegistry)();
    const res = await fetch(\`\${registry}\${pkg}\`);
    if (!res.ok) {
        throw new Error(\`Failed to fetch registry info for \${pkg}, got status \${res.status}\`);
    }
    const data = await res.json();
    const versionData = data.versions[_packagejson.default.version];
    
    // Handle case where version doesn't exist in registry
    if (!versionData) {
        console.warn(\`Warning: Version \${_packagejson.default.version} not found for \${pkg}, using default values\`);
        return {
            os: ['darwin', 'linux', 'win32'],
            cpu: ['arm64', 'x64'],
            engines: undefined,
            tarball: undefined,
            integrity: undefined
        };
    }
    
    return {
        os: versionData.os,
        cpu: versionData.cpu,
        engines: versionData.engines,
        tarball: versionData.dist ? versionData.dist.tarball : undefined,
        integrity: versionData.dist ? versionData.dist.integrity : undefined
    };
}`;
  
  // Replace the function in the file
  const patchedContent = originalContent.replace(originalFunction, patchedFunction);
  
  if (patchedContent === originalContent) {
    console.log('⚠️  No changes made - function pattern not found exactly as expected');
    console.log('Attempting more flexible replacement...');
    
    // Try a more flexible replacement using regex
    const functionRegex = /function fetchPkgInfo\(pkg\) \{[\s\S]*?return \{[\s\S]*?\};[\s\S]*?\}/m;
    const flexibleReplacement = `function fetchPkgInfo(pkg) {
    if (!registry) registry = (0, _getregistry.getRegistry)();
    const res = await fetch(\`\${registry}\${pkg}\`);
    if (!res.ok) {
        throw new Error(\`Failed to fetch registry info for \${pkg}, got status \${res.status}\`);
    }
    const data = await res.json();
    const versionData = data.versions[_packagejson.default.version];
    
    // Handle case where version doesn't exist in registry
    if (!versionData) {
        console.warn(\`Warning: Version \${_packagejson.default.version} not found for \${pkg}, using default values\`);
        return {
            os: ['darwin', 'linux', 'win32'],
            cpu: ['arm64', 'x64'],
            engines: undefined,
            tarball: undefined,
            integrity: undefined
        };
    }
    
    return {
        os: versionData.os,
        cpu: versionData.cpu,
        engines: versionData.engines,
        tarball: versionData.dist ? versionData.dist.tarball : undefined,
        integrity: versionData.dist ? versionData.dist.integrity : undefined
    };
}`;
    
    const finalContent = originalContent.replace(functionRegex, flexibleReplacement);
    
    if (finalContent !== originalContent) {
      fs.writeFileSync(nextPatchFile, finalContent, 'utf8');
      console.log('✅ Successfully patched Next.js lockfile patching function (flexible replacement)');
    } else {
      console.error('❌ Failed to patch - could not find function to replace');
      process.exit(1);
    }
  } else {
    fs.writeFileSync(nextPatchFile, patchedContent, 'utf8');
    console.log('✅ Successfully patched Next.js lockfile patching function');
  }
  
  console.log('\n📋 Next steps:');
  console.log('1. Restart your development server');
  console.log('2. The patching should now handle missing versions gracefully');
  console.log('3. If issues persist, check the console for warning messages');
  
} catch (error) {
  console.error('❌ Error patching Next.js:', error.message);
  
  // Restore from backup if available
  if (fs.existsSync(backupPath)) {
    console.log('🔄 Restoring from backup...');
    fs.copyFileSync(backupPath, nextPatchFile);
    console.log('✅ Restored original file');
  }
  
  process.exit(1);
}