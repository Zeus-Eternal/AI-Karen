// Diagnostic script to validate module resolution issue
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Module Resolution Diagnostic ===\n');

// Check 1: Verify @vitejs/plugin-react installation
const packageJsonPath = path.join(__dirname, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const reactPluginVersion = packageJson.devDependencies['@vitejs/plugin-react'];

console.log('1. @vitejs/plugin-react version:', reactPluginVersion);

// Check 2: Verify TypeScript moduleResolution setting
const tsconfigPath = path.join(__dirname, 'tsconfig.json');
const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
const moduleResolution = tsconfig.compilerOptions.moduleResolution;

console.log('2. TypeScript moduleResolution setting:', moduleResolution);

// Check 3: Verify the actual type definition file exists
const typeDefPath = path.join(__dirname, 'node_modules/@vitejs/plugin-react/dist/index.d.ts');
const typeDefExists = fs.existsSync(typeDefPath);

console.log('3. Type definition file exists:', typeDefExists);
if (typeDefExists) {
  console.log('   Path:', typeDefPath);
}

// Check 4: Check if we're running in ESM mode
const packageType = packageJson.type;
console.log('4. Package type setting:', packageType);

// Check 5: Verify Vitest configuration
const vitestConfigPath = path.join(__dirname, 'vitest.config.ts');
console.log('5. Vitest config exists:', fs.existsSync(vitestConfigPath));

// Check 6: Check TypeScript version
const tsVersion = packageJson.devDependencies.typescript;
console.log('6. TypeScript version:', tsVersion);

console.log('\n=== Analysis ===');
console.log('The issue is likely caused by:');
console.log('- TypeScript moduleResolution is set to "node" (legacy)');
console.log('- Modern packages like @vitejs/plugin-react use ESM exports');
console.log('- The error message suggests updating to "node16", "nodenext", or "bundler"');

console.log('\n=== Recommended Solutions ===');
console.log('1. Update tsconfig.json moduleResolution to "bundler"');
console.log('2. Or update to "node16" or "nodenext"');
console.log('3. Ensure package.json has "type": "module" (already set)');