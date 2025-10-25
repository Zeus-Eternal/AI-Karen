#!/usr/bin/env node

/**
 * Environment Variable Validation Script
 * 
 * Validates environment configuration for backend connectivity,
 * checks for deprecated variables, and provides migration recommendations.
 * 
 * Requirements: 1.2, 1.4
 * 
 * Usage:
 *   node scripts/validate-environment.js
 *   node scripts/validate-environment.js --fix
 *   node scripts/validate-environment.js --env=production
 */

const fs = require('fs');
const path = require('path');

// Standardized environment variable definitions
const STANDARDIZED_VARS = {
  'KAREN_BACKEND_URL': {
    description: 'Primary backend URL for server-side requests',
    example: 'http://localhost:8000',
    required: false,
    scope: 'server',
  },
  'NEXT_PUBLIC_KAREN_BACKEND_URL': {
    description: 'Primary backend URL for client-side requests',
    example: 'http://localhost:8000',
    required: false,
    scope: 'client',
  },
  'KAREN_FALLBACK_BACKEND_URLS': {
    description: 'Comma-separated fallback backend URLs',
    example: 'http://127.0.0.1:8000,http://host.docker.internal:8000',
    required: false,
    scope: 'both',
  },
  'KAREN_HA_BACKEND_URLS': {
    description: 'High availability backend URLs for production',
    example: 'http://backend1.example.com:8000,http://backend2.example.com:8000',
    required: false,
    scope: 'both',
    environments: ['production'],
  },
  'KAREN_CONTAINER_BACKEND_HOST': {
    description: 'Backend hostname for container environments',
    example: 'backend',
    required: false,
    scope: 'server',
    environments: ['docker'],
  },
  'KAREN_CONTAINER_BACKEND_PORT': {
    description: 'Backend port for container environments',
    example: '8000',
    required: false,
    scope: 'server',
    environments: ['docker'],
  },
  'KAREN_EXTERNAL_HOST': {
    description: 'External hostname for external access',
    example: 'your-domain.com',
    required: false,
    scope: 'both',
    environments: ['production'],
  },
  'KAREN_EXTERNAL_BACKEND_PORT': {
    description: 'Backend port for external access',
    example: '8000',
    required: false,
    scope: 'both',
    environments: ['production'],
  },
  'KAREN_BACKEND_PORT': {
    description: 'Backend port (legacy support)',
    example: '8000',
    required: false,
    scope: 'server',
  },
};

// Deprecated environment variables
const DEPRECATED_VARS = {
  'API_BASE_URL': {
    replacement: 'KAREN_BACKEND_URL',
    description: 'Use KAREN_BACKEND_URL for server-side backend URL',
  },
  'NEXT_PUBLIC_API_BASE_URL': {
    replacement: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
    description: 'Use NEXT_PUBLIC_KAREN_BACKEND_URL for client-side backend URL',
  },
  'BACKEND_PORT': {
    replacement: 'KAREN_BACKEND_PORT',
    description: 'Use KAREN_BACKEND_PORT for backend port configuration',
  },
};

// Timeout and retry configuration variables
const TIMEOUT_RETRY_VARS = {
  'AUTH_TIMEOUT_MS': {
    description: 'Authentication timeout in milliseconds',
    example: '45000',
    default: '45000',
    min: 5000,
    max: 120000,
  },
  'CONNECTION_TIMEOUT_MS': {
    description: 'Connection timeout in milliseconds',
    example: '30000',
    default: '30000',
    min: 1000,
    max: 60000,
  },
  'SESSION_VALIDATION_TIMEOUT_MS': {
    description: 'Session validation timeout in milliseconds',
    example: '30000',
    default: '30000',
    min: 5000,
    max: 60000,
  },
  'HEALTH_CHECK_TIMEOUT_MS': {
    description: 'Health check timeout in milliseconds',
    example: '10000',
    default: '10000',
    min: 1000,
    max: 30000,
  },
  'MAX_RETRY_ATTEMPTS': {
    description: 'Maximum number of retry attempts',
    example: '3',
    default: '3',
    min: 1,
    max: 10,
  },
  'RETRY_BASE_DELAY_MS': {
    description: 'Base delay between retries in milliseconds',
    example: '1000',
    default: '1000',
    min: 100,
    max: 5000,
  },
  'RETRY_MAX_DELAY_MS': {
    description: 'Maximum delay between retries in milliseconds',
    example: '10000',
    default: '10000',
    min: 1000,
    max: 30000,
  },
  'ENABLE_EXPONENTIAL_BACKOFF': {
    description: 'Enable exponential backoff for retries',
    example: 'true',
    default: 'true',
    type: 'boolean',
  },
};

