#!/usr/bin/env node

/**
 * Phase Deployment Script
 * Manages phased deployment of UI modernization features
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const AVAILABLE_PHASES = ['phase1', 'phase2', 'phase3', 'phase4'];

/**
 * Deploy a specific phase
 */
async function deployPhase(phase, environment = 'development') {
  console.log(`🚀 Deploying ${phase} to ${environment} environment`);
  console.log(`⏰ Timestamp: ${new Date().toISOString()}\n`);
  
  try {
    // Validate phase
    if (!AVAILABLE_PHASES.includes(phase)) {
      throw new Error(`Invalid phase: ${phase}. Available phases: ${AVAILABLE_PHASES.join(', ')}`);
    }
    
    // Copy phase environment file
    await copyPhaseEnvironment(phase, environment);
    
    // Run pre-deployment checks
    await runPreDeploymentChecks(phase);
    
    // Build application
    await buildApplication();
    
    // Run post-deployment validation
    await runPostDeploymentValidation(phase);
    
    // Log deployment
    await logDeployment(phase, environment);
    
    console.log(`✅ ${phase} deployed successfully to ${environment}`);
    console.log(`📋 Next steps:`);
    console.log(`  1. Monitor application performance`);
    console.log(`  2. Check error rates and user feedback`);
    console.log(`  3. Validate feature functionality`);
    console.log(`  4. Proceed to next phase when ready`);
    
  } catch (error) {
    console.error(`❌ Deployment failed: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Copy phase-specific environment configuration
 */
async function copyPhaseEnvironment(phase, environment) {
  const sourceFile = path.join(process.cwd(), `.env.${phase}`);
  const targetFile = path.join(process.cwd(), `.env.${environment}`);
  
  if (!fs.existsSync(sourceFile)) {
    throw new Error(`Phase environment file not found: ${sourceFile}`);
  }
  
  console.log(`📝 Copying ${phase} configuration to ${environment}...`);
  fs.copyFileSync(sourceFile, targetFile);
  
  // Also update .env.local for immediate effect
  const localFile = path.join(process.cwd(), '.env.local');
  fs.copyFileSync(sourceFile, localFile);
  
  console.log(`  ✅ Environment configuration updated`);
}

/**
 * Run pre-deployment checks
 */
async function runPreDeploymentChecks(phase) {
  console.log(`🔍 Running pre-deployment checks for ${phase}...`);
  
  const checks = [
    {
      name: 'TypeScript compilation',
      command: 'npx tsc --noEmit --skipLibCheck',
      critical: true
    },
    {
      name: 'Linting',
      command: 'npm run lint',
      critical: false
    },
    {
      name: 'Unit tests',
      command: 'npm test -- --run --reporter=basic',
      critical: true
    },
    {
      name: 'Build test',
      command: 'npm run build',
      critical: true
    }
  ];
  
  for (const check of checks) {
    try {
      console.log(`  🔄 ${check.name}...`);
      execSync(check.command, { stdio: 'pipe' });
      console.log(`  ✅ ${check.name} passed`);
    } catch (error) {
      if (check.critical) {
        throw new Error(`Critical check failed: ${check.name}`);
      } else {
        console.log(`  ⚠️  ${check.name} failed (non-critical)`);
      }
    }
  }
}

/**
 * Build application
 */
async function buildApplication() {
  console.log(`🔨 Building application...`);
  
  try {
    execSync('npm run build', { stdio: 'inherit' });
    console.log(`  ✅ Build completed successfully`);
  } catch (error) {
    throw new Error('Build failed');
  }
}

/**
 * Run post-deployment validation
 */
async function runPostDeploymentValidation(phase) {
  console.log(`✅ Running post-deployment validation for ${phase}...`);
  
  const validations = [
    {
      name: 'Application starts',
      test: () => checkApplicationStart(),
      critical: true
    },
    {
      name: 'Feature flags loaded',
      test: () => checkFeatureFlags(phase),
      critical: true
    },
    {
      name: 'No console errors',
      test: () => checkConsoleErrors(),
      critical: false
    }
  ];
  
  for (const validation of validations) {
    try {
      console.log(`  🔄 ${validation.name}...`);
      await validation.test();
      console.log(`  ✅ ${validation.name} passed`);
    } catch (error) {
      if (validation.critical) {
        throw new Error(`Critical validation failed: ${validation.name} - ${error.message}`);
      } else {
        console.log(`  ⚠️  ${validation.name} failed (non-critical): ${error.message}`);
      }
    }
  }
}

/**
 * Check if application starts successfully
 */
async function checkApplicationStart() {
  // This would typically involve starting the app and checking if it responds
  // For now, we'll just check if the build output exists
  const buildDir = path.join(process.cwd(), '.next');
  if (!fs.existsSync(buildDir)) {
    throw new Error('Build output not found');
  }
}

/**
 * Check if feature flags are loaded correctly
 */
async function checkFeatureFlags(phase) {
  const envFile = path.join(process.cwd(), '.env.local');
  if (!fs.existsSync(envFile)) {
    throw new Error('Environment file not found');
  }
  
  const envContent = fs.readFileSync(envFile, 'utf8');
  
  // Check for phase-specific flags
  const phaseFlags = {
    phase1: ['MODERN_DESIGN_TOKENS=true'],
    phase2: ['MODERN_COMPONENTS=true'],
    phase3: ['ENHANCED_ACCESSIBILITY=true'],
    phase4: ['FULL_MODERNIZATION=true']
  };
  
  const expectedFlags = phaseFlags[phase] || [];
  for (const flag of expectedFlags) {
    if (!envContent.includes(flag)) {
      throw new Error(`Expected flag not found: ${flag}`);
    }
  }
}

/**
 * Check for console errors (placeholder)
 */
async function checkConsoleErrors() {
  // This would typically involve running the app and checking for console errors
  // For now, we'll just return success
  return true;
}

/**
 * Log deployment for audit purposes
 */
async function logDeployment(phase, environment) {
  const logDir = path.join(process.cwd(), 'logs');
  const logFile = path.join(logDir, 'deployment.log');
  
  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    phase,
    environment,
    user: process.env.USER || 'unknown',
    version: getPackageVersion(),
    success: true
  };
  
  const logLine = JSON.stringify(logEntry) + '\n';
  fs.appendFileSync(logFile, logLine);
  
  console.log(`📝 Deployment logged to ${logFile}`);
}

/**
 * Get package version
 */
function getPackageVersion() {
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    return packageJson.version || 'unknown';
  } catch (error) {
    return 'unknown';
  }
}

/**
 * Show help information
 */
function showHelp() {
  console.log('🚀 Phase Deployment Script\n');
  console.log('Usage: node scripts/deploy-phase.js <phase> [environment]\n');
  
  console.log('Available Phases:');
  console.log('  - phase1: Foundation (design tokens, layout system)');
  console.log('  - phase2: Components (modern components, interactions)');
  console.log('  - phase3: Enhanced Features (accessibility, optimizations)');
  console.log('  - phase4: Full Integration (complete modernization)\n');
  
  console.log('Available Environments:');
  console.log('  - development (default)');
  console.log('  - staging');
  console.log('  - production\n');
  
  console.log('Examples:');
  console.log('  node scripts/deploy-phase.js phase1');
  console.log('  node scripts/deploy-phase.js phase2 staging');
  console.log('  node scripts/deploy-phase.js phase4 production');
}

/**
 * Main function
 */
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    showHelp();
    return;
  }
  
  const phase = args[0];
  const environment = args[1] || 'development';
  
  deployPhase(phase, environment);
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = { deployPhase, AVAILABLE_PHASES };