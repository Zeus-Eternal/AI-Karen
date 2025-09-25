#!/usr/bin/env node

/**
 * Frontend UI Audit Script
 * Validates performance, accessibility, and cross-browser compatibility issues
 */

const fs = require('fs');
const path = require('path');

class FrontendAuditor {
  constructor() {
    this.results = {
      performance: [],
      accessibility: [],
      compatibility: [],
      security: [],
      structure: []
    };
  }

  // Analyze file structure and component sizes
  analyzeComponentStructure() {
    console.log('🔍 Analyzing component structure...');
    
    const componentsDir = path.join(__dirname, '../src/components');
    const chatDir = path.join(componentsDir, 'chat');
    
    try {
      // Check ChatInterface size
      const chatInterfacePath = path.join(chatDir, 'ChatInterface.tsx');
      if (fs.existsSync(chatInterfacePath)) {
        const content = fs.readFileSync(chatInterfacePath, 'utf8');
        const lineCount = content.split('\n').length;
        
        this.results.structure.push({
          level: lineCount > 1000 ? 'critical' : 'warning',
          message: `ChatInterface component is ${lineCount} lines (recommended: < 500)`,
          details: { file: 'ChatInterface.tsx', lines: lineCount },
          suggestion: 'Break into smaller components: MessageList, MessageInput, ChatContainer'
        });
      }

      // Check for large files
      const checkFileSize = (filePath, maxLines = 300) => {
        if (fs.existsSync(filePath)) {
          const content = fs.readFileSync(filePath, 'utf8');
          const lineCount = content.split('\n').length;
          if (lineCount > maxLines) {
            return { file: path.basename(filePath), lines: lineCount };
          }
        }
        return null;
      };

      const largeFiles = [];
      const componentFiles = this.getAllFiles(componentsDir, '.tsx');
      
      componentFiles.forEach(file => {
        const result = checkFileSize(file, 300);
        if (result) largeFiles.push(result);
      });

      if (largeFiles.length > 0) {
        this.results.structure.push({
          level: 'warning',
          message: `${largeFiles.length} components exceed recommended size`,
          details: { largeFiles },
          suggestion: 'Consider component splitting and code splitting'
        });
      }

    } catch (error) {
      console.error('Error analyzing structure:', error);
    }
  }

