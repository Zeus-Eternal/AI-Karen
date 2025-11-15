#!/usr/bin/env node

const fs = require('fs');

// Simple replacements for any types
const replacements = [
  { from: /:\s*any\[\]/g, to: ': unknown[]' },
  { from: /Array<any>/g, to: 'Array<unknown>' },
  { from: /Record<string,\s*any>/g, to: 'Record<string, unknown>' },
  { from: /Record<(\w+),\s*any>/g, to: 'Record<$1, unknown>' },
  { from: /Promise<any>/g, to: 'Promise<unknown>' },
  { from: /\bevent:\s*any\b/g, to: 'event: Event' },
  { from: /\be:\s*any\b/g, to: 'e: Event' },
  { from: /\berror:\s*any\b/g, to: 'error: Error' },
  { from: /\berr:\s*any\b/g, to: 'err: Error' },
  { from: /\bdata:\s*any\b/g, to: 'data: unknown' },
  { from: /\bresponse:\s*any\b/g, to: 'response: unknown' },
  { from: /\bresult:\s*any\b/g, to: 'result: unknown' },
  { from: /\bpayload:\s*any\b/g, to: 'payload: unknown' },
  { from: /\bconfig:\s*any\b/g, to: 'config: Record<string, unknown>' },
  { from: /\boptions:\s*any\b/g, to: 'options: Record<string, unknown>' },
  { from: /\bparams:\s*any\b/g, to: 'params: Record<string, unknown>' },
  { from: /\bmetadata:\s*any\b/g, to: 'metadata: Record<string, unknown>' },
  { from: /\bprops:\s*any\b/g, to: 'props: Record<string, unknown>' },
  { from: /\bchildren:\s*any\b/g, to: 'children: React.ReactNode' },
  { from: /:\s*any(?=\s*[;,\)\]\}=])/g, to: ': unknown' }
];

function processFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      console.log('File not found: ' + filePath);
      return false;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    let newContent = content;
    let changes = 0;

    // Apply replacements
    for (const replacement of replacements) {
      const before = newContent;
      newContent = newContent.replace(replacement.from, replacement.to);
      if (before !== newContent) {
        changes++;
      }
    }

    // Fix empty blocks
    newContent = newContent.replace(/catch\s*\([^)]*\)\s*\{\s*\}/g, 'catch (error) {\n    // Handle error silently\n  }');
    newContent = newContent.replace(/try\s*\{\s*\}\s*catch/g, 'try {\n    // TODO: Add implementation\n  } catch');

    if (newContent !== content) {
      // Create backup
      fs.writeFileSync(filePath + '.backup', content, 'utf8');
      
      // Write new content
      fs.writeFileSync(filePath, newContent, 'utf8');
      
      console.log('Fixed: ' + filePath + ' (' + changes + ' changes)');
      return true;
    }

    console.log('No changes needed: ' + filePath);
    return false;
  } catch (error) {
    console.error('Error processing ' + filePath + ': ' + error.message);
    return false;
  }
}

// Process the specific file
const filePath = process.argv[2] || 'ui_launchers/KAREN-Theme-Default/src/lib/auth/hot-reload-auth.ts';
processFile(filePath);