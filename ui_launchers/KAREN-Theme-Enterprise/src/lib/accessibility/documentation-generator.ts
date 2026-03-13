/**
 * Accessibility Documentation Generator
 * 
 * Automatically generates accessibility documentation, component guidelines,
 * and usage examples based on component analysis and best practices.
 */

import { readdir, readFile, writeFile, mkdir } from 'fs/promises';
import { join, extname, basename } from 'path';
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import * as t from '@babel/types';

interface ComponentAnalysis {
  ariaAttributes: Set<string>;
  eventHandlers: Set<string>;
  htmlElements: Set<string>;
  imports: Set<string>;
  hooks: Set<string>;
  props: Set<string>;
}
// Types for documentation generation
export interface ComponentAccessibilityInfo {
  name: string;
  filePath: string;
  description: string;
  accessibilityFeatures: AccessibilityFeature[];
  ariaAttributes: AriaAttribute[];
  keyboardSupport: KeyboardSupport[];
  screenReaderSupport: ScreenReaderFeature[];
  examples: AccessibilityExample[];
  guidelines: string[];
  commonIssues: AccessibilityIssue[];
  testingInstructions: TestingInstruction[];
}
export interface AccessibilityFeature {
  feature: string;
  description: string;
  implementation: string;
  wcagCriteria: string[];
}
export interface AriaAttribute {
  attribute: string;
  purpose: string;
  usage: string;
  required: boolean;
  example: string;
}
export interface KeyboardSupport {
  key: string;
  action: string;
  context: string;
  required: boolean;
}
export interface ScreenReaderFeature {
  feature: string;
  announcement: string;
  context: string;
  implementation: string;
}
export interface AccessibilityExample {
  title: string;
  description: string;
  code: string;
  doExample: boolean; // true for "do", false for "don't"
  explanation: string;
}
export interface AccessibilityIssue {
  issue: string;
  description: string;
  solution: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}
export interface TestingInstruction {
  method: 'keyboard' | 'screen-reader' | 'automated' | 'manual';
  instruction: string;
  expectedResult: string;
  tools?: string[];
}
export interface DocumentationConfig {
  sourceDir: string;
  outputDir: string;
  componentPatterns: string[];
  excludePatterns: string[];
  includeTests: boolean;
  includeStories: boolean;
  generateExamples: boolean;
  wcagLevel: 'A' | 'AA' | 'AAA';
}
/**
 * Accessibility Documentation Generator Class
 */
export class AccessibilityDocumentationGenerator {
  private config: DocumentationConfig;
  private componentRegistry: Map<string, ComponentAccessibilityInfo> = new Map();
  constructor(config: Partial<DocumentationConfig> = {}) {
    this.config = {
      sourceDir: 'src/components',
      outputDir: 'docs/accessibility',
      componentPatterns: ['**/*.tsx', '**/*.jsx'],
      excludePatterns: ['**/*.test.*', '**/*.spec.*', '**/node_modules/**'],
      includeTests: true,
      includeStories: true,
      generateExamples: true,
      wcagLevel: 'AA',
      ...config
    };
  }

