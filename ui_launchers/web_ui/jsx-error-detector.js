#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * JSX Error Detection Script
 * Scans .tsx files for common JSX syntax errors including:
 * - Missing closing braces
 * - JSX capitalization issues
 * - Unexpected EOF errors
 * - JSX tag mismatches
 */

class JSXErrorDetector {
  constructor() {
    this.errors = [];
    this.fixSuggestions = new Map();
    this.options = {};
  }

  /**
   * Main entry point to scan all .tsx files
   */
  async scanAllFiles() {
    console.log('🔍 Starting JSX error detection...\n');
    
    const tsxFiles = this.findTsxFiles(path.join(process.cwd(), 'src'));

    console.log(`Found ${tsxFiles.length} .tsx files to scan\n`);

    for (const file of tsxFiles) {
      await this.scanFile(file);
    }

    this.generateReport();
  }

  /**
   * Scan specific files
   */
  async scanSpecificFiles(filePaths) {
    console.log('🔍 Starting JSX error detection for specific files...\n');
    
    const tsxFiles = [];
    for (const filePath of filePaths) {
      if (fs.existsSync(filePath) && filePath.endsWith('.tsx')) {
        tsxFiles.push(path.resolve(filePath));
      } else {
        console.log(`Warning: File ${filePath} not found or not a .tsx file`);
      }
    }

    console.log(`Found ${tsxFiles.length} .tsx files to scan\n`);

    for (const file of tsxFiles) {
      await this.scanFile(file);
    }

    this.generateReport();
  }

