#!/usr/bin/env node

/**
 * Fix Syntax Errors Script
 * 
 * Fixes syntax errors introduced by the UX enhancement script
 */

const fs = require('fs');
const path = require('path');

const SRC_DIR = path.join(__dirname, '../src');

class SyntaxErrorFixer {
  constructor() {
    this.fixedFiles = 0;
    this.errors = [];
  }

  fixFile(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Fix malformed self-closing tags with aria attributes
      content = content.replace(/\s*\/\s*aria-label="[^"]*">/g, ' />');
      
      // Fix other malformed self-closing tags
      content = content.replace(/\s*\/\s*aria-[^=]*="[^"]*">/g, ' />');
      
      // Fix broken JSX tags
      content = content.replace(/<([a-zA-Z][a-zA-Z0-9]*)[^>]*\s*\/\s*aria-[^>]*>/g, (match, tagName) => {
        // Extract the tag content without the malformed aria attribute
        const cleanMatch = match.replace(/\s*\/\s*aria-[^>]*>/, ' />');
        return cleanMatch;
      });

      // Fix specific patterns
      content = content.replace(/\s*\/\s*aria-label="[^"]*">/g, ' />');
      content = content.replace(/\s*\/\s*aria-describedby="[^"]*">/g, ' />');
      content = content.replace(/\s*\/\s*aria-expanded="[^"]*">/g, ' />');
      content = content.replace(/\s*\/\s*aria-hidden="[^"]*">/g, ' />');

      // Fix button elements specifically
      content = content.replace(/<Button([^>]*)\s*\/\s*aria-label="[^"]*">/g, '<Button$1 />');
      content = content.replace(/<input([^>]*)\s*\/\s*aria-label="[^"]*">/g, '<input$1 />');
      content = content.replace(/<select([^>]*)\s*\/\s*aria-label="[^"]*">/g, '<select$1 />');
      content = content.replace(/<textarea([^>]*)\s*\/\s*aria-label="[^"]*">/g, '<textarea$1 />');

      // Fix component references
      content = content.replace(/([a-zA-Z][a-zA-Z0-9]*)\s*\/\s*aria-label="[^"]*">/g, '$1 />');

      if (content !== originalContent) {
        fs.writeFileSync(filePath, content);
        hasChanges = true;
      }

      return hasChanges;
    } catch (error) {
      this.errors.push(`Error fixing ${filePath}: ${error.message}`);
      return false;
    }
  }

  walkDirectory(dirPath, callback) {
    if (!fs.existsSync(dirPath)) return;
    
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        this.walkDirectory(fullPath, callback);
      } else if (entry.isFile() && /\.(tsx?|jsx?)$/.test(entry.name)) {
        callback(fullPath);
      }
    }
  }

  run() {
    console.log('🔧 Fixing syntax errors...');
    
    this.walkDirectory(SRC_DIR, (filePath) => {
      if (this.fixFile(filePath)) {
        this.fixedFiles++;
        console.log(`✅ Fixed: ${path.relative(SRC_DIR, filePath)}`);
      }
    });

    console.log(`\n📊 Fixed ${this.fixedFiles} files`);
    
    if (this.errors.length > 0) {
      console.log('\n❌ Errors:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log('✅ Syntax error fixing completed!');
  }
}

// Run the fixer
if (require.main === module) {
  const fixer = new SyntaxErrorFixer();
  fixer.run();
}

module.exports = SyntaxErrorFixer;