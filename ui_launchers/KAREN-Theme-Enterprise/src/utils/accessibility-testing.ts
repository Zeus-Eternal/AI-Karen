"use client";
/**
 * Accessibility Testing Utilities (Vitest/JSDOM + axe-core)
 *
 * Comprehensive utilities for automated and manual a11y testing across
 * components and full pages. SSR-safe on import; DOM access only at call time.
 */

import axeCore, { type AxeResults, type RunOptions } from "axe-core";

type ExtendedRunOptions = RunOptions & {
  timeout?: number;
  include?: string[][];
  exclude?: string[][];
};

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================
export interface AccessibilityTestOptions {
  /** Custom axe-core rules configuration */
  rules?: RunOptions["rules"];
  /** Tags to include in testing */
  tags?: string[];
  /** CSS selectors to exclude from testing */
  exclude?: string[];
  /** CSS selectors to include explicitly */
  include?: string[];
  /** Custom timeout for tests (ms) */
  timeout?: number;
  /** Enable detailed reporting (kept for future pretty printers) */
  detailedReport?: boolean;
}

export interface AccessibilityViolation {
  /** Rule ID that was violated */
  id: string;
  /** Impact level of the violation */
  impact: "minor" | "moderate" | "serious" | "critical" | null;
  /** Description of the violation */
  description: string;
  /** Help text for fixing the violation */
  help: string;
  /** URL to more information */
  helpUrl: string;
  /** Elements that have the violation */
  nodes: Array<{
    target: string[];
    html: string;
    failureSummary: string;
  }>;
}

export interface AccessibilityReport {
  /** Test results from axe-core */
  results: AxeResults;
  /** Summary of violations */
  summary: {
    violations: number;
    passes: number;
    incomplete: number;
    inapplicable: number;
  };
  /** Detailed violation information */
  violations: AccessibilityViolation[];
  /** Performance metrics */
  performance: {
    duration: number; // ms
    rulesRun: number;
  };
}

export interface KeyboardTestResult {
  /** Whether all interactive elements are reachable */
  allReachable: boolean;
  /** Elements that are not keyboard accessible */
  unreachableElements: string[];
  /** Focus order issues */
  focusOrderIssues: string[];
  /** Missing focus indicators */
  missingFocusIndicators: string[];
}

export interface ScreenReaderTestResult {
  /** Whether all content has appropriate labels */
  hasLabels: boolean;
  /** Elements missing labels */
  missingLabels: string[];
  /** ARIA usage issues */
  ariaIssues: string[];
  /** Landmark structure issues */
  landmarkIssues: string[];
}

// ============================================================================
// AUTOMATED ACCESSIBILITY TESTING
// ============================================================================

/**
 * Run comprehensive accessibility tests on a DOM element or document
 */
