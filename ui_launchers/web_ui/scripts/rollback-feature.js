#!/usr/bin/env node

/**
 * Feature Rollback Script
 * Quickly disable feature flags and rollback problematic features
 */

const fs = require('fs');
const path = require('path');

// Available features that can be rolled back
const AVAILABLE_FEATURES = [
  'MODERN_DESIGN_TOKENS',
  'MODERN_LAYOUT_SYSTEM',
  'PERFORMANCE_MONITORING',
  'CONTAINER_QUERIES',
  'MODERN_COMPONENTS',
  'MICRO_INTERACTIONS',
  'ANIMATION_SYSTEM',
  'COMPOUND_PATTERNS',
  'ENHANCED_ACCESSIBILITY',
  'MODERN_ERROR_HANDLING',
  'LAZY_LOADING',
  'PERFORMANCE_OPTIMIZATIONS',
  'FULL_MODERNIZATION',
  'ALL_MODERN_COMPONENTS',
  'COMPLETE_INTEGRATION'
];

// Phase rollback presets
const PHASE_ROLLBACKS = {
  'phase4': ['FULL_MODERNIZATION', 'ALL_MODERN_COMPONENTS', 'COMPLETE_INTEGRATION'],
  'phase3': ['ENHANCED_ACCESSIBILITY', 'MODERN_ERROR_HANDLING', 'LAZY_LOADING', 'PERFORMANCE_OPTIMIZATIONS'],
  'phase2': ['MODERN_COMPONENTS', 'MICRO_INTERACTIONS', 'ANIMATION_SYSTEM', 'COMPOUND_PATTERNS'],
  'phase1': ['MODERN_DESIGN_TOKENS', 'MODERN_LAYOUT_SYSTEM', 'PERFORMANCE_MONITORING', 'CONTAINER_QUERIES'],
  'all': AVAILABLE_FEATURES
};

/**
 * Main rollback function
 */
async function rollbackFeature(featureName, reason = 'Manual rollback') {
  console.log(`🔄 Rolling back feature: ${featureName}`);
  console.log(`📝 Reason: ${reason}`);
  console.log(`⏰ Timestamp: ${new Date().toISOString()}\n`);
  
  try {
    // Validate feature name
    if (!AVAILABLE_FEATURES.includes(featureName) && !PHASE_ROLLBACKS[featureName]) {
      throw new Error(`Unknown feature: ${featureName}`);
    }
    
    // Determine features to rollback
    const featuresToRollback = PHASE_ROLLBACKS[featureName] || [featureName];
    
    // Update environment variables
    await updateEnvironmentVariables(featuresToRollback);
    
    // Log the rollback
    await logRollback(featureName, reason, featuresToRollback);
    
    // Clear Next.js cache
    await clearNextJSCache();
    
    // Notify team (if configured)
    await notifyTeam({
      type: 'rollback',
      feature: featureName,
      reason,
      timestamp: new Date().toISOString(),
      features: featuresToRollback
    });
    
    console.log(`✅ Feature ${featureName} rolled back successfully`);
    console.log(`📋 Features disabled: ${featuresToRollback.join(', ')}`);
    console.log(`\n🔄 Please restart the application to apply changes`);
    
  } catch (error) {
    console.error(`❌ Rollback failed: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Update environment variables to disable features
 */
async function updateEnvironmentVariables(features) {
  const envFiles = ['.env.local', '.env.development', '.env.production'];
  
  for (const envFile of envFiles) {
    const envPath = path.join(process.cwd(), envFile);
    
    if (fs.existsSync(envPath)) {
      console.log(`📝 Updating ${envFile}...`);
      
      let envContent = fs.readFileSync(envPath, 'utf8');
      
      // Disable each feature
      for (const feature of features) {
        const envVar = `NEXT_PUBLIC_${feature}`;
        const regex = new RegExp(`^${envVar}=.*$`, 'm');
        
        if (regex.test(envContent)) {
          // Update existing variable
          envContent = envContent.replace(regex, `${envVar}=false`);
        } else {
          // Add new variable
          envContent += `\n${envVar}=false`;
        }
      }
      
      fs.writeFileSync(envPath, envContent);
      console.log(`  ✅ Updated ${envFile}`);
    }
  }
}

/**
 * Log rollback for audit purposes
 */
async function logRollback(feature, reason, features) {
  const logDir = path.join(process.cwd(), 'logs');
  const logFile = path.join(logDir, 'rollback.log');
  
  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    feature,
    reason,
    features,
    user: process.env.USER || 'unknown',
    environment: process.env.NODE_ENV || 'development'
  };
  
  const logLine = JSON.stringify(logEntry) + '\n';
  fs.appendFileSync(logFile, logLine);
  
  console.log(`📝 Rollback logged to ${logFile}`);
}

/**
 * Clear Next.js cache
 */
async function clearNextJSCache() {
  const cacheDir = path.join(process.cwd(), '.next');
  
  if (fs.existsSync(cacheDir)) {
    console.log('🗑️  Clearing Next.js cache...');
    
    try {
      // Remove .next directory
      fs.rmSync(cacheDir, { recursive: true, force: true });
      console.log('  ✅ Next.js cache cleared');
    } catch (error) {
      console.warn(`  ⚠️  Could not clear cache: ${error.message}`);
    }
  }
}

/**
 * Notify team about rollback (placeholder for integration with Slack, etc.)
 */
async function notifyTeam(rollbackInfo) {
  // This would integrate with your notification system
  // For now, just log the notification
  console.log('📢 Team notification (placeholder):');
  console.log(JSON.stringify(rollbackInfo, null, 2));
  
  // Example integrations:
  // - Slack webhook
  // - Email notification
  // - PagerDuty alert
  // - Status page update
}

/**
 * Show available features and phases
 */
function showHelp() {
  console.log('🔄 Feature Rollback Script\n');
  console.log('Usage: node scripts/rollback-feature.js <feature|phase> [reason]\n');
  
  console.log('Available Features:');
  AVAILABLE_FEATURES.forEach(feature => {
    console.log(`  - ${feature}`);
  });
  
  console.log('\nAvailable Phases:');
  Object.keys(PHASE_ROLLBACKS).forEach(phase => {
    console.log(`  - ${phase} (${PHASE_ROLLBACKS[phase].length} features)`);
  });
  
  console.log('\nExamples:');
  console.log('  node scripts/rollback-feature.js MODERN_COMPONENTS "Performance issues"');
  console.log('  node scripts/rollback-feature.js phase2 "User complaints"');
  console.log('  node scripts/rollback-feature.js all "Critical bug found"');
}

/**
 * Parse command line arguments and execute rollback
 */
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    showHelp();
    return;
  }
  
  const featureName = args[0];
  const reason = args[1] || 'Manual rollback via script';
  
  rollbackFeature(featureName, reason);
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = { rollbackFeature, AVAILABLE_FEATURES, PHASE_ROLLBACKS };