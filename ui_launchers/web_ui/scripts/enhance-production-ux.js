#!/usr/bin/env node

/**
 * Production UX Enhancement Script
 * 
 * Enhances UI/UX for production standards including accessibility compliance,
 * responsive design validation, theme consistency, and error boundaries.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SRC_DIR = path.join(__dirname, '../src');
const COMPONENTS_DIR = path.join(SRC_DIR, 'components');
const STYLES_DIR = path.join(SRC_DIR, 'styles');

class ProductionUXEnhancer {
  constructor() {
    this.processedComponents = 0;
    this.enhancedComponents = 0;
    this.accessibilityIssues = [];
    this.responsiveIssues = [];
    this.themeIssues = [];
    this.errors = [];
  }

  // Enhance accessibility compliance
  enhanceAccessibility(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Add missing ARIA labels to interactive elements
      const interactiveElements = [
        { tag: 'button', attr: 'aria-label' },
        { tag: 'input', attr: 'aria-label' },
        { tag: 'select', attr: 'aria-label' },
        { tag: 'textarea', attr: 'aria-label' },
      ];

      interactiveElements.forEach(({ tag, attr }) => {
        const regex = new RegExp(`<${tag}(?![^>]*${attr})([^>]*)>`, 'gi');
        content = content.replace(regex, (match, attributes) => {
          // Skip if already has aria-label, aria-labelledby, or title
          if (attributes.includes('aria-label') || 
              attributes.includes('aria-labelledby') || 
              attributes.includes('title')) {
            return match;
          }

          // Add appropriate aria-label based on context
          let ariaLabel = '';
          if (attributes.includes('type="submit"')) {
            ariaLabel = ' aria-label="Submit form"';
          } else if (attributes.includes('type="search"')) {
            ariaLabel = ' aria-label="Search"';
          } else if (attributes.includes('className') && attributes.includes('close')) {
            ariaLabel = ' aria-label="Close"';
          } else if (tag === 'select') {
            ariaLabel = ' aria-label="Select option"';
          } else {
            ariaLabel = ` aria-label="${tag.charAt(0).toUpperCase() + tag.slice(1)}"`;
          }

          hasChanges = true;
          return `<${tag}${attributes}${ariaLabel}>`;
        });
      });

      // Add role attributes where missing
      const rolePatterns = [
        { pattern: /<div[^>]*className[^>]*dialog[^>]*>/gi, role: 'dialog' },
        { pattern: /<div[^>]*className[^>]*modal[^>]*>/gi, role: 'dialog' },
        { pattern: /<div[^>]*className[^>]*tooltip[^>]*>/gi, role: 'tooltip' },
        { pattern: /<div[^>]*className[^>]*alert[^>]*>/gi, role: 'alert' },
        { pattern: /<nav(?![^>]*role)/gi, role: 'navigation' },
        { pattern: /<main(?![^>]*role)/gi, role: 'main' },
        { pattern: /<aside(?![^>]*role)/gi, role: 'complementary' },
      ];

      rolePatterns.forEach(({ pattern, role }) => {
        content = content.replace(pattern, (match) => {
          if (match.includes('role=')) return match;
          hasChanges = true;
          return match.replace('>', ` role="${role}">`);
        });
      });

      // Add focus management for modals and dialogs
      if (content.includes('dialog') || content.includes('modal')) {
        if (!content.includes('useEffect') && !content.includes('focus')) {
          const focusManagement = `
  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);`;

          if (content.includes('export')) {
            content = content.replace(
              /^(import.*from 'react';)$/m,
              `$1\nimport { useEffect } from 'react';`
            );
            content = content.replace(
              /^(\s*return\s*\()/m,
              `${focusManagement}\n\n$1`
            );
            hasChanges = true;
          }
        }
      }

      if (hasChanges) {
        fs.writeFileSync(filePath, content);
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error enhancing accessibility in ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Validate and enhance responsive design
  enhanceResponsiveDesign(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Add responsive classes where missing
      const responsivePatterns = [
        {
          pattern: /className="([^"]*\bw-\d+[^"]*)"(?![^>]*sm:|md:|lg:|xl:)/g,
          replacement: (match, classes) => {
            if (classes.includes('sm:') || classes.includes('md:')) return match;
            return match.replace(classes, `${classes} sm:w-auto md:w-full`);
          }
        },
        {
          pattern: /className="([^"]*\btext-\w+[^"]*)"(?![^>]*sm:|md:|lg:|xl:)/g,
          replacement: (match, classes) => {
            if (classes.includes('sm:') || classes.includes('md:')) return match;
            if (classes.includes('text-xs')) {
              return match.replace(classes, `${classes} sm:text-sm md:text-base`);
            }
            if (classes.includes('text-sm')) {
              return match.replace(classes, `${classes} md:text-base lg:text-lg`);
            }
            return match;
          }
        },
        {
          pattern: /className="([^"]*\bp-\d+[^"]*)"(?![^>]*sm:|md:|lg:|xl:)/g,
          replacement: (match, classes) => {
            if (classes.includes('sm:') || classes.includes('md:')) return match;
            return match.replace(classes, `${classes} sm:p-4 md:p-6`);
          }
        }
      ];

      responsivePatterns.forEach(({ pattern, replacement }) => {
        const newContent = content.replace(pattern, replacement);
        if (newContent !== content) {
          content = newContent;
          hasChanges = true;
        }
      });

      // Add mobile-first media queries for custom CSS
      if (filePath.endsWith('.css') && content.includes('@media')) {
        const mobileFirstPattern = /@media\s*\(\s*max-width:/g;
        if (mobileFirstPattern.test(content)) {
          // Convert max-width to min-width (mobile-first approach)
          content = content.replace(
            /@media\s*\(\s*max-width:\s*(\d+px)\s*\)/g,
            '@media (min-width: $1)'
          );
          hasChanges = true;
        }
      }

      if (hasChanges) {
        fs.writeFileSync(filePath, content);
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error enhancing responsive design in ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Validate theme consistency
  validateThemeConsistency(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const issues = [];

      // Check for hardcoded colors instead of theme variables
      const hardcodedColors = content.match(/(#[0-9a-fA-F]{3,6}|rgb\(|rgba\()/g);
      if (hardcodedColors) {
        issues.push(`Hardcoded colors found: ${hardcodedColors.join(', ')}`);
      }

      // Check for missing dark mode classes
      const lightModeClasses = content.match(/\b(bg-white|text-black|border-gray-200)\b/g);
      if (lightModeClasses && !content.includes('dark:')) {
        issues.push('Light mode classes without dark mode variants');
      }

      // Check for inconsistent spacing
      const spacingClasses = content.match(/\b(p-\d+|m-\d+|px-\d+|py-\d+|mx-\d+|my-\d+)\b/g);
      if (spacingClasses) {
        const uniqueSpacing = [...new Set(spacingClasses)];
        if (uniqueSpacing.length > 8) {
          issues.push('Too many different spacing values - consider using consistent spacing scale');
        }
      }

      if (issues.length > 0) {
        this.themeIssues.push({
          file: path.relative(SRC_DIR, filePath),
          issues
        });
      }

      return issues.length === 0;
    } catch (error) {
      this.errors.push(`Error validating theme consistency in ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Add error boundaries where missing
  addErrorBoundaries(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Add error boundary to page components
      if (filePath.includes('/app/') && filePath.endsWith('/page.tsx')) {
        if (!content.includes('ErrorBoundary') && !content.includes('error.tsx')) {
          const errorBoundaryImport = `import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';`;
          const returnMatch = content.match(/return\s*\(\s*(<[^>]+>)/);
          
          if (returnMatch) {
            // Add import
            content = content.replace(
              /^(import.*from.*';)$/m,
              `$1\n${errorBoundaryImport}`
            );

            // Wrap return content with ErrorBoundary
            content = content.replace(
              /return\s*\(\s*(<[^>]+>[\s\S]*<\/[^>]+>)\s*\);/,
              `return (
    <ErrorBoundary>
      $1
    </ErrorBoundary>
  );`
            );
            hasChanges = true;
          }
        }
      }

      // Add error boundaries to complex components
      if (content.includes('useState') && content.includes('useEffect') && 
          !content.includes('ErrorBoundary') && !filePath.includes('ErrorBoundary')) {
        const componentName = path.basename(filePath, '.tsx');
        if (componentName.includes('Dashboard') || componentName.includes('Manager') || 
            componentName.includes('Interface')) {
          
          const errorBoundaryImport = `import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';`;
          const returnMatch = content.match(/return\s*\(\s*(<[^>]+>)/);
          
          if (returnMatch && !content.includes(errorBoundaryImport)) {
            content = content.replace(
              /^(import.*from.*';)$/m,
              `$1\n${errorBoundaryImport}`
            );

            content = content.replace(
              /return\s*\(\s*(<[^>]+>[\s\S]*<\/[^>]+>)\s*\);/,
              `return (
    <ErrorBoundary fallback={<div>Something went wrong in ${componentName}</div>}>
      $1
    </ErrorBoundary>
  );`
            );
            hasChanges = true;
          }
        }
      }

      if (hasChanges) {
        fs.writeFileSync(filePath, content);
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error adding error boundaries to ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Add loading states where missing
  addLoadingStates(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Add loading states to components with async operations
      if (content.includes('useState') && content.includes('useEffect') && 
          !content.includes('loading') && !content.includes('Loading')) {
        
        // Add loading state
        const loadingStatePattern = /const\s+\[([^,]+),\s*set[A-Z][^]]*\]\s*=\s*useState/;
        const firstStateMatch = content.match(loadingStatePattern);
        
        if (firstStateMatch && content.includes('fetch') || content.includes('api')) {
          const loadingState = `const [loading, setLoading] = useState(false);`;
          
          // Add loading state after first useState
          content = content.replace(
            firstStateMatch[0],
            `${firstStateMatch[0]}\n  ${loadingState}`
          );

          // Add loading UI
          const returnMatch = content.match(/return\s*\(\s*(<[^>]+>)/);
          if (returnMatch) {
            content = content.replace(
              /return\s*\(\s*(<[^>]+>[\s\S]*<\/[^>]+>)\s*\);/,
              `if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <span className="ml-2">Loading...</span>
      </div>
    );
  }

  return (
    $1
  );`
            );
            hasChanges = true;
          }
        }
      }

      if (hasChanges) {
        fs.writeFileSync(filePath, content);
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error adding loading states to ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Create production-ready global styles
  createProductionStyles() {
    console.log('🎨 Creating production-ready global styles...');

    const productionGlobalCSS = `/* Production Global Styles */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Base layer - Production optimizations */