export async function runAccessibilityTest(
  element: Element | Document = document,
  options: AccessibilityTestOptions = {}
): Promise<AccessibilityReport> {
  const startTime = (typeof performance !== "undefined" ? performance.now() : Date.now());

  // Configure axe-core options
  const axeOptions: ExtendedRunOptions = {
    rules: {
      // Sensible defaults; caller can override via options.rules
      "color-contrast": { enabled: true },
      "focus-order-semantics": { enabled: true },
      "keyboard-navigation": { enabled: true },
      "aria-valid-attr": { enabled: true },
      "aria-valid-attr-value": { enabled: true },
      "aria-roles": { enabled: true },
      "form-field-multiple-labels": { enabled: true },
      "heading-order": { enabled: true },
      "landmark-unique": { enabled: true },
      "link-name": { enabled: true },
      list: { enabled: true },
      listitem: { enabled: true },
      "page-has-heading-one": { enabled: true },
      region: { enabled: true },
      "skip-link": { enabled: true },
      tabindex: { enabled: true },
      ...(options.rules || {}),
    },
    timeout: options.timeout ?? 10_000,
    runOnly: {
      type: "tag",
      values: options.tags ?? ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"],
    },
  };

  if (options.include?.length) axeOptions.include = options.include.map((selector) => [selector]);
  if (options.exclude?.length) axeOptions.exclude = options.exclude.map((selector) => [selector]);

  try {
    const node = element as unknown as Node;
    const results = (await axeCore.run(node, axeOptions)) as AxeResults;
    const endTime = (typeof performance !== "undefined" ? performance.now() : Date.now());

    const violations: AccessibilityViolation[] = results.violations.map((v) => ({
      id: v.id,
      impact: (v.impact ?? null) as AccessibilityViolation["impact"],
      description: v.description,
      help: v.help,
      helpUrl: v.helpUrl,
      nodes: v.nodes.map((n) => ({
        target: n.target as string[],
        html: n.html ?? "",
        failureSummary: (n as unknown as Record<string, unknown>).failureSummary as string || "",
      })),
    }));

    return {
      results,
      summary: {
        violations: results.violations.length,
        passes: results.passes.length,
        incomplete: results.incomplete.length,
        inapplicable: results.inapplicable.length,
      },
      violations,
      performance: {
        duration: endTime - startTime,
        rulesRun: Object.keys(axeOptions.rules || {}).length,
      },
    };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    throw new Error(`Accessibility test failed: ${msg}`);
  }
}

// ============================================================================
// KEYBOARD ACCESSIBILITY (HEURISTICS)
// ============================================================================

/**
 * Test keyboard accessibility of interactive elements (heuristic)
 */
export function testKeyboardAccessibility(container: Element = document.body): KeyboardTestResult {
  const interactiveSelectors = [
    "button",
    "a[href]",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
    "[role='button']",
    "[role='link']",
    "[role='menuitem']",
    "[role='tab']",
  ];

  const interactiveElements = container.querySelectorAll(interactiveSelectors.join(", "));
  const unreachableElements: string[] = [];
  const focusOrderIssues: string[] = [];
  const missingFocusIndicators: string[] = [];

  interactiveElements.forEach((el, index) => {
    const node = el as HTMLElement;
    const isDisabled = node.hasAttribute("disabled") || node.getAttribute("aria-disabled") === "true";
    const tabIndex = node.tabIndex;

    // Focusability heuristic
    if (!isDisabled && tabIndex < 0 && !node.getAttribute("href")) {
      unreachableElements.push(`${node.tagName.toLowerCase()}[${index}]`);
    }

    // Positive tabindex often indicates custom/incorrect focus order
    if (tabIndex > 0) {
      focusOrderIssues.push(`${node.tagName.toLowerCase()}[${index}] has positive tabindex (${tabIndex})`);
    }

    // Focus indicator heuristic (computed styles on :focus-visible where supported)
    let hasIndicator = false;
    try {
      node.focus();
      const style = window.getComputedStyle(node);
      const outline = style.outlineStyle && style.outlineStyle !== "none";
      const boxShadow = style.boxShadow && style.boxShadow !== "none";
      const forcedClass = node.classList.contains("focus-visible") || node.classList.contains("focus");
      hasIndicator = !!(outline || boxShadow || forcedClass);
    } catch {
      // ignore in non-interactive contexts
    }
    if (!hasIndicator) missingFocusIndicators.push(`${node.tagName.toLowerCase()}[${index}]`);
  });

  return {
    allReachable: unreachableElements.length === 0,
    unreachableElements,
    focusOrderIssues,
    missingFocusIndicators,
  };
}

// ============================================================================
// SCREEN READER ACCESSIBILITY (HEURISTICS)
// ============================================================================

/**
 * Test screen reader accessibility heuristics (labels, ARIA refs, landmarks)
 */
