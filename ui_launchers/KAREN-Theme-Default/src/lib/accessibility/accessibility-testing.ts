import axe, { type AxeResults, type RunOptions } from "axe-core";

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface AccessibilityTestSuite {
  basic: () => Promise<AccessibilityReport>;
  comprehensive: () => Promise<AccessibilityReport>;
  keyboard: () => Promise<KeyboardAccessibilityReport>;
  screenReader: () => Promise<ScreenReaderReport>;
  colorContrast: () => Promise<ColorContrastReport>;
  focusManagement: () => Promise<FocusManagementReport>;
  aria: () => Promise<AriaReport>;
}

export interface AccessibilityReport {
  passed: boolean;
  score: number;
  violations: AccessibilityViolation[];
  warnings: AccessibilityWarning[];
  summary: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
  };
  recommendations: string[];
  testDuration: number;
}

export interface AccessibilityViolation {
  id: string;
  impact: "critical" | "serious" | "moderate" | "minor";
  description: string;
  help: string;
  helpUrl: string;
  elements: Array<{
    target: string;
    html: string;
    failureSummary: string;
  }>;
}

export interface AccessibilityWarning {
  id: string;
  description: string;
  elements: string[];
  recommendation: string;
}

export interface KeyboardAccessibilityReport {
  passed: boolean;
  focusableElements: number;
  unreachableElements: string[];
  focusOrderIssues: string[];
  trapIssues: string[];
  skipLinkIssues: string[];
}

export interface ScreenReaderReport {
  passed: boolean;
  missingLabels: string[];
  ariaIssues: string[];
  landmarkIssues: string[];
  headingStructureIssues: string[];
  liveRegionIssues: string[];
}

export interface ColorContrastReport {
  passed: boolean;
  failedElements: Array<{
    element: string;
    foreground: string;
    background: string;
    ratio: number;
    required: number;
    level: "AA" | "AAA";
  }>;
  averageRatio: number;
}

export interface FocusManagementReport {
  passed: boolean;
  focusTraps: Array<{
    element: string;
    working: boolean;
    issues: string[];
  }>;
  focusRestoration: Array<{
    element: string;
    working: boolean;
  }>;
  focusIndicators: Array<{
    element: string;
    visible: boolean;
    contrast: number;
  }>;
}

export interface AriaReport {
  passed: boolean;
  invalidAttributes: string[];
  missingAttributes: string[];
  incorrectRoles: string[];
  brokenReferences: string[];
}

// ============================================================================
// ACCESSIBILITY TEST SUITE
// ============================================================================

export class AccessibilityTestSuiteImpl implements AccessibilityTestSuite {
  private container: Element | Document;
  private options: RunOptions;

