#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class StaticAuditor {
  constructor() {
    this.results = [];
    this.projectRoot = __dirname;
  }

  addResult(category, test, status, message, details = null) {
    this.results.push({ category, test, status, message, details });
    const icon = status === 'PASS' ? '✅' : status === 'WARNING' ? '⚠️' : '❌';
    console.log(`${icon} ${category} - ${test}: ${message}`);
  }

  auditPackageJson() {
    console.log('\n📦 Auditing package.json...');
    
    const packagePath = path.join(this.projectRoot, 'package.json');
    if (!fs.existsSync(packagePath)) {
      this.addResult('Dependencies', 'package.json', 'FAIL', 'package.json not found');
      return;
    }

    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    // Check for security-related dependencies
    const securityDeps = [
      'helmet',
      'cors',
      'express-rate-limit',
      'bcrypt',
      'jsonwebtoken'
    ];

    const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
    
    securityDeps.forEach(dep => {
      if (allDeps[dep]) {
        this.addResult('Dependencies', `Security: ${dep}`, 'PASS', `Security dependency present: ${allDeps[dep]}`);
      } else {
        this.addResult('Dependencies', `Security: ${dep}`, 'WARNING', `Consider adding security dependency: ${dep}`);
      }
    });

    // Check for outdated or vulnerable patterns
    const vulnerablePatterns = [
      { name: 'eval usage', pattern: /eval\s*\(/ },
      { name: 'innerHTML usage', pattern: /innerHTML\s*=/ },
      { name: 'document.write', pattern: /document\.write\s*\(/ }
    ];

    this.addResult('Dependencies', 'Package structure', 'PASS', `Found ${Object.keys(allDeps).length} dependencies`);
  }

  auditEnvironmentFiles() {
    console.log('\n🔐 Auditing environment files...');
    
    const envFiles = ['.env', '.env.local', '.env.example', '.env.production'];
    
    envFiles.forEach(envFile => {
      const envPath = path.join(this.projectRoot, envFile);
      if (fs.existsSync(envPath)) {
        const stats = fs.statSync(envPath);
        const mode = (stats.mode & parseInt('777', 8)).toString(8);
        
        if (envFile !== '.env.example' && mode !== '600') {
          this.addResult('Environment', `${envFile} permissions`, 'WARNING', 
            `File permissions: ${mode} (should be 600)`);
        } else {
          this.addResult('Environment', `${envFile} permissions`, 'PASS', 
            `File permissions: ${mode}`);
        }

        // Check for sensitive data patterns
        const content = fs.readFileSync(envPath, 'utf8');
        const lines = content.split('\n').filter(line => line.trim() && !line.startsWith('#'));
        
        const sensitiveKeys = lines.filter(line => {
          const key = line.split('=')[0].toLowerCase();
          return key.includes('password') || key.includes('secret') || key.includes('key') || key.includes('token');
        });

        if (sensitiveKeys.length > 0) {
          this.addResult('Environment', `${envFile} sensitive data`, 'PASS', 
            `Found ${sensitiveKeys.length} sensitive environment variables`);
        }
      }
    });
  }

  auditSourceCode() {
    console.log('\n💻 Auditing source code...');
    
    const srcPath = path.join(this.projectRoot, 'src');
    if (!fs.existsSync(srcPath)) {
      this.addResult('Source Code', 'Source directory', 'WARNING', 'src directory not found');
      return;
    }

    let totalFiles = 0;
    let jsxFiles = 0;
    let tsFiles = 0;
    let testFiles = 0;
    let potentialIssues = [];

    const scanDirectory = (dir) => {
      const files = fs.readdirSync(dir);
      
      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          scanDirectory(filePath);
        } else if (stat.isFile()) {
          totalFiles++;
          
          if (file.endsWith('.tsx') || file.endsWith('.jsx')) {
            jsxFiles++;
          } else if (file.endsWith('.ts') || file.endsWith('.js')) {
            tsFiles++;
          } else if (file.includes('.test.') || file.includes('.spec.')) {
            testFiles++;
          }

          // Scan for potential security issues
          if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js') || file.endsWith('.jsx')) {
            try {
              const content = fs.readFileSync(filePath, 'utf8');
              
              // Check for dangerous patterns
              const dangerousPatterns = [
                { name: 'eval usage', pattern: /eval\s*\(/, severity: 'HIGH' },
                { name: 'innerHTML', pattern: /innerHTML\s*=/, severity: 'MEDIUM' },
                { name: 'document.write', pattern: /document\.write\s*\(/, severity: 'MEDIUM' },
                { name: 'localStorage without validation', pattern: /localStorage\.(getItem|setItem)/, severity: 'LOW' },
                { name: 'console.log in production', pattern: /console\.log\s*\(/, severity: 'LOW' }
              ];

              dangerousPatterns.forEach(({ name, pattern, severity }) => {
                const matches = content.match(pattern);
                if (matches) {
                  potentialIssues.push({
                    file: filePath.replace(this.projectRoot, '.'),
                    issue: name,
                    severity,
                    count: matches.length
                  });
                }
              });

            } catch (error) {
              // Skip files that can't be read
            }
          }
        }
      });
    };

    scanDirectory(srcPath);

    this.addResult('Source Code', 'File count', 'PASS', 
      `Scanned ${totalFiles} files (${jsxFiles} JSX, ${tsFiles} TS/JS, ${testFiles} tests)`);

    // Report potential issues
    const highSeverityIssues = potentialIssues.filter(i => i.severity === 'HIGH');
    const mediumSeverityIssues = potentialIssues.filter(i => i.severity === 'MEDIUM');
    const lowSeverityIssues = potentialIssues.filter(i => i.severity === 'LOW');

    if (highSeverityIssues.length > 0) {
      this.addResult('Source Code', 'High severity issues', 'FAIL', 
        `Found ${highSeverityIssues.length} high severity issues`, highSeverityIssues);
    }

    if (mediumSeverityIssues.length > 0) {
      this.addResult('Source Code', 'Medium severity issues', 'WARNING', 
        `Found ${mediumSeverityIssues.length} medium severity issues`, mediumSeverityIssues.slice(0, 5));
    }

    if (lowSeverityIssues.length > 0) {
      this.addResult('Source Code', 'Low severity issues', 'WARNING', 
        `Found ${lowSeverityIssues.length} low severity issues (review recommended)`);
    }

    if (potentialIssues.length === 0) {
      this.addResult('Source Code', 'Security patterns', 'PASS', 'No obvious security issues detected');
    }
  }

  auditConfiguration() {
    console.log('\n⚙️  Auditing configuration files...');
    
    const configFiles = [
      { name: 'next.config.js', required: false },
      { name: 'next.config.mjs', required: false },
      { name: 'tsconfig.json', required: true },
      { name: 'tailwind.config.js', required: false },
      { name: 'playwright.config.ts', required: false },
      { name: '.eslintrc.json', required: false },
      { name: 'docker-compose.yml', required: false }
    ];

    configFiles.forEach(({ name, required }) => {
      const configPath = path.join(this.projectRoot, name);
      if (fs.existsSync(configPath)) {
        this.addResult('Configuration', name, 'PASS', 'Configuration file present');
        
        // Check file permissions
        const stats = fs.statSync(configPath);
        const mode = (stats.mode & parseInt('777', 8)).toString(8);
        
        if (mode === '777') {
          this.addResult('Configuration', `${name} permissions`, 'WARNING', 
            `File permissions too permissive: ${mode}`);
        }
      } else if (required) {
        this.addResult('Configuration', name, 'FAIL', 'Required configuration file missing');
      } else {
        this.addResult('Configuration', name, 'WARNING', 'Optional configuration file missing');
      }
    });
  }

  auditBuildArtifacts() {
    console.log('\n🏗️  Auditing build artifacts...');
    
    const buildDirs = ['.next', 'dist', 'build', 'out'];
    const nodeModules = path.join(this.projectRoot, 'node_modules');
    
    buildDirs.forEach(dir => {
      const dirPath = path.join(this.projectRoot, dir);
      if (fs.existsSync(dirPath)) {
        const stats = fs.statSync(dirPath);
        const sizeInMB = this.getDirectorySize(dirPath) / (1024 * 1024);
        
        if (sizeInMB > 500) {
          this.addResult('Build', `${dir} size`, 'WARNING', 
            `Build directory is large: ${sizeInMB.toFixed(2)}MB`);
        } else {
          this.addResult('Build', `${dir} size`, 'PASS', 
            `Build directory size: ${sizeInMB.toFixed(2)}MB`);
        }
      }
    });

    if (fs.existsSync(nodeModules)) {
      const sizeInMB = this.getDirectorySize(nodeModules) / (1024 * 1024);
      this.addResult('Build', 'node_modules size', 'PASS', 
        `node_modules size: ${sizeInMB.toFixed(2)}MB`);
    }
  }

  getDirectorySize(dirPath) {
    let totalSize = 0;
    
    try {
      const files = fs.readdirSync(dirPath);
      
      files.forEach(file => {
        const filePath = path.join(dirPath, file);
        try {
          const stats = fs.statSync(filePath);
          
          if (stats.isFile()) {
            totalSize += stats.size;
          } else if (stats.isDirectory()) {
            totalSize += this.getDirectorySize(filePath);
          }
        } catch (error) {
          // Skip files/dirs that can't be accessed
        }
      });
    } catch (error) {
      // Skip directories that can't be read
    }
    
    return totalSize;
  }

  generateReport() {
    console.log('\n📊 STATIC AUDIT SUMMARY');
    console.log('=======================');
    
    const summary = {
      PASS: this.results.filter(r => r.status === 'PASS').length,
      WARNING: this.results.filter(r => r.status === 'WARNING').length,
      FAIL: this.results.filter(r => r.status === 'FAIL').length
    };

    console.log(`✅ Passed: ${summary.PASS}`);
    console.log(`⚠️  Warnings: ${summary.WARNING}`);
    console.log(`❌ Failed: ${summary.FAIL}`);
    console.log(`📋 Total checks: ${this.results.length}`);

    // Group results by category
    const categories = [...new Set(this.results.map(r => r.category))];
    console.log('\n📂 Results by category:');
    categories.forEach(category => {
      const categoryResults = this.results.filter(r => r.category === category);
      const categoryPassed = categoryResults.filter(r => r.status === 'PASS').length;
      const categoryWarnings = categoryResults.filter(r => r.status === 'WARNING').length;
      const categoryFailed = categoryResults.filter(r => r.status === 'FAIL').length;
      
      console.log(`  ${category}: ${categoryPassed} passed, ${categoryWarnings} warnings, ${categoryFailed} failed`);
    });

    // Save detailed report
    const reportPath = path.join(this.projectRoot, 'static-audit-report.json');
    fs.writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      summary,
      results: this.results,
      categories: categories.map(cat => ({
        name: cat,
        results: this.results.filter(r => r.category === cat)
      }))
    }, null, 2));

    console.log(`\n📄 Detailed report saved to: ${reportPath}`);

    return summary.FAIL === 0 ? 0 : 1;
  }

  async run() {
    console.log('🔍 STATIC WEB CONTAINER AUDIT');
    console.log('=============================');
    console.log(`Auditing project at: ${this.projectRoot}\n`);

    this.auditPackageJson();
    this.auditEnvironmentFiles();
    this.auditSourceCode();
    this.auditConfiguration();
    this.auditBuildArtifacts();

    return this.generateReport();
  }
}

async function main() {
  const auditor = new StaticAuditor();
  
  try {
    const exitCode = await auditor.run();
    
    console.log('\n🎯 Recommendations:');
    console.log('1. Review any failed checks immediately');
    console.log('2. Consider addressing warnings for better security');
    console.log('3. Run the full audit with server for complete analysis');
    console.log('4. Use: node audit-with-server.js for comprehensive testing');
    
    process.exit(exitCode);
  } catch (error) {
    console.error('❌ Static audit failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}