export function testScreenReaderAccessibility(container: Element = document.body): ScreenReaderTestResult {
  const missingLabels: string[] = [];
  const ariaIssues: string[] = [];
  const landmarkIssues: string[] = [];

  // Form controls should have an accessible name
  const formControls = container.querySelectorAll("input, select, textarea");
  formControls.forEach((control, index) => {
    const el = control as HTMLElement & { id?: string };
    const id = el.id;
    const ariaLabel = el.getAttribute("aria-label");
    const ariaLabelledBy = el.getAttribute("aria-labelledby");
    const hasLabel = id ? container.querySelector(`label[for='${id}']`) : null;

    if (!ariaLabel && !ariaLabelledBy && !hasLabel) {
      missingLabels.push(`${control.tagName.toLowerCase()}[${index}]`);
    }
  });

  // Images should have alt (unless presentational)
  const images = container.querySelectorAll("img");
  images.forEach((img, index) => {
    const altText = img.getAttribute("alt");
    const ariaLabel = img.getAttribute("aria-label");
    const role = img.getAttribute("role");
    if (!altText && !ariaLabel && role !== "presentation" && role !== "none") {
      missingLabels.push(`img[${index}]`);
    }
  });

  // ARIA references should exist
  const withAriaRefs = container.querySelectorAll("[aria-describedby], [aria-labelledby], [aria-controls]");
  withAriaRefs.forEach((element, index) => {
    const attrs = [
      element.getAttribute("aria-describedby"),
      element.getAttribute("aria-labelledby"),
      element.getAttribute("aria-controls"),
    ]
      .filter(Boolean)
      .join(" ")
      .split(" ")
      .filter(Boolean);

    attrs.forEach((id) => {
      if (id && !container.querySelector(`#${id}`)) {
        ariaIssues.push(`${element.tagName.toLowerCase()}[${index}] references non-existent ID: ${id}`);
      }
    });
  });

  // Landmark sanity check
  const mains = container.querySelectorAll("main, [role='main']");
  if (mains.length === 0) landmarkIssues.push("No main landmark found");
  else if (mains.length > 1) landmarkIssues.push("Multiple main landmarks found");

  return {
    hasLabels: missingLabels.length === 0,
    missingLabels,
    ariaIssues,
    landmarkIssues,
  };
}

// ============================================================================
// ACCESSIBILITY VALIDATION HELPERS
// ============================================================================

/**
 * Validate color contrast ratio using WCAG relative luminance
 */
export function validateColorContrast(
  foreground: string,
  background: string,
  fontSize: number = 16,
  fontWeight: number = 400
): { ratio: number; passes: { aa: boolean; aaa: boolean } } {
  const fgRgb = toRgb(foreground);
  const bgRgb = toRgb(background);
  if (!fgRgb || !bgRgb) throw new Error("Invalid color format; expected hex (#rrggbb or #rgb)");

  const fgL = relativeLuminance(fgRgb);
  const bgL = relativeLuminance(bgRgb);
  const ratio = (Math.max(fgL, bgL) + 0.05) / (Math.min(fgL, bgL) + 0.05);

  const isLarge = fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700);
  const aaReq = isLarge ? 3 : 4.5;
  const aaaReq = isLarge ? 4.5 : 7;

  const rounded = Math.round(ratio * 100) / 100;
  return {
    ratio: rounded,
    passes: { aa: ratio >= aaReq, aaa: ratio >= aaaReq },
  };
}

/**
 * Validate ARIA attributes on a single element
 */