@layer base {
  * {
    @apply border-border;
  }
  
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  /* Improved focus styles for accessibility */
  *:focus-visible {
    @apply outline-2 outline-offset-2 outline-blue-500;
  }

  /* Smooth scrolling for better UX */
  html {
    scroll-behavior: smooth;
  }

  /* Prevent layout shift */
  img, video {
    height: auto;
    max-width: 100%;
  }

  /* Better text rendering */
  body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }
}

/* Component layer - Production components */
@layer components {
  /* Loading spinner */
  .loading-spinner {
    @apply inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent;
    width: 1em;
    height: 1em;
  }

  /* Error states */
  .error-message {
    @apply text-red-600 dark:text-red-400 text-sm font-medium;
  }

  .error-boundary {
    @apply p-4 border border-red-200 dark:border-red-800 rounded-lg bg-red-50 dark:bg-red-900/20;
  }

  /* Success states */
  .success-message {
    @apply text-green-600 dark:text-green-400 text-sm font-medium;
  }

  /* Interactive elements */
  .interactive-element {
    @apply transition-all duration-200 ease-in-out;
  }

  .interactive-element:hover {
    @apply scale-105;
  }

  .interactive-element:active {
    @apply scale-95;
  }

  /* Card components */
  .card {
    @apply bg-card text-card-foreground rounded-lg border shadow-sm;
  }

  .card-header {
    @apply p-6 pb-4;
  }

  .card-content {
    @apply p-6 pt-0;
  }

  /* Form elements */
  .form-input {
    @apply w-full px-3 py-2 border border-input bg-background rounded-md text-sm;
    @apply focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent;
    @apply disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .form-label {
    @apply text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70;
  }

  /* Button variants */
  .btn {
    @apply inline-flex items-center justify-center rounded-md text-sm font-medium;
    @apply transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring;
    @apply disabled:pointer-events-none disabled:opacity-50;
  }

  .btn-primary {
    @apply bg-primary text-primary-foreground hover:bg-primary/90;
  }

  .btn-secondary {
    @apply bg-secondary text-secondary-foreground hover:bg-secondary/80;
  }

  .btn-destructive {
    @apply bg-destructive text-destructive-foreground hover:bg-destructive/90;
  }

  .btn-ghost {
    @apply hover:bg-accent hover:text-accent-foreground;
  }

  /* Navigation */
  .nav-link {
    @apply text-sm font-medium transition-colors hover:text-primary;
  }

  .nav-link.active {
    @apply text-primary;
  }
}

/* Utility layer - Production utilities */
@layer utilities {
  /* Screen reader only */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* Truncate text */
  .truncate-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .truncate-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Responsive containers */
  .container-responsive {
    @apply w-full mx-auto px-4 sm:px-6 lg:px-8;
    max-width: 1200px;
  }

  /* Animation utilities */
  .animate-fade-in {
    animation: fadeIn 0.3s ease-in-out;
  }

  .animate-slide-up {
    animation: slideUp 0.3s ease-out;
  }

  .animate-scale-in {
    animation: scaleIn 0.2s ease-out;
  }
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.95);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

/* Dark mode optimizations */
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .btn {
    border: 2px solid currentColor;
  }
  
  .card {
    border-width: 2px;
  }
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
  
  * {
    color: black !important;
    background: white !important;
  }
}`;

    const globalStylesPath = path.join(STYLES_DIR, 'globals.css');
    fs.writeFileSync(globalStylesPath, productionGlobalCSS);
    console.log('✅ Production global styles created');
  }

  // Process all components
  processComponents() {
    console.log('🔧 Enhancing components for production...');
    
    this.walkDirectory(COMPONENTS_DIR, (filePath) => {
      if (!/\.(tsx?|jsx?)$/.test(filePath)) return;
      
      this.processedComponents++;
      let enhanced = false;

      if (this.enhanceAccessibility(filePath)) enhanced = true;
      if (this.enhanceResponsiveDesign(filePath)) enhanced = true;
      if (this.addErrorBoundaries(filePath)) enhanced = true;
      if (this.addLoadingStates(filePath)) enhanced = true;
      
      this.validateThemeConsistency(filePath);

      if (enhanced) {
        this.enhancedComponents++;
      }
    });
  }

  // Walk directory recursively
  walkDirectory(dirPath, callback) {
    if (!fs.existsSync(dirPath)) return;
    
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        this.walkDirectory(fullPath, callback);
      } else if (entry.isFile()) {
        callback(fullPath);
      }
    }
  }

  // Run accessibility tests
  runAccessibilityTests() {
    console.log('♿ Running accessibility tests...');
    
    try {
      // Run axe-core accessibility tests
      execSync('npm run test:accessibility', { 
        cwd: path.join(__dirname, '..'),
        stdio: 'inherit' 
      });
      console.log('✅ Accessibility tests passed');
    } catch (error) {
      console.warn('⚠️ Some accessibility tests failed - check the output above');
    }
  }

  // Generate UX enhancement report
  generateReport() {
    console.log('\n📊 Production UX Enhancement Report');
    console.log('=====================================');
    console.log(`Components processed: ${this.processedComponents}`);
    console.log(`Components enhanced: ${this.enhancedComponents}`);
    console.log(`Enhancement rate: ${((this.enhancedComponents / this.processedComponents) * 100).toFixed(1)}%`);
    
    if (this.themeIssues.length > 0) {
      console.log(`\n🎨 Theme consistency issues found: ${this.themeIssues.length}`);
      this.themeIssues.slice(0, 5).forEach(({ file, issues }) => {
        console.log(`  - ${file}: ${issues.join(', ')}`);
      });
      if (this.themeIssues.length > 5) {
        console.log(`  ... and ${this.themeIssues.length - 5} more`);
      }
    }
    
    if (this.errors.length > 0) {
      console.log('\n❌ Errors encountered:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log('\n✅ Production UX enhancement completed!');
    console.log('🎯 Next steps:');
    console.log('  - Run accessibility tests: npm run test:accessibility');
    console.log('  - Test responsive design on different screen sizes');
    console.log('  - Validate theme consistency in dark/light modes');
    console.log('  - Test error boundaries with simulated errors');
  }

  // Run all enhancements
  run() {
    console.log('🚀 Starting production UX enhancement...\n');
    
    this.createProductionStyles();
    this.processComponents();
    this.runAccessibilityTests();
    this.generateReport();
  }
}

// Run the enhancer
if (require.main === module) {
  const enhancer = new ProductionUXEnhancer();
  enhancer.run();
}

module.exports = ProductionUXEnhancer;