  private logDevelopmentWarning(message: string, error: unknown): void {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(message, error);
    }
  }
  /**
   * Generate complete accessibility documentation
   */
  async generateDocumentation(): Promise<void> {
    // Analyze components
    await this.analyzeComponents();
    // Generate documentation files
    await this.generateComponentDocs();
    await this.generateOverviewDoc();
    await this.generateGuidelinesDoc();
    await this.generateTestingDoc();
    await this.generateChecklistDoc();
  }
  /**
   * Analyze components for accessibility features
   */
  private async analyzeComponents(): Promise<void> {
    const componentFiles = await this.findComponentFiles();
    for (const filePath of componentFiles) {
      try {
        const componentInfo = await this.analyzeComponent(filePath);
        if (componentInfo) {
          this.componentRegistry.set(componentInfo.name, componentInfo);
        }
      } catch (error: unknown) {
        this.logDevelopmentWarning(
          `Failed to analyze accessibility component at ${filePath}`,
          error
        );
      }
    }
  }
  /**
   * Find component files to analyze
   */
  private async findComponentFiles(): Promise<string[]> {
    const files: string[] = [];
    const scanDirectory = async (dir: string): Promise<void> => {
      try {
        const entries = await readdir(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = join(dir, entry.name);
          if (entry.isDirectory()) {
            await scanDirectory(fullPath);
          } else if (entry.isFile()) {
            const ext = extname(entry.name);
            if (['.tsx', '.jsx'].includes(ext) && !this.shouldExclude(fullPath)) {
              files.push(fullPath);
            }
          }
        }
        } catch (error: unknown) {
          this.logDevelopmentWarning(
            `Skipping inaccessible directory during accessibility scan: ${dir}`,
            error
          );
        }
      };
    await scanDirectory(this.config.sourceDir);
    return files;
  }
  /**
   * Check if file should be excluded
   */
  private shouldExclude(filePath: string): boolean {
    return this.config.excludePatterns.some(pattern => {
      // Simple pattern matching - in a real implementation, use a proper glob library
      return filePath.includes(pattern.replace('**/', '').replace('*', ''));
    });
  }
  /**
   * Analyze a single component file
   */
  private async analyzeComponent(filePath: string): Promise<ComponentAccessibilityInfo | null> {
    const content = await readFile(filePath, 'utf-8');
    const componentName = this.extractComponentName(filePath);
    if (!componentName) return null;
    try {
      const ast = parse(content, {
        sourceType: 'module',
        plugins: ['typescript', 'jsx']
      }) as t.File;
      const analysis = this.analyzeAST(ast);
      return {
        name: componentName,
        filePath,
        description: this.extractDescription(content),
        accessibilityFeatures: this.identifyAccessibilityFeatures(analysis),
        ariaAttributes: this.extractAriaAttributes(analysis),
        keyboardSupport: this.identifyKeyboardSupport(analysis),
        screenReaderSupport: this.identifyScreenReaderSupport(analysis),
        examples: this.generateExamples(componentName, analysis),
        guidelines: this.generateGuidelines(componentName, analysis),
        commonIssues: this.identifyCommonIssues(componentName, analysis),
        testingInstructions: this.generateTestingInstructions(componentName, analysis)
      };
    } catch (error: unknown) {
      this.logDevelopmentWarning(
        `Failed to process accessibility metadata for ${filePath}`,
        error
      );
      return null;
    }
  }
  /**
   * Extract component name from file path
   */
  private extractComponentName(filePath: string): string | null {
    const fileName = basename(filePath, extname(filePath));
    // Skip index files, test files, etc.
    if (['index', 'types', 'utils'].includes(fileName.toLowerCase())) {
      return null;
    }
    return fileName;
  }
  /**
   * Extract component description from comments
   */
  private extractDescription(content: string): string {
    const lines = content.split('\n');
    const commentLines: string[] = [];
    let inComment = false;
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('/**')) {
        inComment = true;
        continue;
      }
      if (trimmed.endsWith('*/')) {
        inComment = false;
        break;
      }
      if (inComment && trimmed.startsWith('*')) {
        const commentText = trimmed.substring(1).trim();
        if (commentText && !commentText.startsWith('@')) {
          commentLines.push(commentText);
        }
      }
    }
    return commentLines.join(' ').trim() || 'No description available.';
  }
  /**
   * Analyze AST for accessibility patterns
   */
  private analyzeAST(ast: t.File): ComponentAnalysis {
    const analysis: ComponentAnalysis = {
      ariaAttributes: new Set<string>(),
      eventHandlers: new Set<string>(),
      htmlElements: new Set<string>(),
      imports: new Set<string>(),
      hooks: new Set<string>(),
      props: new Set<string>()
    };
    traverse(ast, {
      JSXAttribute(path) {
        const name = path.node.name;
        if (t.isJSXIdentifier(name)) {
          if (name.name.startsWith('aria-') || name.name.startsWith('role')) {
            analysis.ariaAttributes.add(name.name);
          }
          if (name.name.startsWith('on')) {
            analysis.eventHandlers.add(name.name);
          }
        }
      },
      JSXElement(path) {
        const openingElement = path.node.openingElement;
        if (t.isJSXIdentifier(openingElement.name)) {
          analysis.htmlElements.add(openingElement.name.name);
        }
      },
      ImportDeclaration(path) {
        if (t.isStringLiteral(path.node.source)) {
          analysis.imports.add(path.node.source.value);
        }
      },
      CallExpression(path) {
        if (t.isIdentifier(path.node.callee) && path.node.callee.name.startsWith('use')) {
          analysis.hooks.add(path.node.callee.name);
        }
      }
    });

    return analysis;
  }
  /**
   * Identify accessibility features
   */
  private identifyAccessibilityFeatures(analysis: ComponentAnalysis): AccessibilityFeature[] {
    const features: AccessibilityFeature[] = [];
    // Check for semantic HTML
    const semanticElements = ['button', 'nav', 'main', 'header', 'footer', 'section', 'article'];
    for (const element of semanticElements) {
      if (analysis.htmlElements.has(element)) {
        features.push({
          feature: 'Semantic HTML',
          description: `Uses semantic ${element} element`,
          implementation: `<${element}>...</${element}>`,
          wcagCriteria: ['1.3.1', '4.1.2']
        });
      }
    }
    // Check for ARIA attributes
    if (analysis.ariaAttributes.size > 0) {
      features.push({
        feature: 'ARIA Support',
        description: 'Implements ARIA attributes for enhanced accessibility',
        implementation: Array.from(analysis.ariaAttributes).join(', '),
        wcagCriteria: ['1.3.1', '4.1.2']
      });
    }
    // Check for keyboard support
    const keyboardEvents = ['onKeyDown', 'onKeyUp', 'onKeyPress'];
    if (keyboardEvents.some(event => analysis.eventHandlers.has(event))) {
      features.push({
        feature: 'Keyboard Support',
        description: 'Supports keyboard interaction',
        implementation: 'Keyboard event handlers implemented',
        wcagCriteria: ['2.1.1', '2.1.2']
      });
    }
    return features;
  }
  /**
   * Extract ARIA attributes with documentation
   */
  private extractAriaAttributes(analysis: ComponentAnalysis): AriaAttribute[] {
    const ariaAttributes: AriaAttribute[] = [];
    const ariaDocumentation: Record<string, { purpose: string; usage: string; required: boolean }> = {
      'aria-label': {
        purpose: 'Provides an accessible name for the element',
        usage: 'Use when the visible text is not descriptive enough',
        required: false
      },
      'aria-labelledby': {
        purpose: 'References other elements that describe this element',
        usage: 'Use to associate labels or headings with form controls',
        required: false
      },
      'aria-describedby': {
        purpose: 'References elements that provide additional description',
        usage: 'Use to associate help text or error messages',
        required: false
      },
      'aria-expanded': {
        purpose: 'Indicates if a collapsible element is expanded',
        usage: 'Required for collapsible/expandable elements',
        required: true
      },
      'aria-hidden': {
        purpose: 'Hides decorative elements from screen readers',
        usage: 'Use for purely decorative elements',
        required: false
      },
      'role': {
        purpose: 'Defines the element\'s purpose or function',
        usage: 'Use to provide semantic meaning when HTML elements are insufficient',
        required: false
      }
    };
    for (const attr of analysis.ariaAttributes) {
      const doc = ariaDocumentation[attr];
      if (doc) {
        ariaAttributes.push({
          attribute: attr,
          purpose: doc.purpose,
          usage: doc.usage,
          required: doc.required,
          example: `${attr}="value"`
        });
      }
    }
    return ariaAttributes;
  }
  /**
   * Identify keyboard support patterns
   */
  private identifyKeyboardSupport(analysis: ComponentAnalysis): KeyboardSupport[] {
    const keyboardSupport: KeyboardSupport[] = [];
    // Standard keyboard patterns based on component type
    if (analysis.htmlElements.has('button')) {
      keyboardSupport.push(
        {
          key: 'Enter',
          action: 'Activate button',
          context: 'When button is focused',
          required: true
        },
        {
          key: 'Space',
          action: 'Activate button',
          context: 'When button is focused',
          required: true
        }
      );
    }
    if (analysis.htmlElements.has('input')) {
      keyboardSupport.push({
        key: 'Tab',
        action: 'Move focus to next element',
        context: 'Form navigation',
        required: true
      });
    }
    if (analysis.ariaAttributes.has('aria-expanded')) {
      keyboardSupport.push(
        {
          key: 'Enter',
          action: 'Toggle expanded state',
          context: 'Collapsible elements',
          required: true
        },
        {
          key: 'Escape',
          action: 'Collapse if expanded',
          context: 'Collapsible elements',
          required: true
        }
      );
    }
    return keyboardSupport;
  }
  /**
   * Identify screen reader support features
   */
  private identifyScreenReaderSupport(analysis: ComponentAnalysis): ScreenReaderFeature[] {
    const features: ScreenReaderFeature[] = [];
    if (analysis.ariaAttributes.has('aria-label')) {
      features.push({
        feature: 'Custom Labels',
        announcement: 'Announces custom accessible name',
        context: 'When element receives focus',
        implementation: 'aria-label attribute'
      });
    }
    if (analysis.ariaAttributes.has('aria-live')) {
      features.push({
        feature: 'Live Regions',
        announcement: 'Announces dynamic content changes',
        context: 'When content updates',
        implementation: 'aria-live attribute'
      });
    }
    if (analysis.ariaAttributes.has('role')) {
      features.push({
        feature: 'Role Announcement',
        announcement: 'Announces element role and purpose',
        context: 'When element receives focus',
        implementation: 'role attribute'
      });
    }
    return features;
  }
  /**
   * Generate usage examples
   */
  private generateExamples(componentName: string, analysis: ComponentAnalysis): AccessibilityExample[] {
    const examples: AccessibilityExample[] = [];
    // Good example
    examples.push({
      title: 'Accessible Implementation',
      description: 'Proper accessibility implementation',
      code: this.generateGoodExample(componentName, analysis),
      doExample: true,
      explanation: 'This example includes proper ARIA attributes, keyboard support, and semantic HTML.'
    });
    // Bad example
    examples.push({
      title: 'Inaccessible Implementation',
      description: 'Common accessibility mistakes to avoid',
      code: this.generateBadExample(componentName),
      doExample: false,
      explanation: 'This example lacks proper accessibility features and should be avoided.'
    });
    return examples;
  }
  /**
   * Generate good example code
   */
  private generateGoodExample(componentName: string, analysis: ComponentAnalysis): string {
    const hasAriaLabel = analysis.ariaAttributes.has('aria-label');
    const hasKeyboardHandler = analysis.eventHandlers.has('onKeyDown');
    const hasButton = analysis.htmlElements.has('button');
    const labelAttribute = hasAriaLabel
      ? '  aria-label="Descriptive button label"'
      : '  aria-labelledby="component-label"';
    const keyboardSupportLine = hasKeyboardHandler
      ? '  onKeyDown={handleKeyDown}'
      : '  onKeyDown={handleKeyDown} // Added to ensure keyboard support';
    if (hasButton) {
      return `<${componentName}
${labelAttribute}
  onClick={handleClick}
${keyboardSupportLine}
  disabled={isDisabled}
>
</${componentName}>`;
    }
    return `<${componentName}
${labelAttribute}
  role="button"
  tabIndex={0}
  onClick={handleClick}
${keyboardSupportLine}
>
</${componentName}>`;
  }
  /**
   * Generate bad example code
   */
  private generateBadExample(componentName: string): string {
    return `<${componentName}
  onClick={handleClick}
>
  <div>Click me</div>
</${componentName}>`;
  }
  /**
   * Generate accessibility guidelines
   */
  private generateGuidelines(componentName: string, analysis: ComponentAnalysis): string[] {
    const guidelines: string[] = [];
    guidelines.push('Always provide meaningful labels for interactive elements');
    guidelines.push('Ensure keyboard accessibility for all interactive features');
    guidelines.push('Use semantic HTML elements when possible');
    guidelines.push('Provide clear focus indicators');
    guidelines.push('Test with screen readers and keyboard navigation');
    if (analysis.ariaAttributes.has('aria-expanded')) {
      guidelines.push('Update aria-expanded state when collapsible content changes');
    }
    if (analysis.htmlElements.has('button')) {
      guidelines.push('Use button elements for actions, links for navigation');
    }
    return guidelines;
  }
  /**
   * Identify common accessibility issues
   */
  private identifyCommonIssues(componentName: string, analysis: ComponentAnalysis): AccessibilityIssue[] {
    const issues: AccessibilityIssue[] = [];
    // Generic issues
    issues.push({
      issue: 'Missing focus indicators',
      description: 'Interactive elements lack visible focus indicators',
      solution: 'Add CSS focus styles with sufficient contrast',
      severity: 'high'
    });
    issues.push({
      issue: 'Insufficient color contrast',
      description: 'Text and background colors do not meet WCAG contrast requirements',
      solution: 'Use colors with at least 4.5:1 contrast ratio for normal text',
      severity: 'high'
    });
    if (analysis.htmlElements.has('button')) {
      issues.push({
        issue: 'Generic button text',
        description: 'Button text like "Click here" or "Read more" is not descriptive',
        solution: 'Use descriptive button text that explains the action',
        severity: 'medium'
      });
    }
    return issues;
  }
  /**
   * Generate testing instructions
   */
  private generateTestingInstructions(componentName: string, analysis: ComponentAnalysis): TestingInstruction[] {
    const instructions: TestingInstruction[] = [];
    // Keyboard testing
    instructions.push({
      method: 'keyboard',
      instruction: 'Navigate to the component using only the Tab key',
      expectedResult: 'Component should receive focus with visible focus indicator',
      tools: ['Keyboard only']
    });
    if (analysis.htmlElements.has('button')) {
      instructions.push({
        method: 'keyboard',
        instruction: 'Press Enter or Space when button is focused',
        expectedResult: 'Button action should be triggered',
        tools: ['Keyboard only']
      });
    }
    // Screen reader testing
    instructions.push({
      method: 'screen-reader',
      instruction: 'Navigate to component with screen reader',
      expectedResult: 'Screen reader should announce component role and accessible name',
      tools: ['NVDA', 'JAWS', 'VoiceOver']
    });
    // Automated testing
    instructions.push({
      method: 'automated',
      instruction: 'Run axe-core accessibility tests',
      expectedResult: 'No accessibility violations should be reported',
      tools: ['axe-core', 'jest-axe']
    });
    return instructions;
  }
  /**
   * Generate component documentation files
   */
  private async generateComponentDocs(): Promise<void> {
    await mkdir(this.config.outputDir, { recursive: true });
    for (const [name, info] of this.componentRegistry) {
      const markdown = this.generateComponentMarkdown(info);
      const filePath = join(this.config.outputDir, `${name}.md`);
      await writeFile(filePath, markdown);
    }
  }
  /**
   * Generate markdown for a component
   */
  private generateComponentMarkdown(info: ComponentAccessibilityInfo): string {
    return `# ${info.name} Accessibility Guide
## Description
${info.description}
## Accessibility Features
${info.accessibilityFeatures.map(feature => `
### ${feature.feature}
${feature.description}
**Implementation:** ${feature.implementation}
**WCAG Criteria:** ${feature.wcagCriteria.join(', ')}
`).join('')}
## ARIA Attributes
${info.ariaAttributes.map(attr => `
### ${attr.attribute}
**Purpose:** ${attr.purpose}
**Usage:** ${attr.usage}
**Required:** ${attr.required ? 'Yes' : 'No'}
**Example:** \`${attr.example}\`
`).join('')}
## Keyboard Support
| Key | Action | Context | Required |
|-----|--------|---------|----------|
${info.keyboardSupport.map(kb => `| ${kb.key} | ${kb.action} | ${kb.context} | ${kb.required ? 'Yes' : 'No'} |`).join('\n')}
## Screen Reader Support
${info.screenReaderSupport.map(sr => `
### ${sr.feature}
**Announcement:** ${sr.announcement}
**Context:** ${sr.context}
**Implementation:** ${sr.implementation}
`).join('')}
## Examples
${info.examples.map(example => `
### ${example.title} ${example.doExample ? '✅' : '❌'}
${example.description}
\`\`\`jsx
${example.code}
\`\`\`
${example.explanation}
`).join('')}
## Guidelines
${info.guidelines.map(guideline => `- ${guideline}`).join('\n')}
## Common Issues
${info.commonIssues.map(issue => `
### ${issue.issue} (${issue.severity.toUpperCase()})
**Description:** ${issue.description}
**Solution:** ${issue.solution}
`).join('')}
## Testing Instructions
${info.testingInstructions.map(test => `
### ${test.method.charAt(0).toUpperCase() + test.method.slice(1)} Testing
**Instruction:** ${test.instruction}
**Expected Result:** ${test.expectedResult}
${test.tools ? `**Tools:** ${test.tools.join(', ')}` : ''}
`).join('')}
---
*Generated automatically by Accessibility Documentation Generator*
`;
  }
  /**
   * Generate overview documentation
   */
  private async generateOverviewDoc(): Promise<void> {
    const components = Array.from(this.componentRegistry.values());
    const totalComponents = components.length;
    const componentsWithAria = components.filter(c => c.ariaAttributes.length > 0).length;
    const componentsWithKeyboard = components.filter(c => c.keyboardSupport.length > 0).length;
    const markdown = `# Accessibility Documentation Overview