  /**
   * Recursively find all .tsx files in a directory
   */
  findTsxFiles(dir) {
    const files = [];
    
    if (!fs.existsSync(dir)) {
      console.log(`Directory ${dir} does not exist, skipping...`);
      return files;
    }
    
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        // Skip node_modules and other common directories to ignore
        if (!['node_modules', '.next', '.git', 'dist', 'build'].includes(entry.name)) {
          files.push(...this.findTsxFiles(fullPath));
        }
      } else if (entry.isFile() && entry.name.endsWith('.tsx')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  /**
   * Scan a single file for JSX errors
   */
  async scanFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const relativePath = path.relative(process.cwd(), filePath);
      
      console.log(`Scanning: ${relativePath}`);

      // Run all error detection algorithms
      this.detectMissingClosingBraces(content, relativePath);
      this.detectCapitalizationErrors(content, relativePath);
      this.detectEOFErrors(content, relativePath);
      this.detectTagMismatches(content, relativePath);
      this.detectGeneralSyntaxErrors(content, relativePath);

    } catch (error) {
      this.addError(filePath, 0, 0, 'file-read', `Failed to read file: ${error.message}`, 'Check file permissions and encoding');
    }
  }

  /**
   * Detect missing closing braces in JSX expressions
   */
  detectMissingClosingBraces(content, filePath) {
    const lines = content.split('\n');
    const braceStack = [];
    let inJSXContext = false;
    
    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
      const line = lines[lineNum];
      let inString = false;
      let stringChar = '';
      let inComment = false;
      
      // Skip obvious non-JSX lines
      if (line.trim().startsWith('//') || 
          line.trim().startsWith('/*') || 
          line.trim().startsWith('*') ||
          line.trim().startsWith('import ') ||
          line.trim().startsWith('export ')) {
        continue;
      }
      
      for (let col = 0; col < line.length; col++) {
        const char = line[col];
        const prevChar = col > 0 ? line[col - 1] : '';
        const nextChar = col + 1 < line.length ? line[col + 1] : '';
        
        // Handle comments
        if (char === '/' && nextChar === '/') {
          break; // Rest of line is comment
        }
        if (char === '/' && nextChar === '*') {
          inComment = true;
          continue;
        }
        if (char === '*' && nextChar === '/' && inComment) {
          inComment = false;
          col++; // Skip the '/'
          continue;
        }
        if (inComment) continue;
        
        // Track string boundaries
        if ((char === '"' || char === "'" || char === '`') && prevChar !== '\\') {
          if (!inString) {
            inString = true;
            stringChar = char;
          } else if (char === stringChar) {
            inString = false;
            stringChar = '';
          }
        }
        
        if (inString) continue;
        
        // Detect JSX context more accurately
        if (char === '<' && /[A-Za-z]/.test(nextChar)) {
          // Check if this is likely JSX (not a comparison)
          const beforeContext = line.substring(Math.max(0, col - 10), col);
          if (!beforeContext.match(/\b(if|while|for)\s*\($/) && 
              !this.isTypeScriptGeneric(line, col) &&
              !this.isComparison(line, col)) {
            inJSXContext = true;
          }
        }
        
        // Track braces only in JSX context
        if (inJSXContext && char === '{') {
          braceStack.push({
            line: lineNum + 1,
            column: col + 1,
            type: '{'
          });
        } else if (inJSXContext && char === '}') {
          if (braceStack.length === 0) {
            this.addError(filePath, lineNum + 1, col + 1, 'extra-closing-brace', 
              'Unexpected closing brace in JSX', 'Remove extra closing brace or add matching opening brace');
          } else {
            braceStack.pop();
          }
        }
        
        // End JSX context
        if (char === '>' && inJSXContext) {
          // Check if we're ending a tag or still in JSX content
          if (prevChar === '/') {
            inJSXContext = false; // Self-closing tag
          }
          // For regular tags, we stay in JSX context until we see the closing tag
        }
      }
    }
    
    // Report unmatched opening braces (but only if we're confident they're JSX-related)
    for (const brace of braceStack) {
      this.addError(filePath, brace.line, brace.column, 'missing-closing-brace',
        'Missing closing brace for JSX expression', 'Add closing brace "}" at the end of the JSX expression');
    }
  }

  /**
   * Detect JSX capitalization errors
   */
  detectCapitalizationErrors(content, filePath) {
    const lines = content.split('\n');
    
    // Common HTML elements that should be lowercase
    const htmlElements = [
      'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'button', 'input', 'form', 'label', 'select', 'option',
      'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
      'img', 'a', 'nav', 'header', 'footer', 'main', 'section', 'article',
      'aside', 'figure', 'figcaption', 'video', 'audio', 'canvas'
    ];
    
    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
      const line = lines[lineNum];
      
      // Find JSX elements with incorrect capitalization
      const jsxElementRegex = /<([A-Z][a-z]+)(?:\s|>|\/)/g;
      let match;
      
      while ((match = jsxElementRegex.exec(line)) !== null) {
        const elementName = match[1];
        const lowerElementName = elementName.toLowerCase();
        
        if (htmlElements.includes(lowerElementName)) {
          this.addError(filePath, lineNum + 1, match.index + 1, 'capitalization',
            `HTML element "${elementName}" should be lowercase`,
            `Change "<${elementName}" to "<${lowerElementName}"`);
        }
      }
      
      // Also check for closing tags
      const closingTagRegex = /<\/([A-Z][a-z]+)>/g;
      while ((match = closingTagRegex.exec(line)) !== null) {
        const elementName = match[1];
        const lowerElementName = elementName.toLowerCase();
        
        if (htmlElements.includes(lowerElementName)) {
          this.addError(filePath, lineNum + 1, match.index + 1, 'capitalization',
            `HTML closing tag "${elementName}" should be lowercase`,
            `Change "</${elementName}>" to "</${lowerElementName}>"`);
        }
      }
    }
  }

  /**
   * Detect unexpected EOF errors
   */
  detectEOFErrors(content, filePath) {
    const trimmedContent = content.trim();
    
    // Check if file ends abruptly without proper component closure
    const lines = content.split('\n');
    const lastNonEmptyLine = lines.slice().reverse().find(line => line.trim() !== '');
    
    if (!lastNonEmptyLine) {
      this.addError(filePath, lines.length, 0, 'eof',
        'File is empty or contains only whitespace',
        'Add proper React component structure');
      return;
    }
    
    // Check for incomplete JSX structures
    const openBraces = (content.match(/\{/g) || []).length;
    const closeBraces = (content.match(/\}/g) || []).length;
    
    if (openBraces > closeBraces) {
      this.addError(filePath, lines.length, 0, 'eof',
        `File ends with ${openBraces - closeBraces} unmatched opening brace(s)`,
        'Add missing closing brace(s) before end of file');
    }
    
    // Check for incomplete component export
    if (!content.includes('export') && content.includes('function') || content.includes('const')) {
      this.addError(filePath, lines.length, 0, 'eof',
        'Component appears to be missing export statement',
        'Add "export default" or "export" before component declaration');
    }
    
    // Check for incomplete JSX return statement
    if (content.includes('return (') && !content.includes(');')) {
      this.addError(filePath, lines.length, 0, 'eof',
        'JSX return statement appears incomplete',
        'Add closing parenthesis and semicolon to return statement');
    }
  }

  /**
   * Detect JSX tag mismatches
   */
  detectTagMismatches(content, filePath) {
    const lines = content.split('\n');
    const tagStack = [];
    
    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
      const line = lines[lineNum];
      
      // Skip lines that are clearly not JSX (comments, imports, etc.)
      if (line.trim().startsWith('//') || 
          line.trim().startsWith('/*') || 
          line.trim().startsWith('*') ||
          line.trim().startsWith('import ') ||
          line.trim().startsWith('export ') ||
          !line.includes('<')) {
        continue;
      }
      
      // Find opening JSX tags (not TypeScript generics)
      // Look for tags that start with < followed by a capital letter or lowercase letter
      // but exclude TypeScript generic syntax
      const openingTagRegex = /<([A-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*|[a-z][a-zA-Z0-9-]*)\s*(?:[^>]*?)(?<!\/)\s*>/g;
      let match;
      
      while ((match = openingTagRegex.exec(line)) !== null) {
        const tagName = match[1];
        const fullMatch = match[0];
        
        // Skip if this looks like a TypeScript generic or comparison
        if (this.isTypeScriptGeneric(line, match.index) || this.isComparison(line, match.index)) {
          continue;
        }
        
        tagStack.push({
          name: tagName,
          line: lineNum + 1,
          column: match.index + 1
        });
      }
      
      // Find self-closing tags and remove them from consideration
      const selfClosingRegex = /<([A-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*|[a-z][a-zA-Z0-9-]*)\s*[^>]*\/>/g;
      while ((match = selfClosingRegex.exec(line)) !== null) {
        const tagName = match[1];
        
        // Skip if this looks like a TypeScript generic
        if (this.isTypeScriptGeneric(line, match.index)) {
          continue;
        }
        
        // Remove the last matching opening tag if it exists
        for (let i = tagStack.length - 1; i >= 0; i--) {
          if (tagStack[i].name === tagName) {
            tagStack.splice(i, 1);
            break;
          }
        }
      }
      
      // Find closing tags
      const closingTagRegex = /<\/([A-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*|[a-z][a-zA-Z0-9-]*)\s*>/g;
      while ((match = closingTagRegex.exec(line)) !== null) {
        const tagName = match[1];
        
        if (tagStack.length === 0) {
          this.addError(filePath, lineNum + 1, match.index + 1, 'tag-mismatch',
            `Closing tag "</${tagName}>" has no matching opening tag`,
            `Add opening tag "<${tagName}>" or remove closing tag`);
        } else {
          const lastTag = tagStack.pop();
          if (lastTag.name !== tagName) {
            this.addError(filePath, lineNum + 1, match.index + 1, 'tag-mismatch',
              `Closing tag "</${tagName}>" does not match opening tag "<${lastTag.name}>" at line ${lastTag.line}`,
              `Change closing tag to "</${lastTag.name}>" or fix opening tag`);
          }
        }
      }
    }
    
    // Report unmatched opening tags (but be conservative)
    for (const tag of tagStack) {
      // Only report if it looks like a real JSX component
      if (tag.name.match(/^[A-Z]/) || tag.name.match(/^[a-z][a-z0-9-]*$/)) {
        this.addError(filePath, tag.line, tag.column, 'tag-mismatch',
          `Opening tag "<${tag.name}>" has no matching closing tag`,
          `Add closing tag "</${tag.name}>" or make it self-closing`);
      }
    }
  }

  /**
   * Check if a < character is part of a TypeScript generic
   */
  isTypeScriptGeneric(line, index) {
    // Look for patterns like: function<T>, Array<string>, React.FC<Props>
    const beforeChar = index > 0 ? line[index - 1] : '';
    const beforeContext = line.substring(Math.max(0, index - 20), index);
    
    // Check if preceded by function name, type name, or interface name
    return /[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(beforeContext) ||
           beforeContext.includes('function') ||
           beforeContext.includes('interface') ||
           beforeContext.includes('type ') ||
           beforeContext.includes('extends') ||
           beforeContext.includes('implements');
  }

  /**
   * Check if a < character is part of a comparison operator
   */
  isComparison(line, index) {
    const nextChar = index + 1 < line.length ? line[index + 1] : '';
    const prevChar = index > 0 ? line[index - 1] : '';
    
    // Check for <=, <, or other comparison contexts
    return nextChar === '=' || 
           /\d/.test(prevChar) || 
           /\d/.test(nextChar) ||
           line.substring(index - 5, index + 5).includes('length') ||
           line.substring(index - 5, index + 5).includes('size');
  }

  /**
   * Detect general JSX syntax errors
   */
  detectGeneralSyntaxErrors(content, filePath) {
    const lines = content.split('\n');
    
    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
      const line = lines[lineNum];
      
      // Skip lines that are comments or strings
      if (line.trim().startsWith('//') || line.trim().startsWith('/*') || line.trim().startsWith('*')) {
        continue;
      }
      
      // Check for incorrect JSX comments (only in JSX context)
      if (line.includes('<') && (line.includes('<!-- ') || line.includes(' -->'))) {
        this.addError(filePath, lineNum + 1, line.indexOf('<!--') + 1, 'syntax',
          'HTML comments are not valid in JSX',
          'Use JSX comments: {/* comment */}');
      }
      
      // Check for class instead of className (only in JSX context)
      if (line.includes('<') && line.includes('class=') && !line.includes('className=')) {
        // Make sure it's not in a string or comment
        const classMatch = line.match(/\bclass\s*=/);
        if (classMatch) {
          const classIndex = line.indexOf(classMatch[0]);
          this.addError(filePath, lineNum + 1, classIndex + 1, 'syntax',
            'Use "className" instead of "class" in JSX',
            'Change "class=" to "className="');
        }
      }
      
      // Check for for instead of htmlFor (only in JSX context)
      if (line.includes('<') && line.includes(' for=') && !line.includes('htmlFor=')) {
        const forMatch = line.match(/\bfor\s*=/);
        if (forMatch) {
          const forIndex = line.indexOf(forMatch[0]);
          this.addError(filePath, lineNum + 1, forIndex + 1, 'syntax',
            'Use "htmlFor" instead of "for" in JSX',
            'Change "for=" to "htmlFor="');
        }
      }
    }
  }

  /**
   * Add an error to the collection
   */
  addError(file, line, column, type, message, suggestion) {
    // Filter by error type if specified
    if (this.options.errorTypes && this.options.errorTypes.length > 0) {
      if (!this.options.errorTypes.includes(type)) {
        return;
      }
    }
    
    this.errors.push({
      file: path.relative(process.cwd(), file),
      line,
      column,
      type,
      message,
      suggestion,
      severity: 'error'
    });
  }

  /**
   * Generate and display the error report
   */
  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('📋 JSX ERROR DETECTION REPORT');
    console.log('='.repeat(80));
    
    if (this.errors.length === 0) {
      console.log('✅ No JSX syntax errors found!');
      return;
    }
    
    console.log(`\n❌ Found ${this.errors.length} JSX syntax errors:\n`);
    
    if (!this.options.summaryOnly) {
      // Group errors by file
      const errorsByFile = this.errors.reduce((acc, error) => {
        if (!acc[error.file]) {
          acc[error.file] = [];
        }
        acc[error.file].push(error);
        return acc;
      }, {});
      
      // Display errors grouped by file
      for (const [file, fileErrors] of Object.entries(errorsByFile)) {
        console.log(`📄 ${file} (${fileErrors.length} errors)`);
        console.log('-'.repeat(file.length + 20));
        
        fileErrors.forEach((error, index) => {
          console.log(`  ${index + 1}. Line ${error.line}, Column ${error.column}`);
          console.log(`     Type: ${error.type}`);
          console.log(`     Error: ${error.message}`);
          console.log(`     Fix: ${error.suggestion}`);
          console.log('');
        });
      }
    }
    
    // Summary by error type
    const errorsByType = this.errors.reduce((acc, error) => {
      acc[error.type] = (acc[error.type] || 0) + 1;
      return acc;
    }, {});
    
    console.log('📊 Error Summary by Type:');
    console.log('-'.repeat(30));
    for (const [type, count] of Object.entries(errorsByType)) {
      console.log(`  ${type}: ${count} errors`);
    }
    
    // Calculate unique files
    const uniqueFiles = new Set(this.errors.map(e => e.file)).size;
    
    console.log('\n' + '='.repeat(80));
    console.log(`Total: ${this.errors.length} errors found across ${uniqueFiles} files`);
    console.log('='.repeat(80));
    
    // Generate JSON report for programmatic use
    this.generateJSONReport();
  }

  /**
   * Generate JSON report for programmatic use
   */
  generateJSONReport() {
    const report = {
      timestamp: new Date().toISOString(),
      totalErrors: this.errors.length,
      totalFiles: new Set(this.errors.map(e => e.file)).size,
      errors: this.errors,
      summary: this.errors.reduce((acc, error) => {
        acc[error.type] = (acc[error.type] || 0) + 1;
        return acc;
      }, {})
    };
    
    const reportPath = path.join(process.cwd(), 'jsx-error-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 Detailed JSON report saved to: ${reportPath}`);
  }
}

// Run the detector if this script is executed directly
if (require.main === module) {
  const args = process.argv.slice(2);
  const detector = new JSXErrorDetector();
  
  // Parse command line arguments
  const options = {
    files: [],
    errorTypes: [],
    summaryOnly: false,
    help: false
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--summary' || arg === '-s') {
      options.summaryOnly = true;
    } else if (arg === '--type' || arg === '-t') {
      if (i + 1 < args.length) {
        options.errorTypes.push(args[++i]);
      }
    } else if (arg === '--file' || arg === '-f') {
      if (i + 1 < args.length) {
        options.files.push(args[++i]);
      }
    } else if (!arg.startsWith('-')) {
      options.files.push(arg);
    }
  }
  
  if (options.help) {
    console.log(`
JSX Error Detection Script

Usage: node jsx-error-detector.js [options] [files...]

Options:
  -h, --help              Show this help message
  -s, --summary           Show only summary, not detailed errors
  -t, --type <type>       Filter by error type (missing-closing-brace, capitalization, eof, tag-mismatch, syntax)
  -f, --file <pattern>    Scan specific file pattern

Examples:
  node jsx-error-detector.js                           # Scan all .tsx files
  node jsx-error-detector.js --summary                 # Show only summary
  node jsx-error-detector.js --type missing-closing-brace  # Show only brace errors
  node jsx-error-detector.js src/components/MyComponent.tsx  # Scan specific file
`);
    process.exit(0);
  }
  
  // Apply options to detector
  detector.options = options;
  
  if (options.files.length > 0) {
    // Scan specific files
    detector.scanSpecificFiles(options.files).catch(console.error);
  } else {
    // Scan all files
    detector.scanAllFiles().catch(console.error);
  }
}

module.exports = JSXErrorDetector;