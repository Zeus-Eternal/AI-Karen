#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Starting Web Container Audit...\n');

// Ensure the web server is running
console.log('📡 Checking if web server is running...');
const testPorts = [8010];
let serverRunning = false;

for (const port of testPorts) {
  try {
    const response = execSync(`curl -s -o /dev/null -w "%{http_code}" http://localhost:${port}`, { encoding: 'utf8' });
    if (response.trim() === '200') {
      console.log(`✅ Web server is running on port ${port}\n`);
      serverRunning = true;
      process.env.AUDIT_URL = `http://localhost:${port}`;
      break;
    }
  } catch (error) {
    // Continue checking other ports
  }
}

if (!serverRunning) {
  console.log('⚠️  Web server not responding on port 8010.');
  console.log('Please start the server with: npm run dev or npm start (port 8010)');
  process.exit(1);
}

// Run the comprehensive audit
console.log('🚀 Running Playwright audit...');
try {
  const result = execSync('npx playwright test comprehensive-audit.spec.ts --reporter=html,json', {
    cwd: __dirname,
    stdio: 'inherit'
  });
  
  console.log('\n✅ Audit completed successfully!');
  console.log('📊 Check the HTML report at: playwright-report/index.html');
  console.log('📄 JSON results at: playwright-report/results.json');
  
} catch (error) {
  console.log('\n❌ Audit completed with issues. Check the reports for details.');
  console.log('📊 HTML report: playwright-report/index.html');
  console.log('📄 JSON results: playwright-report/results.json');
}

// Generate summary report
try {
  const reportPath = path.join(__dirname, 'playwright-report', 'results.json');
  if (fs.existsSync(reportPath)) {
    const results = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    
    console.log('\n📋 AUDIT SUMMARY');
    console.log('================');
    console.log(`Total tests: ${results.stats?.total || 'N/A'}`);
    console.log(`Passed: ${results.stats?.passed || 'N/A'}`);
    console.log(`Failed: ${results.stats?.failed || 'N/A'}`);
    console.log(`Duration: ${results.stats?.duration || 'N/A'}ms`);
  }
} catch (error) {
  console.log('Could not generate summary from results file');
}

console.log('\n🎯 Next steps:');
console.log('1. Review the HTML report for detailed findings');
console.log('2. Address any critical security or functionality issues');
console.log('3. Consider the warnings for optimization opportunities');
console.log('4. Re-run the audit after making changes');