class EnvironmentValidator {
  constructor(options = {}) {
    this.options = {
      fix: false,
      environment: process.env.NODE_ENV || 'development',
      verbose: false,
      ...options,
    };
    
    this.warnings = [];
    this.errors = [];
    this.recommendations = [];
  }

  /**
   * Load environment variables from .env files
   */
  loadEnvironmentFiles() {
    const envFiles = [
      '.env',
      '.env.local',
      `.env.${this.options.environment}`,
      `.env.${this.options.environment}.local`,
      'ui_launchers/web_ui/.env.development',
    ];

    const envVars = {};

    for (const envFile of envFiles) {
      if (fs.existsSync(envFile)) {
        const stat = fs.statSync(envFile);
        if (stat.isFile()) {
          try {
            const content = fs.readFileSync(envFile, 'utf8');
            const lines = content.split('\n');
            
            for (const line of lines) {
              const trimmed = line.trim();
              if (trimmed && !trimmed.startsWith('#')) {
                const [key, ...valueParts] = trimmed.split('=');
                if (key && valueParts.length > 0) {
                  const value = valueParts.join('=').replace(/^["']|["']$/g, '');
                  envVars[key] = value;
                }
              }
            }
          } catch (error) {
            console.warn(`Warning: Could not read ${envFile}: ${error.message}`);
          }
        }
      }
    }

    return envVars;
  }

  /**
   * Validate standardized environment variables
   */
  validateStandardizedVars(envVars) {
    console.log('🔍 Validating standardized environment variables...\n');

    for (const [varName, config] of Object.entries(STANDARDIZED_VARS)) {
      const value = envVars[varName] || process.env[varName];
      
      if (config.required && !value) {
        this.errors.push(`Required environment variable ${varName} is not set`);
        continue;
      }

      if (value) {
        // Validate URL format for URL variables
        if (varName.includes('URL') || varName.includes('HOST')) {
          if (varName.includes('URL')) {
            // Handle comma-separated URLs
            if (varName.includes('FALLBACK') || varName.includes('HA')) {
              const urls = value.split(',').map(url => url.trim());
              for (const url of urls) {
                try {
                  new URL(url);
                } catch (error) {
                  this.errors.push(`Invalid URL format in ${varName}: ${url}`);
                }
              }
            } else {
              // Single URL
              try {
                new URL(value);
              } catch (error) {
                this.errors.push(`Invalid URL format for ${varName}: ${value}`);
              }
            }
          }
        }

        // Validate port numbers
        if (varName.includes('PORT')) {
          const port = parseInt(value, 10);
          if (isNaN(port) || port < 1 || port > 65535) {
            this.errors.push(`Invalid port number for ${varName}: ${value}`);
          }
        }

        // Environment-specific validation
        if (config.environments && !config.environments.includes(this.options.environment)) {
          this.warnings.push(`${varName} is typically used in ${config.environments.join(', ')} environments`);
        }

        console.log(`✅ ${varName}: ${value}`);
      } else {
        console.log(`⚪ ${varName}: not set (using default)`);
      }
    }
  }

  /**
   * Check for deprecated environment variables
   */
  checkDeprecatedVars(envVars) {
    console.log('\n🚨 Checking for deprecated environment variables...\n');

    let foundDeprecated = false;

    for (const [varName, config] of Object.entries(DEPRECATED_VARS)) {
      const value = envVars[varName] || process.env[varName];
      
      if (value) {
        foundDeprecated = true;
        this.warnings.push(`Deprecated variable ${varName} found. ${config.description}`);
        this.recommendations.push({
          action: 'migrate',
          from: varName,
          to: config.replacement,
          value: value,
          description: config.description,
        });
        
        console.log(`⚠️  ${varName}: ${value} (deprecated)`);
        console.log(`    → Migrate to: ${config.replacement}`);
      }
    }

    if (!foundDeprecated) {
      console.log('✅ No deprecated environment variables found');
    }
  }

  /**
   * Validate timeout and retry configuration
   */
  validateTimeoutRetryConfig(envVars) {
    console.log('\n⏱️  Validating timeout and retry configuration...\n');

    for (const [varName, config] of Object.entries(TIMEOUT_RETRY_VARS)) {
      const value = envVars[varName] || process.env[varName];
      
      if (value) {
        if (config.type === 'boolean') {
          if (!['true', 'false'].includes(value.toLowerCase())) {
            this.errors.push(`${varName} must be 'true' or 'false', got: ${value}`);
          }
        } else {
          const numValue = parseInt(value, 10);
          if (isNaN(numValue)) {
            this.errors.push(`${varName} must be a number, got: ${value}`);
          } else {
            if (config.min && numValue < config.min) {
              this.warnings.push(`${varName} is below recommended minimum (${config.min}): ${value}`);
            }
            if (config.max && numValue > config.max) {
              this.warnings.push(`${varName} is above recommended maximum (${config.max}): ${value}`);
            }
          }
        }
        
        console.log(`✅ ${varName}: ${value}`);
      } else {
        console.log(`⚪ ${varName}: not set (default: ${config.default})`);
      }
    }
  }

  /**
   * Check for conflicting environment variables
   */
  checkConflicts(envVars) {
    console.log('\n🔍 Checking for conflicting environment variables...\n');

    const conflicts = [
      {
        vars: ['KAREN_BACKEND_URL', 'API_BASE_URL'],
        description: 'Server-side backend URL conflict',
      },
      {
        vars: ['NEXT_PUBLIC_KAREN_BACKEND_URL', 'NEXT_PUBLIC_API_BASE_URL'],
        description: 'Client-side backend URL conflict',
      },
      {
        vars: ['KAREN_BACKEND_PORT', 'BACKEND_PORT'],
        description: 'Backend port conflict',
      },
    ];

    let foundConflicts = false;

    for (const conflict of conflicts) {
      const values = conflict.vars.map(varName => ({
        name: varName,
        value: envVars[varName] || process.env[varName],
      })).filter(item => item.value);

      if (values.length > 1) {
        const uniqueValues = [...new Set(values.map(item => item.value))];
        if (uniqueValues.length > 1) {
          foundConflicts = true;
          this.warnings.push(`${conflict.description}: ${values.map(item => `${item.name}=${item.value}`).join(', ')}`);
          
          console.log(`⚠️  ${conflict.description}:`);
          values.forEach(item => {
            console.log(`    ${item.name}: ${item.value}`);
          });
        }
      }
    }

    if (!foundConflicts) {
      console.log('✅ No conflicting environment variables found');
    }
  }

  /**
   * Environment-specific validation
   */
  validateEnvironmentSpecific(envVars) {
    console.log(`\n🌍 Validating ${this.options.environment} environment configuration...\n`);

    if (this.options.environment === 'production') {
      // Production-specific validation
      const haUrls = envVars['KAREN_HA_BACKEND_URLS'] || process.env['KAREN_HA_BACKEND_URLS'];
      const fallbackUrls = envVars['KAREN_FALLBACK_BACKEND_URLS'] || process.env['KAREN_FALLBACK_BACKEND_URLS'];
      
      if (!haUrls && !fallbackUrls) {
        this.warnings.push('Production environment should have high availability or fallback URLs configured');
      }

      // Check for localhost URLs in production
      const backendUrl = envVars['KAREN_BACKEND_URL'] || process.env['KAREN_BACKEND_URL'];
      const publicBackendUrl = envVars['NEXT_PUBLIC_KAREN_BACKEND_URL'] || process.env['NEXT_PUBLIC_KAREN_BACKEND_URL'];
      
      if (backendUrl && backendUrl.includes('localhost')) {
        this.warnings.push('Production environment using localhost backend URL');
      }
      
      if (publicBackendUrl && publicBackendUrl.includes('localhost')) {
        this.warnings.push('Production environment using localhost public backend URL');
      }
    }

    if (this.options.environment === 'development') {
      // Development-specific validation
      const dockerContainer = envVars['DOCKER_CONTAINER'] || process.env['DOCKER_CONTAINER'];
      const backendUrl = envVars['KAREN_BACKEND_URL'] || process.env['KAREN_BACKEND_URL'];
      
      if (dockerContainer && backendUrl && backendUrl.includes('localhost')) {
        this.warnings.push('Docker environment with localhost backend URL may cause connectivity issues');
      }
    }
  }

  /**
   * Generate migration script
   */
  generateMigrationScript() {
    if (this.recommendations.length === 0) {
      return null;
    }

    let script = '#!/bin/bash\n\n';
    script += '# Environment Variable Migration Script\n';
    script += '# Generated by validate-environment.js\n\n';

    for (const rec of this.recommendations) {
      if (rec.action === 'migrate') {
        script += `# Migrate ${rec.from} to ${rec.to}\n`;
        script += `# ${rec.description}\n`;
        script += `# Current value: ${rec.value}\n`;
        script += `# TODO: Update your .env files to use ${rec.to}=${rec.value}\n`;
        script += `# TODO: Remove ${rec.from} after migration\n\n`;
      }
    }

    return script;
  }

  /**
   * Run validation
   */
  async validate() {
    console.log('🔧 Environment Variable Validation\n');
    console.log(`Environment: ${this.options.environment}`);
    console.log(`Fix mode: ${this.options.fix ? 'enabled' : 'disabled'}\n`);

    const envVars = this.loadEnvironmentFiles();

    // Run all validations
    this.validateStandardizedVars(envVars);
    this.checkDeprecatedVars(envVars);
    this.validateTimeoutRetryConfig(envVars);
    this.checkConflicts(envVars);
    this.validateEnvironmentSpecific(envVars);

    // Generate migration script if needed
    if (this.options.fix && this.recommendations.length > 0) {
      const migrationScript = this.generateMigrationScript();
      if (migrationScript) {
        fs.writeFileSync('migrate-environment.sh', migrationScript);
        console.log('\n📝 Generated migration script: migrate-environment.sh');
      }
    }

    // Print summary
    console.log('\n📊 Validation Summary:');
    console.log(`✅ Validation completed`);
    console.log(`⚠️  Warnings: ${this.warnings.length}`);
    console.log(`❌ Errors: ${this.errors.length}`);
    console.log(`💡 Recommendations: ${this.recommendations.length}`);

    if (this.warnings.length > 0) {
      console.log('\n⚠️  Warnings:');
      this.warnings.forEach(warning => console.log(`  - ${warning}`));
    }

    if (this.errors.length > 0) {
      console.log('\n❌ Errors:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }

    if (this.recommendations.length > 0) {
      console.log('\n💡 Recommendations:');
      this.recommendations.forEach(rec => {
        console.log(`  - ${rec.description}`);
        if (rec.action === 'migrate') {
          console.log(`    Migrate: ${rec.from} → ${rec.to}`);
        }
      });
    }

    return {
      success: this.errors.length === 0,
      warnings: this.warnings,
      errors: this.errors,
      recommendations: this.recommendations,
    };
  }
}

// CLI handling
async function main() {
  const args = process.argv.slice(2);
  const options = {};

  for (const arg of args) {
    if (arg === '--fix') {
      options.fix = true;
    } else if (arg === '--verbose') {
      options.verbose = true;
    } else if (arg.startsWith('--env=')) {
      options.environment = arg.split('=')[1];
    } else if (arg === '--help') {
      console.log(`
Environment Variable Validation Script

Usage:
  node scripts/validate-environment.js [options]

Options:
  --fix                 Generate migration scripts for deprecated variables
  --env=<environment>   Specify environment (development, production, test)
  --verbose            Enable verbose output
  --help               Show this help message

Examples:
  node scripts/validate-environment.js
  node scripts/validate-environment.js --fix
  node scripts/validate-environment.js --env=production
      `);
      process.exit(0);
    }
  }

  const validator = new EnvironmentValidator(options);
  const result = await validator.validate();

  process.exit(result.success ? 0 : 1);
}

if (require.main === module) {
  main().catch(error => {
    console.error('Validation failed:', error);
    process.exit(1);
  });
}

module.exports = { EnvironmentValidator };