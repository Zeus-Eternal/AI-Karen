# JSX Error Detection Script

This script automatically scans TypeScript React (.tsx) files for common JSX syntax errors.

## Features

- **Missing Closing Braces**: Detects unmatched opening braces `{` in JSX expressions
- **JSX Capitalization**: Identifies HTML elements incorrectly capitalized as React components
- **EOF Errors**: Finds incomplete component structures at end of file
- **Tag Mismatches**: Detects opening tags without matching closing tags
- **General Syntax**: Catches common JSX syntax issues like HTML comments, class vs className

## Usage

### Basic Usage

```bash
# Scan all .tsx files in the project
node jsx-error-detector.js

# Show only summary (no detailed errors)
node jsx-error-detector.js --summary
```

### Filter by Error Type

```bash
# Show only missing closing brace errors
node jsx-error-detector.js --type missing-closing-brace

# Show only capitalization errors
node jsx-error-detector.js --type capitalization

# Show only EOF errors
node jsx-error-detector.js --type eof
```

### Scan Specific Files

```bash
# Scan a specific file
node jsx-error-detector.js src/components/MyComponent.tsx

# Scan multiple files
node jsx-error-detector.js src/components/A.tsx src/components/B.tsx
```

### Combined Options

```bash
# Show only missing brace errors in summary format
node jsx-error-detector.js --summary --type missing-closing-brace

# Scan specific file for specific error type
node jsx-error-detector.js --type tag-mismatch src/components/MyComponent.tsx
```

## Command Line Options

- `-h, --help`: Show help message
- `-s, --summary`: Show only summary, not detailed errors
- `-t, --type <type>`: Filter by error type
- `-f, --file <pattern>`: Scan specific file pattern

## Error Types

1. **missing-closing-brace**: Missing `}` for JSX expressions
2. **capitalization**: HTML elements incorrectly capitalized (e.g., `<Div>` should be `<div>`)
3. **eof**: Unexpected end of file or incomplete structures
4. **tag-mismatch**: Opening tags without matching closing tags
5. **syntax**: General JSX syntax errors (HTML comments, class vs className, etc.)
6. **extra-closing-brace**: Unexpected closing braces

## Output

The script generates:

1. **Console Output**: Detailed error report with file locations and fix suggestions
2. **JSON Report**: Machine-readable report saved as `jsx-error-report.json`

### Example Output

```
📄 src/components/settings/PersonalFactsSettings.tsx (1 errors)
---------------------------------------------------------------------
  1. Line 245, Column 9
     Type: missing-closing-brace
     Error: Missing closing brace for JSX expression
     Fix: Add closing brace "}" at the end of the JSX expression

📊 Error Summary by Type:
------------------------------
  missing-closing-brace: 1885 errors
  capitalization: 2228 errors
  eof: 1032 errors
  tag-mismatch: 4368 errors
  syntax: 8 errors

Total: 9521 errors found across 304 files
```

## Integration

This script can be integrated into:

- **Build Process**: Run before compilation to catch JSX errors early
- **CI/CD Pipeline**: Fail builds if JSX syntax errors are found
- **Pre-commit Hooks**: Validate JSX syntax before commits
- **IDE Integration**: Run as a custom task in your development environment

## Troubleshooting

### False Positives

The script uses heuristics to detect JSX context and may occasionally report false positives, especially:

- In TypeScript generic syntax (`Array<T>`)
- In comparison operators (`a < b`)
- In complex nested structures

### Performance

For large codebases, use filtering options to focus on specific error types or files:

```bash
# Focus on critical errors first
node jsx-error-detector.js --type missing-closing-brace --summary
```

## Examples

### Find all missing braces in settings components
```bash
node jsx-error-detector.js --type missing-closing-brace src/components/settings/*.tsx
```

### Quick health check (summary only)
```bash
node jsx-error-detector.js --summary
```

### Focus on specific error types for fixing
```bash
node jsx-error-detector.js --type eof --type capitalization
```