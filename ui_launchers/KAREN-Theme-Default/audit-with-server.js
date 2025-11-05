#!/usr/bin/env node

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class ServerManager {
  constructor() {
    this.serverProcess = null;
    this.serverReady = false;
  }

  async startServer() {
    return new Promise((resolve, reject) => {
      console.log('🚀 Starting development server...');
      
      // Start the Next.js dev server
      this.serverProcess = spawn('npm', ['run', 'dev'], {
        cwd: __dirname,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let output = '';
      
      this.serverProcess.stdout.on('data', (data) => {
        output += data.toString();
        process.stdout.write(data);
        
        // Check if server is ready
        if (output.includes('Ready in') || output.includes('Local:') || output.includes('ready')) {
          this.serverReady = true;
          console.log('✅ Server is ready!');
          resolve();
        }
      });

      this.serverProcess.stderr.on('data', (data) => {
        process.stderr.write(data);
      });

      this.serverProcess.on('error', (error) => {
        console.error('❌ Failed to start server:', error);
        reject(error);
      });

      // Timeout after 60 seconds
      setTimeout(() => {
        if (!this.serverReady) {
          console.log('⚠️  Server startup timeout, proceeding anyway...');
          resolve();
        }
      }, 60000);
    });
  }

  async stopServer() {
    if (this.serverProcess) {
      console.log('🛑 Stopping server...');
      this.serverProcess.kill('SIGTERM');
      
      // Wait a bit for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      if (!this.serverProcess.killed) {
        this.serverProcess.kill('SIGKILL');
      }
    }
  }

  async waitForServer(maxAttempts = 30) {
    console.log('⏳ Waiting for server to be accessible...');
    
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = execSync('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000', { 
          encoding: 'utf8',
          timeout: 5000 
        });
        
        if (response.trim() === '200') {
          console.log('✅ Server is accessible!');
          return true;
        }
      } catch (error) {
        // Server not ready yet
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      process.stdout.write('.');
    }
    
    console.log('\n⚠️  Server may not be fully ready, but proceeding with audit...');
    return false;
  }
}

async function runQuickAudit() {
  console.log('\n🔍 Running Quick Audit...');
  try {
    execSync('node quick-audit.js', { 
      cwd: __dirname, 
      stdio: 'inherit',
      env: { ...process.env, AUDIT_URL: 'http://localhost:8000' }
    });
  } catch (error) {
    console.log('Quick audit completed with issues');
  }
}

async function runPlaywrightAudit() {
  console.log('\n🎭 Running Playwright Comprehensive Audit...');
  try {
    execSync('npx playwright test comprehensive-audit.spec.ts --reporter=html,json', {
      cwd: __dirname,
      stdio: 'inherit'
    });
    
    console.log('\n✅ Playwright audit completed!');
    console.log('📊 Check the HTML report at: playwright-report/index.html');
    
  } catch (error) {
    console.log('\n⚠️  Playwright audit completed with issues');
    console.log('📊 Check the HTML report at: playwright-report/index.html');
  }
}

async function generateFinalReport() {
  console.log('\n📋 Generating Final Report...');
  
  const reports = [];
  
  // Read quick audit report
  const quickReportPath = path.join(__dirname, 'quick-audit-report.json');
  if (fs.existsSync(quickReportPath)) {
    const quickReport = JSON.parse(fs.readFileSync(quickReportPath, 'utf8'));
    reports.push({ type: 'Quick Audit', ...quickReport });
  }
  
  // Read Playwright report
  const playwrightReportPath = path.join(__dirname, 'playwright-report', 'results.json');
  if (fs.existsSync(playwrightReportPath)) {
    const playwrightReport = JSON.parse(fs.readFileSync(playwrightReportPath, 'utf8'));
    reports.push({ type: 'Playwright Audit', ...playwrightReport });
  }
  
  // Generate combined report
  const finalReport = {
    timestamp: new Date().toISOString(),
    reports,
    summary: {
      totalAudits: reports.length,
      quickAuditPassed: reports.find(r => r.type === 'Quick Audit')?.summary?.PASS || 0,
      quickAuditWarnings: reports.find(r => r.type === 'Quick Audit')?.summary?.WARNING || 0,
      quickAuditFailed: reports.find(r => r.type === 'Quick Audit')?.summary?.FAIL || 0,
      playwrightTests: reports.find(r => r.type === 'Playwright Audit')?.stats?.total || 0,
      playwrightPassed: reports.find(r => r.type === 'Playwright Audit')?.stats?.passed || 0,
      playwrightFailed: reports.find(r => r.type === 'Playwright Audit')?.stats?.failed || 0
    }
  };
  
  const finalReportPath = path.join(__dirname, 'final-audit-report.json');
  fs.writeFileSync(finalReportPath, JSON.stringify(finalReport, null, 2));
  
  console.log('📄 Final report saved to:', finalReportPath);
  console.log('\n🎯 AUDIT COMPLETE!');
  console.log('================');
  console.log(`Quick Audit: ${finalReport.summary.quickAuditPassed} passed, ${finalReport.summary.quickAuditWarnings} warnings, ${finalReport.summary.quickAuditFailed} failed`);
  console.log(`Playwright: ${finalReport.summary.playwrightPassed}/${finalReport.summary.playwrightTests} tests passed`);
  
  return finalReport;
}

async function main() {
  const serverManager = new ServerManager();
  
  try {
    // Check if server is already running
    let serverWasRunning = false;
    try {
      const response = execSync('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000', { 
        encoding: 'utf8',
        timeout: 5000 
      });
      serverWasRunning = response.trim() === '200';
    } catch (error) {
      // Server not running
    }
    
    if (!serverWasRunning) {
      await serverManager.startServer();
      await serverManager.waitForServer();
    } else {
      console.log('✅ Server already running');
    }
    
    // Run audits
    await runQuickAudit();
    await runPlaywrightAudit();
    
    // Generate final report
    const finalReport = await generateFinalReport();
    
    // Cleanup
    if (!serverWasRunning) {
      await serverManager.stopServer();
    }
    
    // Exit with appropriate code
    const hasFailures = finalReport.summary.quickAuditFailed > 0 || finalReport.summary.playwrightFailed > 0;
    process.exit(hasFailures ? 1 : 0);
    
  } catch (error) {
    console.error('❌ Audit process failed:', error.message);
    await serverManager.stopServer();
    process.exit(1);
  }
}

// Handle cleanup on exit
process.on('SIGINT', async () => {
  console.log('\n🛑 Audit interrupted, cleaning up...');
  process.exit(1);
});

process.on('SIGTERM', async () => {
  console.log('\n🛑 Audit terminated, cleaning up...');
  process.exit(1);
});

if (require.main === module) {
  main();
}