## Summary
This documentation covers accessibility implementation for ${totalComponents} components in the application.
- **Components with ARIA support:** ${componentsWithAria}/${totalComponents}
- **Components with keyboard support:** ${componentsWithKeyboard}/${totalComponents}
- **WCAG Level:** ${this.config.wcagLevel}
## Components
${components.map(component => `
### [${component.name}](${component.name}.md)
${component.description}
**Accessibility Features:** ${component.accessibilityFeatures.length}
**ARIA Attributes:** ${component.ariaAttributes.length}
**Keyboard Support:** ${component.keyboardSupport.length}
`).join('')}
## Quick Links
- [Accessibility Guidelines](guidelines.md)
- [Testing Guide](testing.md)
- [Accessibility Checklist](checklist.md)
---
*Generated on ${new Date().toISOString()}*
`;
    await writeFile(join(this.config.outputDir, 'README.md'), markdown);
  }
  /**
   * Generate guidelines documentation
   */
  private async generateGuidelinesDoc(): Promise<void> {
    const markdown = `# Accessibility Guidelines
## General Principles
### 1. Perceivable
- Provide text alternatives for images
- Ensure sufficient color contrast
- Make content adaptable to different presentations
### 2. Operable
- Make all functionality keyboard accessible
- Give users enough time to read content
- Don't use content that causes seizures
### 3. Understandable
- Make text readable and understandable
- Make content appear and operate predictably
- Help users avoid and correct mistakes
### 4. Robust
- Maximize compatibility with assistive technologies
- Use valid, semantic HTML
- Ensure content works across different browsers and devices
## Component Development Guidelines
### Semantic HTML
- Use appropriate HTML elements for their intended purpose
- Prefer semantic elements over generic divs and spans
- Use headings to create a logical document structure
### ARIA Usage
- Use ARIA attributes to enhance semantics when HTML is insufficient
- Don't change native semantics unless absolutely necessary
- Ensure ARIA attributes are properly supported
### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Provide visible focus indicators
- Implement logical tab order
- Support standard keyboard conventions
### Color and Contrast
- Don't rely on color alone to convey information
- Ensure text has sufficient contrast (4.5:1 for normal text, 3:1 for large text)
- Test with color blindness simulators
### Forms
- Associate labels with form controls
- Provide clear error messages
- Group related form fields with fieldsets
- Indicate required fields clearly
### Dynamic Content
- Use ARIA live regions for important updates
- Manage focus when content changes
- Provide loading states and progress indicators
## Testing Requirements
All components must pass:
- Automated accessibility tests (axe-core)
- Keyboard navigation tests
- Screen reader compatibility tests
- Color contrast validation
## Resources
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/resources/)
`;
    await writeFile(join(this.config.outputDir, 'guidelines.md'), markdown);
  }
  /**
   * Generate testing documentation
   */
  private async generateTestingDoc(): Promise<void> {
    const markdown = `# Accessibility Testing Guide
