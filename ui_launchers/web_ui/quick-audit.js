#!/usr/bin/env node

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

class QuickAuditor {
  constructor() {
    this.results = [];
    this.baseUrl = process.env.AUDIT_URL || 'http://localhost:8000';
  }

  addResult(category, test, status, message, details = null) {
    this.results.push({ category, test, status, message, details });
    const icon = status === 'PASS' ? '✅' : status === 'WARNING' ? '⚠️' : '❌';
    console.log(`${icon} ${category} - ${test}: ${message}`);
  }

  async makeRequest(url) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https') ? https : http;
      const req = client.get(url, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, data }));
      });
      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
    });
  }

  async auditServer() {
    console.log('\n🔍 QUICK WEB CONTAINER AUDIT');
    console.log('============================\n');

    // Check if server is running
    try {
      const response = await this.makeRequest(this.baseUrl);
      this.addResult('Server', 'Availability', 'PASS', `Server responding with status ${response.status}`);
      
      // Check response headers
      const headers = response.headers;
      const securityHeaders = {
        'x-frame-options': 'X-Frame-Options',
        'x-content-type-options': 'X-Content-Type-Options',
        'x-xss-protection': 'X-XSS-Protection',
        'strict-transport-security': 'Strict-Transport-Security',
        'content-security-policy': 'Content-Security-Policy'
      };

      Object.entries(securityHeaders).forEach(([header, displayName]) => {
        if (headers[header]) {
          this.addResult('Security', displayName, 'PASS', `Header present: ${headers[header]}`);
        } else {
          this.addResult('Security', displayName, 'WARNING', `Missing security header: ${header}`);
        }
      });

      // Check for sensitive information in response
      const content = response.data.toLowerCase();
      const sensitivePatterns = [
        { pattern: /password\s*[:=]\s*['"]\w+['"]/, name: 'Password exposure' },
        { pattern: /api[_-]?key\s*[:=]\s*['"]\w+['"]/, name: 'API key exposure' },
        { pattern: /secret\s*[:=]\s*['"]\w+['"]/, name: 'Secret exposure' },
        { pattern: /token\s*[:=]\s*['"]\w+['"]/, name: 'Token exposure' }
      ];

      let foundSensitive = false;
      sensitivePatterns.forEach(({ pattern, name }) => {
        if (pattern.test(content)) {
          foundSensitive = true;
          this.addResult('Security', 'Data Exposure', 'FAIL', `Potential ${name} in HTML`);
        }
      });

      if (!foundSensitive) {
        this.addResult('Security', 'Data Exposure', 'PASS', 'No obvious sensitive data in HTML');
      }

    } catch (error) {
      this.addResult('Server', 'Availability', 'FAIL', `Server not accessible: ${error.message}`);
      return;
    }

    // Test API endpoints
    const apiEndpoints = [
      '/api/health',
      '/api/admin/users',
      '/api/admin/system/config',
      '/api/auth/login'
    ];

    console.log('\n🔌 Testing API Endpoints...');
    for (const endpoint of apiEndpoints) {
      try {
        const response = await this.makeRequest(this.baseUrl + endpoint);
        const status = response.status;
        
        if (status === 200) {
          this.addResult('API', `${endpoint}`, 'PASS', `Accessible (${status})`);
        } else if (status === 401 || status === 403) {
          this.addResult('API', `${endpoint}`, 'PASS', `Protected (${status})`);
        } else if (status === 404) {
          this.addResult('API', `${endpoint}`, 'WARNING', `Not found (${status})`);
        } else {
          this.addResult('API', `${endpoint}`, 'WARNING', `Unexpected status (${status})`);
        }
      } catch (error) {
        this.addResult('API', `${endpoint}`, 'FAIL', `Request failed: ${error.message}`);
      }
    }
  }

  async auditFileSystem() {
    console.log('\n📁 Checking File System Security...');
    
    const sensitiveFiles = [
      '.env',
      '.env.local',
      'config.json',
      'package.json',
      'docker-compose.yml'
    ];

    sensitiveFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      if (fs.existsSync(filePath)) {
        try {
          const stats = fs.statSync(filePath);
          const mode = (stats.mode & parseInt('777', 8)).toString(8);
          
          if (file.startsWith('.env') && mode !== '600') {
            this.addResult('FileSystem', `${file} permissions`, 'WARNING', 
              `File permissions: ${mode} (should be 600 for env files)`);
          } else {
            this.addResult('FileSystem', `${file} permissions`, 'PASS', 
              `File permissions: ${mode}`);
          }
        } catch (error) {
          this.addResult('FileSystem', `${file} check`, 'FAIL', 
            `Could not check file: ${error.message}`);
        }
      }
    });

    // Check for backup files
    const backupPatterns = ['.bak', '.backup', '.old', '.tmp', '~'];
    const files = fs.readdirSync(__dirname);
    
    const backupFiles = files.filter(file => 
      backupPatterns.some(pattern => file.endsWith(pattern))
    );

    if (backupFiles.length === 0) {
      this.addResult('FileSystem', 'Backup files', 'PASS', 'No backup files found in web directory');
    } else {
      this.addResult('FileSystem', 'Backup files', 'WARNING', 
        `Found ${backupFiles.length} backup files: ${backupFiles.join(', ')}`);
    }
  }

  generateReport() {
    console.log('\n📊 AUDIT SUMMARY');
    console.log('================');
    
    const summary = {
      PASS: this.results.filter(r => r.status === 'PASS').length,
      WARNING: this.results.filter(r => r.status === 'WARNING').length,
      FAIL: this.results.filter(r => r.status === 'FAIL').length
    };

    console.log(`✅ Passed: ${summary.PASS}`);
    console.log(`⚠️  Warnings: ${summary.WARNING}`);
    console.log(`❌ Failed: ${summary.FAIL}`);
    console.log(`📋 Total checks: ${this.results.length}`);

    // Save results to file
    const reportPath = path.join(__dirname, 'quick-audit-report.json');
    fs.writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      summary,
      results: this.results
    }, null, 2));

    console.log(`\n📄 Detailed report saved to: ${reportPath}`);

    if (summary.FAIL > 0) {
      console.log('\n🚨 CRITICAL ISSUES FOUND - Please review failed checks');
      return 1;
    } else if (summary.WARNING > 0) {
      console.log('\n⚠️  Some warnings found - Consider reviewing for optimization');
      return 0;
    } else {
      console.log('\n🎉 All checks passed!');
      return 0;
    }
  }
}

async function main() {
  const auditor = new QuickAuditor();
  
  try {
    await auditor.auditServer();
    await auditor.auditFileSystem();
    const exitCode = auditor.generateReport();
    process.exit(exitCode);
  } catch (error) {
    console.error('❌ Audit failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}