  // Analyze accessibility issues
  analyzeAccessibility() {
    console.log('🔍 Analyzing accessibility patterns...');
    
    // Check for ARIA patterns in components
    const componentsDir = path.join(__dirname, '../src/components');
    const componentFiles = this.getAllFiles(componentsDir, '.tsx');
    
    let ariaIssues = 0;
    let keyboardIssues = 0;

    componentFiles.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      
      // Check for ARIA landmarks
      if (!content.includes('role=') && !content.includes('aria-')) {
        ariaIssues++;
      }
      
      // Check for keyboard navigation
      if (content.includes('onClick') && !content.includes('onKeyDown') && 
          !content.includes('tabIndex') && content.includes('button')) {
        keyboardIssues++;
      }
    });

    if (ariaIssues > 0) {
      this.results.accessibility.push({
        level: 'critical',
        message: `${ariaIssues} components missing ARIA attributes`,
        details: { componentsWithIssues: ariaIssues },
        suggestion: 'Add proper ARIA roles, labels, and landmarks'
      });
    }

    if (keyboardIssues > 0) {
      this.results.accessibility.push({
        level: 'warning',
        message: `${keyboardIssues} components may have keyboard navigation issues`,
        details: { componentsWithIssues: keyboardIssues },
        suggestion: 'Ensure all interactive elements are keyboard accessible'
      });
    }
  }

  // Analyze performance patterns
  analyzePerformance() {
    console.log('🔍 Analyzing performance patterns...');
    
    const componentsDir = path.join(__dirname, '../src/components');
    const componentFiles = this.getAllFiles(componentsDir, '.tsx');
    
    let virtualizationMissing = false;
    let memoizationMissing = false;

    componentFiles.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      const fileName = path.basename(file);
      
      // Check for virtualization in chat/list components
      if (fileName.includes('Chat') || fileName.includes('List')) {
        if (!content.includes('react-window') && !content.includes('virtual') && 
            content.includes('map') && content.includes('messages')) {
          virtualizationMissing = true;
        }
      }
      
      // Check for memoization
      if (content.includes('useState') && content.includes('props') && 
          !content.includes('React.memo') && !content.includes('useMemo')) {
        memoizationMissing = true;
      }
    });

    if (virtualizationMissing) {
      this.results.performance.push({
        level: 'critical',
        message: 'Message lists missing virtualization',
        details: { issue: 'Long lists will impact performance' },
        suggestion: 'Implement react-window for virtualized scrolling'
      });
    }

    if (memoizationMissing) {
      this.results.performance.push({
        level: 'warning',
        message: 'Components missing proper memoization',
        details: { issue: 'Potential unnecessary re-renders' },
        suggestion: 'Use React.memo and useMemo for expensive computations'
      });
    }
  }

  // Analyze cross-browser compatibility
  analyzeCompatibility() {
    console.log('🔍 Analyzing cross-browser compatibility...');
    
    const packageJsonPath = path.join(__dirname, '../package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    // Check browser support in dependencies
    const modernDeps = ['framer-motion', 'react-spring', 'intersection-observer'];
    const compatibilityIssues = [];

    modernDeps.forEach(dep => {
      if (packageJson.dependencies[dep] || packageJson.devDependencies[dep]) {
        compatibilityIssues.push(dep);
      }
    });

    if (compatibilityIssues.length > 0) {
      this.results.compatibility.push({
        level: 'warning',
        message: `Modern dependencies may have compatibility issues: ${compatibilityIssues.join(', ')}`,
        details: { dependencies: compatibilityIssues },
        suggestion: 'Check browser support and consider polyfills'
      });
    }

    // Check for CSS Grid usage
    const stylesDir = path.join(__dirname, '../src/styles');
    const styleFiles = this.getAllFiles(stylesDir, '.css');
    
    let cssGridUsage = false;
    styleFiles.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      if (content.includes('display: grid') || content.includes('grid-template')) {
        cssGridUsage = true;
      }
    });

    if (cssGridUsage) {
      this.results.compatibility.push({
        level: 'info',
        message: 'CSS Grid detected (IE11 not supported)',
        details: { feature: 'CSS Grid Layout' },
        suggestion: 'Ensure fallbacks for older browsers if needed'
      });
    }
  }

  // Analyze security patterns
  analyzeSecurity() {
    console.log('🔍 Analyzing security patterns...');
    
    const componentsDir = path.join(__dirname, '../src/components');
    const componentFiles = this.getAllFiles(componentsDir, '.tsx');
    
    let xssRisks = 0;
    let inputSanitization = false;

    componentFiles.forEach(file => {
      const content = fs.readFileSync(file, 'utf8');
      
      // Check for dangerous HTML insertion
      if (content.includes('dangerouslySetInnerHTML') && !content.includes('DOMPurify')) {
        xssRisks++;
      }
      
      // Check for input sanitization
      if (content.includes('sanitize') || content.includes('DOMPurify')) {
        inputSanitization = true;
      }
    });

    if (xssRisks > 0) {
      this.results.security.push({
        level: 'critical',
        message: `${xssRisks} components use dangerouslySetInnerHTML without sanitization`,
        details: { componentsWithRisks: xssRisks },
        suggestion: 'Use DOMPurify for HTML sanitization'
      });
    }

    if (!inputSanitization) {
      this.results.security.push({
        level: 'warning',
        message: 'Input sanitization may be insufficient',
        details: { issue: 'User input not properly sanitized' },
        suggestion: 'Implement comprehensive input validation and sanitization'
      });
    }
  }

  // Utility function to get all files recursively
  getAllFiles(dir, extension) {
    let results = [];
    const list = fs.readdirSync(dir);
    
    list.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat && stat.isDirectory()) {
        results = results.concat(this.getAllFiles(filePath, extension));
      } else if (file.endsWith(extension)) {
        results.push(filePath);
      }
    });
    
    return results;
  }

  // Generate comprehensive report
  generateReport() {
    const totalIssues = Object.values(this.results).reduce((sum, category) => sum + category.length, 0);
    const criticalIssues = Object.values(this.results).flat().filter(issue => issue.level === 'critical').length;
    const warnings = Object.values(this.results).flat().filter(issue => issue.level === 'warning').length;

    console.log('\n' + '='.repeat(80));
    console.log('🚀 FRONTEND UI AUDIT REPORT');
    console.log('='.repeat(80));
    console.log(`📊 Summary: ${totalIssues} issues found (${criticalIssues} critical, ${warnings} warnings)`);
    console.log('='.repeat(80));

    Object.entries(this.results).forEach(([category, issues]) => {
      if (issues.length > 0) {
        console.log(`\n${category.toUpperCase()}:`);
        issues.forEach((issue, index) => {
          const emoji = issue.level === 'critical' ? '🚨' : issue.level === 'warning' ? '⚠️' : 'ℹ️';
          console.log(`${emoji} ${issue.message}`);
          if (issue.suggestion) {
            console.log(`   💡 Suggestion: ${issue.suggestion}`);
          }
          if (index < issues.length - 1) console.log('   ---');
        });
      }
    });

    console.log('\n' + '='.repeat(80));
    console.log('🎯 RECOMMENDATIONS');
    console.log('='.repeat(80));

    // Generate prioritized recommendations
    const recommendations = [];
    
    if (criticalIssues > 0) {
      recommendations.push('1. IMMEDIATE: Fix critical accessibility and security issues');
    }
    
    if (this.results.performance.length > 0) {
      recommendations.push('2. HIGH: Implement performance optimizations (virtualization, memoization)');
    }
    
    if (this.results.accessibility.length > 0) {
      recommendations.push('3. MEDIUM: Improve accessibility (ARIA, keyboard navigation)');
    }
    
    if (this.results.compatibility.length > 0) {
      recommendations.push('4. LOW: Address cross-browser compatibility concerns');
    }

    recommendations.forEach(rec => console.log(`✅ ${rec}`));

    return {
      totalIssues,
      criticalIssues,
      warnings,
      results: this.results,
      recommendations
    };
  }

  // Run all audits
  run() {
    console.log('Starting frontend UI audit...\n');
    
    this.analyzeComponentStructure();
    this.analyzeAccessibility();
    this.analyzePerformance();
    this.analyzeCompatibility();
    this.analyzeSecurity();
    
    return this.generateReport();
  }
}

// Run if called directly
if (require.main === module) {
  const auditor = new FrontendAuditor();
  auditor.run();
}

module.exports = FrontendAuditor;