export function validateAriaAttributes(element: Element): string[] {
  const issues: string[] = [];
  const ariaAttributes = Array.from(element.attributes).filter((a) => a.name.startsWith("aria-"));

  ariaAttributes.forEach((attr) => {
    const name = attr.name;
    const value = attr.value;

    if (!value.trim()) {
      issues.push(`${name} has empty value`);
      return;
    }

    switch (name) {
      case "aria-expanded":
      case "aria-checked":
      case "aria-selected":
      case "aria-pressed":
      case "aria-hidden": {
        if (!["true", "false"].includes(value)) issues.push(`${name} must be "true" or "false"`);
        break;
      }
      case "aria-level":
      case "aria-setsize":
      case "aria-posinset": {
        if (!/^\d+$/.test(value) || parseInt(value, 10) < 1) issues.push(`${name} must be a positive integer`);
        break;
      }
      case "aria-describedby":
      case "aria-labelledby":
      case "aria-controls": {
        const ids = value.split(" ").filter(Boolean);
        ids.forEach((id) => {
          if (id && !document.getElementById(id)) issues.push(`${name} references non-existent ID: ${id}`);
        });
        break;
      }
      default:
        // other aria- attributes not exhaustively validated here
        break;
    }
  });

  return issues;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function toRgb(hex: string): { r: number; g: number; b: number } | null {
  let h = hex.trim();
  if (!h.startsWith("#")) return null;
  h = h.slice(1);
  if (h.length === 3) {
    h = h.split("").map((c) => c + c).join("");
  }
  const m = /^([a-fA-F\d]{2})([a-fA-F\d]{2})([a-fA-F\d]{2})$/.exec(h);
  if (!m) return null;
  return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
}

function relativeLuminance({ r, g, b }: { r: number; g: number; b: number }): number {
  const toLin = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  const rs = toLin(r);
  const gs = toLin(g);
  const bs = toLin(b);
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Generate a terse, human-readable accessibility report summary
 */
export function generateAccessibilityReportSummary(report: AccessibilityReport): string {
  const { summary, violations, performance } = report;
  let txt = "Accessibility Test Report\n";
  txt += "========================\n\n";
  txt += "Summary:\n";
  txt += `- Violations: ${summary.violations}\n`;
  txt += `- Passes: ${summary.passes}\n`;
  txt += `- Incomplete: ${summary.incomplete}\n`;
  txt += `- Not Applicable: ${summary.inapplicable}\n`;
  txt += `- Test Duration: ${Math.round(performance.duration)}ms\n\n`;

  if (violations.length) {
    txt += "Violations:\n";
    violations.forEach((v, i) => {
      txt += `${i + 1}. ${v.description} (${v.impact ?? "unknown"})\n`;
      txt += `   Help: ${v.help}\n`;
      txt += `   More info: ${v.helpUrl}\n`;
      txt += `   Affected elements: ${v.nodes.length}\n\n`;
    });
  }

  return txt;
}

// ============================================================================
// PRESET CONFIGS
// ============================================================================
export const accessibilityTestConfigs = {
  basic: {
    tags: ["wcag2a", "wcag2aa"],
    rules: {
      "color-contrast": { enabled: true },
      "keyboard-navigation": { enabled: true },
      "aria-valid-attr": { enabled: true },
    },
  },
  comprehensive: {
    tags: ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"],
    rules: {
      "color-contrast": { enabled: true },
      "focus-order-semantics": { enabled: true },
      "keyboard-navigation": { enabled: true },
      "aria-valid-attr": { enabled: true },
      "aria-valid-attr-value": { enabled: true },
      "form-field-multiple-labels": { enabled: true },
      "heading-order": { enabled: true },
      "landmark-unique": { enabled: true },
      "page-has-heading-one": { enabled: true },
    },
  },
  forms: {
    tags: ["wcag2a", "wcag2aa"],
    rules: {
      label: { enabled: true },
      "form-field-multiple-labels": { enabled: true },
      "aria-valid-attr": { enabled: true },
      "aria-required-attr": { enabled: true },
    },
  },
  navigation: {
    tags: ["wcag2a", "wcag2aa"],
    rules: {
      "link-name": { enabled: true },
      "skip-link": { enabled: true },
      "landmark-unique": { enabled: true },
      region: { enabled: true },
    },
  },
} as const;

export type AccessibilityPresetKey = keyof typeof accessibilityTestConfigs;

/**
 * Convenience wrapper to run using a named preset
 */
export async function runWithPreset(
  container: Element | Document,
  preset: AccessibilityPresetKey
): Promise<AccessibilityReport> {
  const cfg = accessibilityTestConfigs[preset];
  return runAccessibilityTest(container, {
    tags: [...cfg.tags],
    rules: cfg.rules,
  });
}
