#!/usr/bin/env node

/**
 * Advanced Module Compatibility Diagnostic Tool
 * 
 * This tool analyzes the dependency graph for ESM/CJS compatibility issues,
 * identifies legacy patterns, and validates module resolution strategies.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

console.log('🔍 Advanced Module Compatibility Diagnostic\n');
console.log('='.repeat(60));

// Configuration
const projectRoot = __dirname;
const packageJsonPath = path.join(projectRoot, 'package.json');
const tsconfigPath = path.join(projectRoot, 'tsconfig.json');
const nodeModulesPath = path.join(projectRoot, 'node_modules');

// Read configuration files
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));

console.log('📋 Project Configuration Analysis');
console.log('-'.repeat(40));

// 1. Check package.json ESM configuration
console.log(`Package type: ${packageJson.type || 'undefined'}`);
console.log(`TypeScript moduleResolution: ${tsconfig.compilerOptions.moduleResolution}`);

// 2. Analyze @vitejs/plugin-react specifically
console.log('\n🔧 @vitejs/plugin-react Analysis');
console.log('-'.repeat(40));

const pluginPath = path.join(nodeModulesPath, '@vitejs/plugin-react');
const pluginPackageJsonPath = path.join(pluginPath, 'package.json');
const pluginTypeDefPath = path.join(pluginPath, 'dist/index.d.ts');

if (fs.existsSync(pluginPackageJsonPath)) {
  const pluginPackageJson = JSON.parse(fs.readFileSync(pluginPackageJsonPath, 'utf8'));
  console.log(`Plugin version: ${pluginPackageJson.version}`);
  console.log(`Plugin exports: ${JSON.stringify(pluginPackageJson.exports || 'N/A')}`);
  console.log(`Plugin main: ${pluginPackageJson.main || 'N/A'}`);
  console.log(`Plugin module: ${pluginPackageJson.module || 'N/A'}`);
  console.log(`Plugin types: ${pluginPackageJson.types || pluginPackageJson.typings || 'N/A'}`);
}

if (fs.existsSync(pluginTypeDefPath)) {
  console.log(`Type definition file exists: ✅`);
  
  // Analyze the type definition file for export patterns
  const typeDefContent = fs.readFileSync(pluginTypeDefPath, 'utf8');
  const hasExportDefault = typeDefContent.includes('export default');
  const hasNamedExports = typeDefContent.includes('export {');
  const hasESMExports = hasExportDefault || hasNamedExports;
  
  console.log(`ESM exports detected: ${hasESMExports ? '✅' : '❌'}`);
  console.log(`Default export: ${hasExportDefault ? '✅' : '❌'}`);
  console.log(`Named exports: ${hasNamedExports ? '✅' : '❌'}`);
}

// 3. Check for dual-package hazard patterns
console.log('\n⚠️  Dual-Package Hazard Detection');
console.log('-'.repeat(40));

const criticalPackages = [
  '@vitejs/plugin-react',
  'react',
  'react-dom',
  'vite',
  'vitest'
];

criticalPackages.forEach(pkgName => {
  const pkgPath = path.join(nodeModulesPath, pkgName);
  if (fs.existsSync(pkgPath)) {
    const pkgJsonPath = path.join(pkgPath, 'package.json');
    if (fs.existsSync(pkgJsonPath)) {
      const pkgJson = JSON.parse(fs.readFileSync(pkgJsonPath, 'utf8'));
      const hasDualExports = pkgJson.main && pkgJson.module;
      const hasConditionalExports = pkgJson.exports;
      
      console.log(`${pkgName}:`);
      console.log(`  Dual exports: ${hasDualExports ? '⚠️  ' : '✅'}`);
      console.log(`  Conditional exports: ${hasConditionalExports ? '✅' : '❌'}`);
      
      if (hasConditionalExports) {
        const hasImportCondition = pkgJson.exports.import || 
          (pkgJson.exports['.'] && pkgJson.exports['.'].import);
        const hasDefaultCondition = pkgJson.exports.default || 
          (pkgJson.exports['.'] && pkgJson.exports['.'].default);
        
        console.log(`  Import condition: ${hasImportCondition ? '✅' : '❌'}`);
        console.log(`  Default condition: ${hasDefaultCondition ? '✅' : '❌'}`);
      }
    }
  }
});

// 4. Module Resolution Compatibility Check
console.log('\n🔍 Module Resolution Compatibility');
console.log('-'.repeat(40));

const moduleResolution = tsconfig.compilerOptions.moduleResolution;
const target = tsconfig.compilerOptions.target;
const isESMProject = packageJson.type === 'module';

console.log(`Project ESM: ${isESMProject ? '✅' : '❌'}`);
console.log(`Target: ${target}`);
console.log(`Module: ${tsconfig.compilerOptions.module}`);
console.log(`Module resolution: ${moduleResolution}`);

// Compatibility matrix
const compatibilityMatrix = {
  'bundler': {
    description: 'Optimized for bundlers (Vite, Webpack, etc.)',
    esmCompatible: true,
    recommended: true
  },
  'node': {
    description: 'Legacy Node.js resolution',
    esmCompatible: false,
    recommended: false
  },
  'node16': {
    description: 'Node.js 16+ ESM resolution',
    esmCompatible: true,
    recommended: true
  },
  'nodenext': {
    description: 'Latest Node.js ESM resolution',
    esmCompatible: true,
    recommended: true
  }
};

const currentConfig = compatibilityMatrix[moduleResolution];
console.log(`\nCurrent configuration:`);
console.log(`  Description: ${currentConfig.description}`);
console.log(`  ESM compatible: ${currentConfig.esmCompatible ? '✅' : '❌'}`);
console.log(`  Recommended: ${currentConfig.recommended ? '✅' : '❌'}`);

// 5. Recommendations
console.log('\n💡 Recommendations');
console.log('-'.repeat(40));

if (!currentConfig.esmCompatible) {
  console.log('❌ CRITICAL: Your moduleResolution setting is not ESM compatible');
  console.log('   This will cause issues with modern packages like @vitejs/plugin-react');
  console.log('   Recommended fix: Update moduleResolution to "bundler"');
}

if (isESMProject && !currentConfig.esmCompatible) {
  console.log('❌ MISMATCH: Project is configured as ESM but TypeScript is not');
  console.log('   This creates a dual-package hazard within your own project');
  console.log('   Recommended fix: Update moduleResolution to an ESM-compatible option');
}

if (currentConfig.recommended) {
  console.log('✅ Your moduleResolution setting is appropriate for modern development');
} else {
  console.log('⚠️  Consider upgrading to a more modern moduleResolution setting');
}

// 6. Verification Test
console.log('\n🧪 Verification Test');
console.log('-'.repeat(40));

try {
  // Try to import the problematic module
  const reactPlugin = require('@vitejs/plugin-react');
  console.log('✅ @vitejs/plugin-react imported successfully with require()');
  
  // Check if it has the expected structure
  if (typeof reactPlugin === 'function' || (typeof reactPlugin === 'object' && reactPlugin.default)) {
    console.log('✅ Plugin has expected export structure');
  } else {
    console.log('⚠️  Plugin has unexpected export structure');
  }
} catch (error) {
  console.log('❌ Failed to import @vitejs/plugin-react with require()');
  console.log(`   Error: ${error.message}`);
}

console.log('\n' + '='.repeat(60));
console.log('Diagnostic complete! 🎉');