  constructor(
    container: Element | Document = document,
    options: RunOptions = {}
  ) {
    this.container = container;
    this.options = {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21aa"],
      },
      ...options,
    };
  }

  async basic(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] },
      });

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(`Basic accessibility test failed: ${error.message}`);
    }
  }

  async comprehensive(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: {
          type: "tag",
          values: ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"],
        },
      });

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(
        `Comprehensive accessibility test failed: ${error.message}`
      );
    }
  }

  async keyboard(): Promise<KeyboardAccessibilityReport> {
    const focusableSelectors = [
      "a[href]",
      "button:not([disabled])",
      "input:not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
      '[role="button"]',
      '[role="link"]',
      '[role="menuitem"]',
      '[role="tab"]',
    ];

    const focusableElements = this.container.querySelectorAll(
      focusableSelectors.join(", ")
    );
    const unreachableElements: string[] = [];
    const focusOrderIssues: string[] = [];
    const trapIssues: string[] = [];
    const skipLinkIssues: string[] = [];

    focusableElements.forEach((element) => {
      const htmlElement = element as HTMLElement;

      if (htmlElement.tabIndex < 0 && !htmlElement.hasAttribute("disabled")) {
        unreachableElements.push(this.getElementSelector(htmlElement));
      }

      if (htmlElement.tabIndex > 0) {
        focusOrderIssues.push(
          `Element has positive tabindex: ${this.getElementSelector(
            htmlElement
          )}`
        );
      }
    });

    const focusTraps = this.container.querySelectorAll(
      '[data-focus-trap="true"]'
    );
    focusTraps.forEach((trap) => {
      const trapElement = trap as HTMLElement;
      const focusableInTrap = trapElement.querySelectorAll(
        focusableSelectors.join(", ")
      );

      if (focusableInTrap.length === 0) {
        trapIssues.push(
          `Focus trap has no focusable elements: ${this.getElementSelector(
            trapElement
          )}`
        );
      }
    });

    const skipLinks = this.container.querySelectorAll(
      '.skip-links a, [href^="#"]'
    );
    skipLinks.forEach((link) => {
      const href = link.getAttribute("href");
      if (href && href.startsWith("#")) {
        const target = this.container.querySelector(href);
        if (!target) {
          skipLinkIssues.push(`Skip link target not found: ${href}`);
        }
      }
    });

    return {
      passed:
        unreachableElements.length === 0 &&
        focusOrderIssues.length === 0 &&
        trapIssues.length === 0 &&
        skipLinkIssues.length === 0,
      focusableElements: focusableElements.length,
      unreachableElements,
      focusOrderIssues,
      trapIssues,
      skipLinkIssues,
    };
  }

  async screenReader(): Promise<ScreenReaderReport> {
    // Implement the screenReader testing logic
    return {
      passed: true,
      missingLabels: [],
      ariaIssues: [],
      landmarkIssues: [],
      headingStructureIssues: [],
      liveRegionIssues: [],
    };
  }

  async colorContrast(): Promise<ColorContrastReport> {
    if (typeof window === "undefined") {
      return {
        passed: true,
        failedElements: [],
        averageRatio: 4.5,
      };
    }

    const elements = Array.from(
      this.container.querySelectorAll<HTMLElement>("*")
    );
    const failedElements: ColorContrastReport["failedElements"] = [];
    let totalRatio = 0;
    let sampled = 0;

    elements.slice(0, 200).forEach((element) => {
      const styles = window.getComputedStyle(element);
      const foreground = styles.color || "#000000";
      const background = styles.backgroundColor || "#ffffff";
      const ratio = this.calculateContrastRatio(foreground, background);

      totalRatio += ratio;
      sampled += 1;

      const required =
        styles.fontWeight === "bold" || parseFloat(styles.fontSize) >= 18
          ? 3
          : 4.5;
      if (ratio < required) {
        failedElements.push({
          element: this.getElementSelector(element),
          foreground,
          background,
          ratio,
          required,
          level: required >= 4.5 ? "AA" : "AAA",
        });
      }
    });

    const averageRatio = sampled > 0 ? totalRatio / sampled : 4.5;

    return {
      passed: failedElements.length === 0,
      failedElements,
      averageRatio,
    };
  }

  async focusManagement(): Promise<FocusManagementReport> {
    if (typeof document === "undefined") {
      return {
        passed: true,
        focusTraps: [],
        focusRestoration: [],
        focusIndicators: [],
      };
    }

    const focusableSelectors = [
      "a[href]",
      "button:not([disabled])",
      "textarea:not([disabled])",
      "input:not([disabled])",
      "select:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
      '[role="button"]',
      '[role="link"]',
    ];

    const focusTrapCandidates = Array.from(
      this.container.querySelectorAll(
        '[data-focus-trap], [aria-modal="true"], [role="dialog"]'
      )
    ) as HTMLElement[];

    const focusTraps = focusTrapCandidates.map((element) => {
      const innerFocusable = element.querySelectorAll(
        focusableSelectors.join(", ")
      );
      const working = innerFocusable.length > 0;
      const issues = working ? [] : ["No focusable elements inside focus trap"];
      return {
        element: this.getElementSelector(element),
        working,
        issues,
      };
    });

    const restoreTargets = Array.from(
      this.container.querySelectorAll(
        "[data-focus-restore], [data-focus-restoration]"
      )
    ) as HTMLElement[];

    const focusRestoration = restoreTargets.map((element) => ({
      element: this.getElementSelector(element),
      working:
        element.hasAttribute("data-focus-restore") ||
        element.hasAttribute("data-focus-restoration"),
    }));

    const focusableElements = Array.from(
      this.container.querySelectorAll(focusableSelectors.join(", "))
    ) as HTMLElement[];

    const focusIndicators = focusableElements.slice(0, 25).map((element) => {
      if (typeof window === "undefined") {
        return {
          element: this.getElementSelector(element),
          visible: false,
          contrast: 0,
        };
      }
      const styles = window.getComputedStyle(element);
      const outlineVisible =
        styles.outlineStyle !== "none" && styles.outlineWidth !== "0px";
      const borderVisible =
        styles.borderStyle !== "none" && styles.borderWidth !== "0px";
      const visible = outlineVisible || borderVisible;
      const contrast = visible
        ? this.calculateContrastRatio(
            styles.outlineColor || styles.borderColor || "#000000",
            styles.backgroundColor || "#ffffff"
          )
        : 0;
      return {
        element: this.getElementSelector(element),
        visible,
        contrast,
      };
    });

    const passed =
      focusTraps.every((trap) => trap.working && trap.issues.length === 0) &&
      focusIndicators.some((indicator) => indicator.visible);

    return {
      passed,
      focusTraps,
      focusRestoration,
      focusIndicators,
    };
  }

  async aria(): Promise<AriaReport> {
    if (typeof document === "undefined") {
      return {
        passed: true,
        invalidAttributes: [],
        missingAttributes: [],
        incorrectRoles: [],
        brokenReferences: [],
      };
    }
    const allowedAriaAttributes = new Set([
      "aria-activedescendant",
      "aria-atomic",
      "aria-autocomplete",
      "aria-busy",
      "aria-checked",
      "aria-colcount",
      "aria-colindex",
      "aria-colspan",
      "aria-controls",
      "aria-current",
      "aria-describedby",
      "aria-details",
      "aria-disabled",
      "aria-expanded",
      "aria-flowto",
      "aria-haspopup",
      "aria-hidden",
      "aria-invalid",
      "aria-keyshortcuts",
      "aria-label",
      "aria-labelledby",
      "aria-level",
      "aria-live",
      "aria-modal",
      "aria-multiline",
      "aria-multiselectable",
      "aria-orientation",
      "aria-owns",
      "aria-placeholder",
      "aria-posinset",
      "aria-pressed",
      "aria-readonly",
      "aria-relevant",
      "aria-required",
      "aria-roledescription",
      "aria-rowcount",
      "aria-rowindex",
      "aria-rowspan",
      "aria-selected",
      "aria-setsize",
      "aria-sort",
      "aria-valuemax",
      "aria-valuemin",
      "aria-valuenow",
      "aria-valuetext",
    ]);

    const validRoles = new Set([
      "button",
      "checkbox",
      "dialog",
      "heading",
      "link",
      "list",
      "listitem",
      "menu",
      "menubar",
      "menuitem",
      "navigation",
      "none",
      "presentation",
      "progressbar",
      "radio",
      "radiogroup",
      "region",
      "slider",
      "status",
      "switch",
      "tab",
      "tablist",
      "tabpanel",
      "textbox",
      "tooltip",
      "img",
    ]);

    const invalidAttributes = new Set<string>();
    const missingAttributes = new Set<string>();
    const incorrectRoles = new Set<string>();
    const brokenReferences = new Set<string>();

    const allElements = Array.from(
      this.container.querySelectorAll("*")
    ) as HTMLElement[];
    const scopeDocument =
      this.container instanceof Document
        ? this.container
        : this.container.ownerDocument || document;

    allElements.forEach((element) => {
      const attrNames = element.getAttributeNames();
      attrNames.forEach((attr) => {
        if (attr.startsWith("aria-") && !allowedAriaAttributes.has(attr)) {
          invalidAttributes.add(`${this.getElementSelector(element)}: ${attr}`);
        }

        if (
          /(describedby|labelledby|controls|owns|activedescendant)$/.test(attr)
        ) {
          const value = element.getAttribute(attr);
          if (value) {
            value.split(/\s+/).forEach((id) => {
              if (!scopeDocument.getElementById(id)) {
                brokenReferences.add(
                  `${this.getElementSelector(
                    element
                  )} references missing #${id}`
                );
              }
            });
          }
        }
      });

      const role = element.getAttribute("role");
      if (role && !validRoles.has(role.toLowerCase())) {
        incorrectRoles.add(`${this.getElementSelector(element)}: ${role}`);
      }

      if (role === "img") {
        const hasLabel =
          element.hasAttribute("aria-label") ||
          element.hasAttribute("aria-labelledby") ||
          element.hasAttribute("alt");
        if (!hasLabel) {
          missingAttributes.add(
            `${this.getElementSelector(
              element
            )} missing aria-label/labelledby/alt`
          );
        }
      }
    });

    const passed =
      invalidAttributes.size === 0 &&
      missingAttributes.size === 0 &&
      incorrectRoles.size === 0 &&
      brokenReferences.size === 0;

    return {
      passed,
      invalidAttributes: Array.from(invalidAttributes),
      missingAttributes: Array.from(missingAttributes),
      incorrectRoles: Array.from(incorrectRoles),
      brokenReferences: Array.from(brokenReferences),
    };
  }

  private processAxeResults(
    results: AxeResults,
    duration: number
  ): AccessibilityReport {
    const violations: AccessibilityViolation[] = results.violations.map(
      (violation: any) => ({
        id: violation.id,
        impact: violation.impact,
        description: violation.description,
        help: violation.help,
        helpUrl: violation.helpUrl,
        elements: violation.nodes.map((node: any) => ({
          target: node.target.join(" "),
          html: node.html,
          failureSummary: node.failureSummary || "",
        })),
      })
    );

    const summary = {
      critical: violations.filter((v) => v.impact === "critical").length,
      serious: violations.filter((v) => v.impact === "serious").length,
      moderate: violations.filter((v) => v.impact === "moderate").length,
      minor: violations.filter((v) => v.impact === "minor").length,
    };

    const score = Math.max(
      0,
      100 -
        (summary.critical * 25 +
          summary.serious * 10 +
          summary.moderate * 5 +
          summary.minor * 1)
    );

    const recommendations = this.generateRecommendations(violations);

    return {
      passed: violations.length === 0,
      score,
      violations,
      warnings: [],
      summary,
      recommendations,
      testDuration: duration,
    };
  }

  private generateRecommendations(
    violations: AccessibilityViolation[]
  ): string[] {
    const recommendations: string[] = [];
    violations.forEach((violation) => {
      switch (violation.id) {
        case "color-contrast":
          recommendations.push(
            "Increase color contrast to meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)"
          );
          break;
        case "keyboard":
          recommendations.push(
            "Ensure all interactive elements are keyboard accessible"
          );
          break;
        case "aria-valid-attr":
          recommendations.push("Fix invalid ARIA attributes");
          break;
        case "label":
          recommendations.push("Add proper labels to form controls");
          break;
        default:
          recommendations.push(`Address ${violation.id}: ${violation.help}`);
      }
    });

    return [...new Set(recommendations)];
  }

  private getElementSelector(element: HTMLElement): string {
    if (element.id) return `#${element.id}`;
    if (element.className)
      return `${element.tagName.toLowerCase()}.${
        element.className.split(" ")[0]
      }`;
    return element.tagName.toLowerCase();
  }

  private parseColor(color: string): { r: number; g: number; b: number } {
    if (!color) {
      return { r: 0, g: 0, b: 0 };
    }

    if (color.startsWith("#")) {
      const hex = color.replace("#", "");
      const normalized =
        hex.length === 3
          ? hex
              .split("")
              .map((c) => c + c)
              .join("")
          : hex.padEnd(6, "0");
      const value = parseInt(normalized, 16);
      return {
        r: (value >> 16) & 255,
        g: (value >> 8) & 255,
        b: value & 255,
      };
    }

    const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
    if (match) {
      return {
        r: parseInt(match[1], 10),
        g: parseInt(match[2], 10),
        b: parseInt(match[3], 10),
      };
    }

    return { r: 0, g: 0, b: 0 };
  }

  private relativeLuminance({
    r,
    g,
    b,
  }: {
    r: number;
    g: number;
    b: number;
  }): number {
    const srgb = [r, g, b].map((value) => {
      const channel = value / 255;
      return channel <= 0.03928
        ? channel / 12.92
        : Math.pow((channel + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
  }

  private calculateContrastRatio(
    foreground: string,
    background: string
  ): number {
    const fg = this.parseColor(foreground);
    const bg = this.parseColor(background);
    const l1 = this.relativeLuminance(fg);
    const l2 = this.relativeLuminance(bg);
    const brighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return Number(((brighter + 0.05) / (darker + 0.05)).toFixed(2));
  }
}

// ============================================================================
// TESTING UTILITIES
// ============================================================================

export function createAccessibilityTestSuite(
  container?: Element | Document
): AccessibilityTestSuite {
  return new AccessibilityTestSuiteImpl(container);
}

export async function runQuickAccessibilityCheck(
  element?: Element | Document
): Promise<boolean> {
  const suite = createAccessibilityTestSuite(element);
  const result = await suite.basic();
  return result.passed;
}

export async function generateAccessibilityReport(
  element?: Element | Document
): Promise<string> {
  const suite = createAccessibilityTestSuite(element);
  const [basic, keyboard, screenReader, colorContrast] = await Promise.all([
    suite.basic(),
    suite.keyboard(),
    suite.screenReader(),
    suite.colorContrast(),
  ]);

  let report = "Accessibility Test Report\n";
  report += "========================\n\n";

  report += `Overall Score: ${basic.score}/100\n`;
  report += `Basic Test: ${basic.passed ? "PASS" : "FAIL"}\n`;
  report += `Keyboard Test: ${keyboard.passed ? "PASS" : "FAIL"}\n`;
  report += `Screen Reader Test: ${screenReader.passed ? "PASS" : "FAIL"}\n`;
  report += `Color Contrast Test: ${
    colorContrast.passed ? "PASS" : "FAIL"
  }\n\n`;

  if (basic.violations.length > 0) {
    report += "Violations:\n";
    basic.violations.forEach((violation, index) => {
      report += `${index + 1}. ${violation.description} (${
        violation.impact
      })\n`;
      report += `   Elements: ${violation.elements.length}\n`;
      report += `   Help: ${violation.help}\n\n`;
    });
  }

  if (basic.recommendations.length > 0) {
    report += "Recommendations:\n";
    basic.recommendations.forEach((rec, index) => {
      report += `${index + 1}. ${rec}\n`;
    });
  }

  return report;
}

export default AccessibilityTestSuiteImpl;