## Testing Methods
### 1. Automated Testing
Automated tests catch common accessibility issues but cannot replace manual testing.
#### Tools
- **axe-core**: Industry-standard accessibility testing engine
- **jest-axe**: Jest integration for axe-core
- **Playwright**: End-to-end testing with accessibility checks
#### Running Tests
\`\`\`bash
# Run accessibility unit tests
npm run test:accessibility
# Run accessibility integration tests
npm run test:accessibility:integration
# Run full accessibility audit
npm run test:accessibility:audit
\`\`\`
### 2. Keyboard Testing
Test all functionality using only the keyboard.
#### Key Interactions
- **Tab**: Navigate forward through interactive elements
- **Shift+Tab**: Navigate backward through interactive elements
- **Enter**: Activate buttons and links
- **Space**: Activate buttons, check checkboxes
- **Arrow Keys**: Navigate within composite widgets
- **Escape**: Close dialogs and menus
#### Testing Checklist
- [ ] All interactive elements are reachable via keyboard
- [ ] Focus order is logical and intuitive
- [ ] Focus indicators are clearly visible
- [ ] No keyboard traps exist
- [ ] Custom keyboard shortcuts work as expected
### 3. Screen Reader Testing
Test with actual screen reader software.
#### Screen Readers
- **Windows**: NVDA (free), JAWS (commercial), Narrator (built-in)
- **macOS**: VoiceOver (built-in)
- **Linux**: Orca (free)
- **Mobile**: TalkBack (Android), VoiceOver (iOS)
#### Testing Process
1. Turn on screen reader
2. Navigate through the interface using screen reader commands
3. Verify all content is announced correctly
4. Check that interactive elements are properly identified
5. Ensure dynamic content updates are announced
### 4. Manual Testing
Visual and interaction testing that automated tools cannot perform.
#### Visual Testing
- Check color contrast with tools like WebAIM's Contrast Checker
- Test with browser zoom up to 200%
- Verify focus indicators are visible
- Test with high contrast mode enabled
#### Interaction Testing
- Test with different input methods (mouse, keyboard, touch)
- Verify error messages are clear and helpful
- Check that form validation works properly
- Test responsive behavior across different screen sizes
## Testing Scenarios
### Form Testing
1. Navigate through form using only keyboard
2. Verify all form controls have labels
3. Test form validation and error messaging
4. Check that required fields are clearly indicated
5. Verify form submission works with keyboard
### Navigation Testing
1. Test skip links functionality
2. Verify heading structure creates logical outline
3. Check that landmarks are properly implemented
4. Test breadcrumb navigation
5. Verify search functionality is accessible
### Dynamic Content Testing
1. Test that loading states are announced
2. Verify error messages are communicated to screen readers
3. Check that content updates trigger appropriate announcements
4. Test modal dialogs and focus management
5. Verify that infinite scroll or pagination is accessible
## Continuous Integration
### Automated Checks
- Run accessibility tests on every pull request
- Block deployments if critical accessibility issues are found
- Generate accessibility reports for each build
### Regression Testing
- Maintain baseline accessibility scores
- Alert when accessibility metrics decline
- Track improvements over time
## Reporting Issues
When reporting accessibility issues, include:
- Steps to reproduce
- Expected vs. actual behavior
- Assistive technology used (if applicable)
- Browser and operating system
- Screenshots or recordings when helpful
## Resources
### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Web Accessibility Evaluator](https://wave.webaim.org/)
- [Lighthouse Accessibility Audit](https://developers.google.com/web/tools/lighthouse)
- [Color Contrast Analyzers](https://www.tpgi.com/color-contrast-checker/)
### Screen Reader Resources
- [NVDA User Guide](https://www.nvaccess.org/documentation/)
- [VoiceOver User Guide](https://support.apple.com/guide/voiceover/)
- [Screen Reader Testing Guide](https://webaim.org/articles/screenreader_testing/)
`;
    await writeFile(join(this.config.outputDir, 'testing.md'), markdown);
  }
  /**
   * Generate accessibility checklist
   */
  private async generateChecklistDoc(): Promise<void> {
    const markdown = `# Accessibility Checklist
Use this checklist to ensure your components meet accessibility standards.
## Development Checklist
### Semantic HTML
- [ ] Use appropriate HTML elements (button, nav, main, etc.)
- [ ] Implement proper heading hierarchy (h1, h2, h3, etc.)
- [ ] Use lists for grouped content
- [ ] Use tables only for tabular data
- [ ] Include lang attribute on html element
### Keyboard Accessibility
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical and intuitive
- [ ] Focus indicators are clearly visible
- [ ] No keyboard traps exist
- [ ] Custom keyboard shortcuts are documented
- [ ] Skip links are provided for main content
### ARIA Implementation
- [ ] ARIA attributes are used correctly
- [ ] All form controls have accessible names
- [ ] Dynamic content uses appropriate live regions
- [ ] Complex widgets follow ARIA design patterns
- [ ] ARIA attributes are properly supported by target browsers
### Visual Design
- [ ] Color contrast meets WCAG AA standards (4.5:1 for normal text)
- [ ] Information is not conveyed by color alone
- [ ] Focus indicators have sufficient contrast
- [ ] Text is readable at 200% zoom
- [ ] Content reflows properly at different zoom levels
### Forms
- [ ] All form controls have labels
- [ ] Required fields are clearly marked
- [ ] Error messages are descriptive and helpful
- [ ] Form validation is accessible
- [ ] Fieldsets and legends are used for grouped controls
- [ ] Help text is associated with form controls
### Images and Media
- [ ] All images have appropriate alt text
- [ ] Decorative images are marked as such
- [ ] Complex images have detailed descriptions
- [ ] Videos have captions and transcripts
- [ ] Audio content has transcripts
### Dynamic Content
- [ ] Loading states are communicated to screen readers
- [ ] Error messages are announced
- [ ] Status updates use live regions
- [ ] Focus is managed when content changes
- [ ] Modal dialogs trap focus appropriately
## Testing Checklist
### Automated Testing
- [ ] axe-core tests pass without violations
- [ ] Lighthouse accessibility audit scores 100
- [ ] Custom accessibility tests are implemented
- [ ] Tests are integrated into CI/CD pipeline
### Keyboard Testing
- [ ] All functionality works with keyboard only
- [ ] Tab order is logical
- [ ] Focus indicators are visible
- [ ] Keyboard shortcuts work as expected
- [ ] No keyboard traps exist
### Screen Reader Testing
- [ ] Content is announced correctly
- [ ] Navigation is intuitive
- [ ] Form controls are properly labeled
- [ ] Dynamic content updates are announced
- [ ] Error messages are communicated
### Manual Testing
- [ ] Color contrast is sufficient
- [ ] Content works at 200% zoom
- [ ] High contrast mode is supported
- [ ] Reduced motion preferences are respected
- [ ] Touch targets are appropriately sized (44px minimum)
## Component-Specific Checklists
### Buttons
- [ ] Use button element for actions
- [ ] Provide descriptive button text or aria-label
- [ ] Include disabled state styling and behavior
- [ ] Support Enter and Space key activation
### Links
- [ ] Use anchor elements for navigation
- [ ] Provide descriptive link text
- [ ] Indicate external links
- [ ] Support Enter key activation
### Forms
- [ ] Associate labels with form controls
- [ ] Group related fields with fieldsets
- [ ] Provide clear error messages
- [ ] Indicate required fields
- [ ] Support keyboard navigation
### Modals/Dialogs
- [ ] Trap focus within modal
- [ ] Return focus to trigger element when closed
- [ ] Support Escape key to close
- [ ] Provide accessible name and description
- [ ] Prevent background interaction
### Tables
- [ ] Use table headers (th) appropriately
- [ ] Provide table caption or summary
- [ ] Use scope attribute for complex tables
- [ ] Ensure table is keyboard navigable
### Navigation
- [ ] Use nav element for navigation areas
- [ ] Provide skip links
- [ ] Indicate current page/section
- [ ] Support keyboard navigation
- [ ] Use appropriate ARIA attributes
## WCAG 2.1 Level AA Compliance
### Level A
- [ ] 1.1.1 Non-text Content
- [ ] 1.2.1 Audio-only and Video-only (Prerecorded)
- [ ] 1.2.2 Captions (Prerecorded)
- [ ] 1.2.3 Audio Description or Media Alternative (Prerecorded)
- [ ] 1.3.1 Info and Relationships
- [ ] 1.3.2 Meaningful Sequence
- [ ] 1.3.3 Sensory Characteristics
- [ ] 1.4.1 Use of Color
- [ ] 1.4.2 Audio Control
- [ ] 2.1.1 Keyboard
- [ ] 2.1.2 No Keyboard Trap
- [ ] 2.1.4 Character Key Shortcuts
- [ ] 2.2.1 Timing Adjustable
- [ ] 2.2.2 Pause, Stop, Hide
- [ ] 2.3.1 Three Flashes or Below Threshold
- [ ] 2.4.1 Bypass Blocks
- [ ] 2.4.2 Page Titled
- [ ] 2.4.3 Focus Order
- [ ] 2.4.4 Link Purpose (In Context)
- [ ] 2.5.1 Pointer Gestures
- [ ] 2.5.2 Pointer Cancellation
- [ ] 2.5.3 Label in Name
- [ ] 2.5.4 Motion Actuation
- [ ] 3.1.1 Language of Page
- [ ] 3.2.1 On Focus
- [ ] 3.2.2 On Input
- [ ] 3.3.1 Error Identification
- [ ] 3.3.2 Labels or Instructions
- [ ] 4.1.1 Parsing
- [ ] 4.1.2 Name, Role, Value
### Level AA
- [ ] 1.2.4 Captions (Live)
- [ ] 1.2.5 Audio Description (Prerecorded)
- [ ] 1.3.4 Orientation
- [ ] 1.3.5 Identify Input Purpose
- [ ] 1.4.3 Contrast (Minimum)
- [ ] 1.4.4 Resize text
- [ ] 1.4.5 Images of Text
- [ ] 1.4.10 Reflow
- [ ] 1.4.11 Non-text Contrast
- [ ] 1.4.12 Text Spacing
- [ ] 1.4.13 Content on Hover or Focus
- [ ] 2.4.5 Multiple Ways
- [ ] 2.4.6 Headings and Labels
- [ ] 2.4.7 Focus Visible
- [ ] 3.1.2 Language of Parts
- [ ] 3.2.3 Consistent Navigation
- [ ] 3.2.4 Consistent Identification
- [ ] 3.3.3 Error Suggestion
- [ ] 3.3.4 Error Prevention (Legal, Financial, Data)
- [ ] 4.1.3 Status Messages
---
*Use this checklist during development and before releasing features to ensure accessibility compliance.*
`;
    await writeFile(join(this.config.outputDir, 'checklist.md'), markdown);
  }
}
// Export utility functions
export const generateAccessibilityDocs = async (config?: Partial<DocumentationConfig>) => {
  const generator = new AccessibilityDocumentationGenerator(config);
  await generator.generateDocumentation();
};
export default AccessibilityDocumentationGenerator;
